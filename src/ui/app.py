"""Main application window - orchestrates all UI components and services."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from src.config import MONITOR_INTERVAL
from src.models.monitor import MemoryStats
from src.models.restart_config import RestartConfig
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


class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("llamacpp-panel")
        self.root.geometry("1000x700")

        self._create_services()
        self._create_ui()
        self._wire_callbacks()
        self._load_saved_config()
        self._setup_bindings()

        self._current_ssh_process: object | None = None
        self._restart_config = RestartConfig()

    def _create_services(self) -> None:
        self.config_service = ConfigService()
        self.param_service = ParamService()
        self.monitor_service = MonitorService()
        self.ssh_service = SSHService()
        self.process_manager = ProcessManager(
            callback=lambda msg, level: self._safe_log(msg, level),
        )

    def _create_ui(self) -> None:
        self.toolbar = Toolbar(
            self.root,
            on_start=self._on_start,
            on_stop=self._on_stop,
            on_restart=self._on_restart,
            on_auto_restart=self._on_auto_restart_toggled,
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
        notebook.add(self.param_panel, text="参数配置")

        self.ssh_panel = SSHPanel(
            notebook,
            ssh_service=self.ssh_service,
        )
        notebook.add(self.ssh_panel, text="SSH 映射")

    def _wire_callbacks(self) -> None:
        self.monitor_service.start_monitoring(
            interval=MONITOR_INTERVAL,
            callback=lambda s, g: self.root.after(
                0, lambda ms=s, gs=g: self._on_monitor_update(ms, gs)
            ),
        )

    def _safe_log(self, message: str, level: str) -> None:
        self.root.after(0, lambda: self.log_panel.log(message, level))

    def _load_saved_config(self) -> None:
        result = self.config_service.load()
        if result is None:
            return

        launch_config, restart_config, ssh_config = result
        self._restart_config = restart_config

        if launch_config.server_path:
            self.param_panel.set_server_path(launch_config.server_path)
            self.param_panel.load_parameters(launch_config.parameters)

        if ssh_config.remote_host:
            self.ssh_panel.update_status(SSHState.DISCONNECTED)

        self.toolbar.auto_restart.var.set(self._restart_config.auto_restart)

    def _setup_bindings(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_start(self) -> None:
        try:
            launch_config = self.param_panel.get_launch_config()
        except Exception:
            messagebox.showerror("错误", "无法获取启动配置")
            return

        errors = self.param_service.validate(launch_config)
        if errors:
            errmsg = "\n".join(errors)
            messagebox.showwarning("验证失败", f"配置验证失败:\n{errmsg}")
            return

        self.toolbar.set_button_state("starting")
        self.log_panel.log("Starting server...", "SYSTEM")

        try:
            self.process_manager.start(launch_config)
        except Exception as e:
            self.log_panel.log(f"Failed to start: {e}", "ERROR")
            self.toolbar.set_button_state("stopped")
            return

        self.toolbar.set_button_state("running")
        self.log_panel.log(f"Server started: {launch_config.shell_command}", "INFO")

    def _on_stop(self) -> None:
        self.log_panel.log("Stopping server...", "SYSTEM")
        self.process_manager.stop()
        self.toolbar.set_button_state("stopped")
        self.log_panel.log("Server stopped", "INFO")

    def _on_restart(self) -> None:
        self.log_panel.log("Restarting server...", "SYSTEM")
        self.process_manager.stop()
        self.toolbar.set_button_state("starting")

        try:
            launch_config = self.param_panel.get_launch_config()
            errors = self.param_service.validate(launch_config)
            if errors:
                self.log_panel.log(f"Validation failed: {'; '.join(errors)}", "ERROR")
                self.toolbar.set_button_state("stopped")
                return

            self.process_manager.start(launch_config)
            self.toolbar.set_button_state("running")
            self.log_panel.log("Server restarted", "INFO")
        except Exception as e:
            self.log_panel.log(f"Failed to restart: {e}", "ERROR")
            self.toolbar.set_button_state("stopped")

    def _on_monitor_update(self, stats: MemoryStats, gpu_stats: object | None = None) -> None:
        self.toolbar.update_memory_display(stats)
        self.toolbar.update_gpu_display(gpu_stats)

    def _on_auto_restart_toggled(self, enabled: bool) -> None:
        self._restart_config.auto_restart = enabled

        if enabled:
            try:
                launch_config = self.param_panel.get_launch_config()
                self.process_manager.enable_auto_restart(
                    launch_config,
                    self._restart_config,
                    self.monitor_service,
                )
                self.log_panel.log("Auto-restart enabled", "SYSTEM")
            except Exception as e:
                self.log_panel.log(f"Failed to enable auto-restart: {e}", "ERROR")
                self.toolbar.auto_restart.var.set(False)
                self._restart_config.auto_restart = False
        else:
            self.process_manager.disable_auto_restart()
            self.log_panel.log("Auto-restart disabled", "SYSTEM")

    def _on_closing(self) -> None:
        self.log_panel.log("Shutting down...", "SYSTEM")

        self.process_manager.stop()
        self.monitor_service.stop_monitoring()
        self.process_manager.disable_auto_restart()

        try:
            launch_config = self.param_panel.get_launch_config()
            ssh_config = self.ssh_panel.get_config()
            self.config_service.save(launch_config, self._restart_config, ssh_config)
        except Exception as e:
            self.log_panel.log(f"Failed to save config: {e}", "ERROR")

        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
