"""Main application window - orchestrates all UI components and services."""

from __future__ import annotations

import logging
import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from src.config import MONITOR_INTERVAL
from src.models.monitor import MemoryStats
from src.models.restart_config import RestartConfig
from src.models.server_config import Parameter
from src.models.ssh_config import SSHConfig, SSHState
from src.services.config_service import ConfigService
from src.services.monitor_service import MonitorService
from src.services.param_service import ParamService
from src.services.process_manager import ProcessManager
from src.services.ssh_service import SSHService
from src.ui.log_panel import LogPanel
from src.ui.param_panel import ParamPanel
from src.ui.ssh_panel import SSHPanel
from src.ui.toolbar import Toolbar

if TYPE_CHECKING:
    from src.models.server_config import LaunchConfig

logger = logging.getLogger(__name__)


class App:
    def __init__(self) -> None:
        self._init_logging()
        
        self.root = tk.Tk()
        self.root.title("llamacpp-panel")
        self.root.geometry("1000x700")

        self._create_services()
        self._create_ui()
        self._wire_callbacks()
        self._load_saved_config()
        self._setup_bindings()

        self._current_ssh_process: object | None = None
        self._current_process: object | None = None
        self._restart_config = RestartConfig()
        self._ssh_auto_start_check_count: int = 0

    def _init_logging(self) -> None:
        from datetime import datetime
        
        log_dir = "log"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.txt")
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
        root_logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
        root_logger.addHandler(console_handler)
        
        logger.info("[INIT_LOGGING] log_file=%s, console_enabled=True", log_file)

    def _create_services(self) -> None:
        logger.info("[CREATE_SERVICES] starting")
        self.config_service = ConfigService()
        self.param_service = ParamService()
        self.monitor_service = MonitorService()
        self.ssh_service = SSHService()
        self.process_manager = ProcessManager(
            callback=lambda msg, level: self._safe_log(msg, level),
        )
        logger.info("[CREATE_SERVICES] completed")

    def _create_ui(self) -> None:
        logger.info("[CREATE_UI] starting")
        
        self.toolbar = Toolbar(
            self.root,
            on_start=self._on_start,
            on_stop=self._on_stop,
            on_restart=self._on_restart,
            on_auto_restart=self._on_auto_restart_toggled,
            on_auto_restart_config=self._on_auto_restart_config_changed,
        )
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.log_panel = LogPanel(self.root)
        self.log_panel.pack(side=tk.BOTTOM, fill=tk.X)

        notebook = ttk.Notebook(self.root)
        notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.param_panel = ParamPanel(
            notebook,
            param_service=self.param_service,
            config_service=self.config_service,
        )
        self.param_panel._on_save_template = self._on_save_template
        self.param_panel._on_save_as_template = self._on_save_as_template
        self.param_panel._on_ssh_config_loaded = self._on_ssh_config_loaded
        notebook.add(self.param_panel, text="参数配置")

        self.ssh_panel = SSHPanel(
            notebook,
            ssh_service=self.ssh_service,
            on_connect=self._on_ssh_connect,
            on_disconnect=self._on_ssh_disconnect,
        )
        notebook.add(self.ssh_panel, text="SSH 映射")
        
        logger.info("[CREATE_UI] completed")

    def _wire_callbacks(self) -> None:
        logger.info("[WIRE_CALLBACKS] starting_monitoring, interval=%f", MONITOR_INTERVAL)
        self.monitor_service.start_monitoring(
            interval=MONITOR_INTERVAL,
            callback=lambda s, g: self.root.after(
                0, lambda ms=s, gs=g: self._on_monitor_update(ms, gs)
            ),
        )
        self.log_panel.log("应用已启动", "SYSTEM")
        logger.info("[APP] started")

    def _safe_log(self, message: str, level: str) -> None:
        if level in ("STDOUT", "STDERR"):
            logger.debug("[%s] %s", level, message)
            if level == "STDERR" and message:
                self.root.after(0, lambda: self.log_panel.log(message, "ERROR"))
        else:
            self.root.after(0, lambda: self.log_panel.log(message, level))

    def _load_saved_config(self) -> None:
        logger.info("[LOAD_SAVED_CONFIG] loading")
        result = self.config_service.load()
        if result is None:
            logger.info("[LOAD_SAVED_CONFIG] no_saved_config")
            return

        launch_config, restart_config, ssh_config = result
        self._restart_config = restart_config
        logger.info("[LOAD_SAVED_CONFIG] launch_server_path=%s, param_count=%d",
                    launch_config.server_path, len(launch_config.parameters))

        if launch_config.server_path:
            self.param_panel.set_server_path(launch_config.server_path)
            self.param_panel.load_parameters(launch_config.parameters)
            logger.info("[LOAD_SAVED_CONFIG] server_path_set, parameters_loaded")

        if launch_config.parameters:
            for p in launch_config.parameters:
                if p.name == "-m" and p.value:
                    self.param_panel.set_model_path(p.value)
                    logger.info("[LOAD_SAVED_CONFIG] model_path_set: %s", p.value)
                    break

        if ssh_config.remote_host:
            self._on_ssh_config_loaded(ssh_config)
            self.ssh_panel.update_status(SSHState.DISCONNECTED)
            logger.info("[LOAD_SAVED_CONFIG] ssh_config_loaded: host=%s, port=%d", 
                        ssh_config.remote_host, ssh_config.ssh_port)

        self.toolbar.auto_restart_config.var.set(self._restart_config.auto_restart)
        self.toolbar.set_auto_restart_config(
            self._restart_config.max_restarts,
            self._restart_config.restart_interval,
            self._restart_config.memory_threshold,
        )
        logger.info("[LOAD_SAVED_CONFIG] auto_restart=%s, max=%d, interval=%f, threshold=%f",
                    self._restart_config.auto_restart, self._restart_config.max_restarts,
                    self._restart_config.restart_interval, self._restart_config.memory_threshold)

    def _setup_bindings(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_start(self) -> None:
        logger.info("[ON_START] getting_launch_config")
        self.log_panel.log("正在启动服务器...", "SYSTEM")
        
        try:
            launch_config = self.param_panel.get_launch_config()
            logger.info("[ON_START] server_path=%s, param_count=%d",
                        launch_config.server_path, len(launch_config.parameters))
        except Exception as e:
            logger.error("[ON_START] get_config_error: %s", e)
            messagebox.showerror("错误", "无法获取启动配置")
            return

        errors = self.param_service.validate(launch_config)
        if errors:
            logger.warning("[ON_START] validation_failed: %s", errors)
            errmsg = "\n".join(errors)
            messagebox.showwarning("验证失败", f"配置验证失败:\n{errmsg}")
            self.log_panel.log("启动失败: 配置验证错误", "ERROR")
            return

        logger.info("[ON_START] validation_passed")
        self.toolbar.set_button_state("starting")

        try:
            logger.info("[ON_START] starting_process")
            process = self.process_manager.start(launch_config)
            self._current_process = process
            logger.info("[ON_START] process_started, pid=%d", process.pid)
        except Exception as e:
            logger.error("[ON_START] start_error: %s", e)
            self.log_panel.log(f"启动失败: {e}", "ERROR")
            self.toolbar.set_button_state("stopped")
            return

        self.toolbar.set_button_state("running")
        self.log_panel.log("服务器已启动", "INFO")
        
        if self.toolbar.get_auto_start_ssh():
            logger.info("[ON_START] auto_start_ssh_enabled, will check server ready")
            self._schedule_ssh_auto_start()

    def _on_stop(self) -> None:
        logger.info("[ON_STOP] stopping_server")
        self.log_panel.log("正在停止服务器...", "SYSTEM")
        
        self.process_manager.stop()
        self.toolbar.set_button_state("stopped")
        
        logger.info("[ON_STOP] server_stopped")
        self.log_panel.log("服务器已停止", "INFO")

    def _on_restart(self) -> None:
        logger.info("[ON_RESTART] restarting_server")
        self.log_panel.log("正在重启服务器...", "SYSTEM")
        
        self.process_manager.stop()
        self.toolbar.set_button_state("starting")

        try:
            logger.info("[ON_RESTART] getting_launch_config")
            launch_config = self.param_panel.get_launch_config()
            errors = self.param_service.validate(launch_config)
            if errors:
                logger.warning("[ON_RESTART] validation_failed: %s", errors)
                self.log_panel.log("重启失败: 配置验证错误", "ERROR")
                self.toolbar.set_button_state("stopped")
                return

            logger.info("[ON_RESTART] validation_passed, starting_process")
            self.process_manager.start(launch_config)
            self.toolbar.set_button_state("running")
            logger.info("[ON_RESTART] server_restarted")
            self.log_panel.log("服务器已重启", "INFO")
        except Exception as e:
            logger.error("[ON_RESTART] error: %s", e)
            self.log_panel.log(f"重启失败: {e}", "ERROR")
            self.toolbar.set_button_state("stopped")

    def _on_monitor_update(self, stats: MemoryStats, gpu_stats: object | None = None) -> None:
        self.toolbar.update_memory_display(stats)
        self.toolbar.update_gpu_display(gpu_stats)

    def _on_ssh_connect(self, cfg: SSHConfig) -> None:
        logger.info("[ON_SSH_CONNECT] host=%s, user=%s, local_port=%d, remote_port=%d",
                    cfg.remote_host, cfg.username, cfg.local_port, cfg.remote_port)
        self.log_panel.log("正在连接 SSH...", "SYSTEM")
        
        self.ssh_panel.update_status(SSHState.CONNECTING)
        self.toolbar.update_ssh_status("connecting")
        
        try:
            process = self.ssh_service.connect(cfg)
            self._current_ssh_process = process
            self.ssh_panel.update_status(SSHState.CONNECTED)
            self.toolbar.update_ssh_status("connected")
            logger.info("[ON_SSH_CONNECT] connected, pid=%d", process.pid)
            self.log_panel.log(f"SSH 已连接: {cfg.username}@{cfg.remote_host}", "INFO")
        except Exception as e:
            logger.error("[ON_SSH_CONNECT] error: %s", e)
            self.ssh_panel.update_status(SSHState.DISCONNECTED)
            self.toolbar.update_ssh_status("disconnected")
            self.log_panel.log(f"SSH 连接失败: {e}", "ERROR")

    def _on_ssh_disconnect(self) -> None:
        logger.info("[ON_SSH_DISCONNECT] disconnecting")
        self.log_panel.log("正在断开 SSH...", "SYSTEM")
        
        self.ssh_service.disconnect(self._current_ssh_process)
        self._current_ssh_process = None
        self.ssh_panel.update_status(SSHState.DISCONNECTED)
        self.toolbar.update_ssh_status("disconnected")
        
        logger.info("[ON_SSH_DISCONNECT] disconnected")
        self.log_panel.log("SSH 已断开", "INFO")

    def _on_auto_restart_toggled(self, enabled: bool) -> None:
        logger.info("[ON_AUTO_RESTART] enabled=%s", enabled)
        self._restart_config.auto_restart = enabled

        if enabled:
            try:
                launch_config = self.param_panel.get_launch_config()
                logger.info("[ON_AUTO_RESTART] enabling, max_restarts=%d, memory_threshold=%f",
                            self._restart_config.max_restarts, self._restart_config.memory_threshold)
                self.process_manager.enable_auto_restart(
                    launch_config,
                    self._restart_config,
                    self.monitor_service,
                )
                self.log_panel.log("自动重启已启用", "SYSTEM")
            except Exception as e:
                logger.error("[ON_AUTO_RESTART] enable_error: %s", e)
                self.log_panel.log(f"启用自动重启失败: {e}", "ERROR")
                self.toolbar.auto_restart_config.var.set(False)
                self._restart_config.auto_restart = False
        else:
            logger.info("[ON_AUTO_RESTART] disabling")
            self.process_manager.disable_auto_restart()
            self.log_panel.log("自动重启已禁用", "SYSTEM")

    def _on_auto_restart_config_changed(self, max_restarts: int, interval: float, threshold: float) -> None:
        logger.info("[ON_AUTO_RESTART_CONFIG] max=%d, interval=%f, threshold=%f",
                    max_restarts, interval, threshold)
        self._restart_config.max_restarts = max_restarts
        self._restart_config.restart_interval = interval
        self._restart_config.memory_threshold = threshold

    def _schedule_ssh_auto_start(self) -> None:
        self._ssh_auto_start_check_count = 0
        self._check_server_ready_for_ssh()

    def _check_server_ready_for_ssh(self) -> None:
        if self._ssh_auto_start_check_count >= 10:
            logger.warning("[SSH_AUTO_START] timeout, server not ready after 10 checks")
            self.log_panel.log("SSH 自动启动超时: 服务器未就绪", "WARN")
            return
        
        if not self.process_manager.is_running():
            logger.warning("[SSH_AUTO_START] server not running")
            return
        
        self._ssh_auto_start_check_count += 1
        logger.info("[SSH_AUTO_START] check %d, checking port...", self._ssh_auto_start_check_count)
        
        launch_config = self.param_panel.get_launch_config()
        port = 8080
        for p in launch_config.parameters:
            if p.name == "--port" and p.value:
                try:
                    port = int(p.value)
                    break
                except ValueError:
                    pass
        
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                logger.info("[SSH_AUTO_START] server ready on port %d, starting SSH", port)
                self.log_panel.log(f"服务器就绪 (端口 {port})，自动启动 SSH...", "INFO")
                cfg = self.ssh_panel.get_config()
                self._on_ssh_connect(cfg)
                return
        except Exception as e:
            logger.debug("[SSH_AUTO_START] socket_check_error: %s", e)
        
        self.root.after(1000, self._check_server_ready_for_ssh)

    def _on_ssh_config_loaded(self, ssh_config: SSHConfig | None) -> None:
        logger.info("[ON_SSH_CONFIG_LOADED] ssh_config=%s, key_file=%s", 
                    ssh_config, ssh_config.key_file if ssh_config else None)
        if ssh_config is not None:
            self.ssh_panel._local_port_var.set(str(ssh_config.local_port))
            self.ssh_panel._remote_port_var.set(str(ssh_config.remote_port))
            self.ssh_panel._remote_host_var.set(ssh_config.remote_host)
            self.ssh_panel._username_var.set(ssh_config.username)
            self.ssh_panel._ssh_port_var.set(str(ssh_config.ssh_port))
            self.ssh_panel._key_file_var.set(ssh_config.key_file)
            self.ssh_panel._update_cmd_preview()
            logger.info("[ON_SSH_CONFIG_LOADED] key_file_var_set: %s", self.ssh_panel._key_file_var.get())
            self.log_panel.log(f"SSH 配置已加载: {ssh_config.username}@{ssh_config.remote_host}", "INFO")

    def _on_save_template(self, name: str) -> None:
        params = self.param_panel.get_current_params()
        if self.param_panel.get_model_path():
            params.insert(0, Parameter(
                name="-m",
                value=self.param_panel.get_model_path(),
                category="model",
                required=True,
                description="模型路径",
            ))
        ssh_config = self.ssh_panel.get_config()
        self.param_service.save_template(name, params, ssh_config)
        self.log_panel.log(f"模板已保存: {name}", "INFO")

    def _on_save_as_template(self) -> None:
        from tkinter import simpledialog
        name = simpledialog.askstring("另存为模板", "请输入模板名称:", parent=self.root)
        if not name:
            return
        params = self.param_panel.get_current_params()
        if self.param_panel.get_model_path():
            params.insert(0, Parameter(
                name="-m",
                value=self.param_panel.get_model_path(),
                category="model",
                required=True,
                description="模型路径",
            ))
        ssh_config = self.ssh_panel.get_config()
        self.param_service.save_template(name, params, ssh_config)
        self.log_panel.log(f"模板已保存: {name}", "INFO")
        self.param_panel._template_row.cmb_template["values"] = self.param_service.get_template_names()
        self.param_panel._template_row.cmb_template.set(name)

    def _on_closing(self) -> None:
        logger.info("[ON_CLOSING] shutting_down")
        self.log_panel.log("正在关闭应用...", "SYSTEM")

        self.process_manager.stop()
        self.monitor_service.stop_monitoring()
        self.process_manager.disable_auto_restart()

        try:
            launch_config = self.param_panel.get_launch_config()
            ssh_config = self.ssh_panel.get_config()
            logger.info("[ON_CLOSING] saving_config")
            self.config_service.save(launch_config, self._restart_config, ssh_config)
            logger.info("[ON_CLOSING] config_saved")
        except Exception as e:
            logger.error("[ON_CLOSING] save_error: %s", e)
            self.log_panel.log(f"保存配置失败: {e}", "ERROR")

        logger.info("[ON_CLOSING] app_closed")
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
