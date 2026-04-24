from __future__ import annotations

import logging
import shlex
import subprocess
import threading
from subprocess import Popen
from typing import Callable

from src.models.errors import ProcessError
from src.models.monitor import MemoryStats
from src.models.restart_config import RestartConfig
from src.models.server_config import LaunchConfig
from src.utils.cross_platform import kill_process

logger = logging.getLogger(__name__)

_POLL_INTERVAL: float = 3.0


class ProcessManager:
    def __init__(
        self,
        callback: Callable[[str, str], None] | None = None,
    ) -> None:
        self._callback = callback
        self._stop_event = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        self._current_process: Popen[bytes] | None = None
        self._launch_config: LaunchConfig | None = None
        self._restart_config: RestartConfig | None = None
        self._stdout_thread: threading.Thread | None = None
        self._stderr_thread: threading.Thread | None = None

    def start(self, config: LaunchConfig) -> Popen[bytes]:
        logger.info("[START_PROC] shell_command=%s", config.shell_command)
        
        args = shlex.split(config.shell_command)
        logger.debug("[START_PROC] args=%s", args)
        
        try:
            process = Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info("[START_PROC] pid=%d, process_created", process.pid)
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.error("[START_PROC] error: %s", exc)
            raise ProcessError(
                f"Failed to start process: {exc}",
            ) from exc

        if process.returncode is not None:
            stderr = ""
            if process.stderr is not None:
                try:
                    stderr = process.stderr.read()
                except Exception:
                    pass
            logger.error("[START_PROC] immediate_exit: returncode=%d, stderr=%s", 
                         process.returncode, stderr)
            raise ProcessError(
                f"Process exited immediately with code {process.returncode}",
                exit_code=process.returncode,
                stderr=stderr,
            )

        self._current_process = process
        self._log("Server started", "INFO")

        self._stdout_thread = threading.Thread(
            target=self._read_output, args=(process.stdout, "STDOUT"), daemon=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_output, args=(process.stderr, "STDERR"), daemon=True,
        )
        self._stdout_thread.start()
        self._stderr_thread.start()
        logger.info("[START_PROC] stdout_thread_started, stderr_thread_started")

        return process

    def stop(self, process: Popen[bytes] | None = None) -> None:
        target = process if process is not None else self._current_process
        if target is None:
            logger.info("[STOP_PROC] no_process_to_stop")
            return
        
        logger.info("[STOP_PROC] pid=%d, stopping", target.pid)
        
        if target.stdout:
            target.stdout.close()
        if target.stderr:
            target.stderr.close()
        
        kill_process(target, timeout=5)
        
        if target is self._current_process:
            self._current_process = None
        
        logger.info("[STOP_PROC] pid=%d, stopped", target.pid)
        self._log("Server stopped", "INFO")

    def is_running(self, process: Popen[bytes] | None = None) -> bool:
        target = process if process is not None else self._current_process
        if target is None:
            return False
        return target.poll() is None

    def enable_auto_restart(
        self,
        config: LaunchConfig,
        restart_cfg: RestartConfig,
        monitor_service: object,
    ) -> None:
        logger.info("[ENABLE_AUTO_RESTART] max_restarts=%d, memory_threshold=%f", 
                    restart_cfg.max_restarts, restart_cfg.memory_threshold)
        
        self._launch_config = config
        self._restart_config = restart_cfg
        self._stop_event.clear()

        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            logger.info("[ENABLE_AUTO_RESTART] monitor_thread_already_running")
            return

        self._monitor_thread = threading.Thread(
            target=self._restart_loop,
            args=(monitor_service,),
            daemon=True,
        )
        self._monitor_thread.start()
        logger.info("[ENABLE_AUTO_RESTART] monitor_thread_started")
        self._log("Auto-restart enabled", "INFO")

    def disable_auto_restart(self) -> None:
        logger.info("[DISABLE_AUTO_RESTART] stopping")
        self._stop_event.set()
        
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
            logger.info("[DISABLE_AUTO_RESTART] monitor_thread_joined")
        
        self._monitor_thread = None
        logger.info("[DISABLE_AUTO_RESTART] disabled")
        self._log("Auto-restart disabled", "INFO")

    def _restart_loop(self, monitor_service: object) -> None:
        from src.services.monitor_service import MonitorService

        ms: MonitorService | None
        ms = monitor_service if isinstance(monitor_service, MonitorService) else None

        logger.info("[RESTART_LOOP] started, poll_interval=%f", _POLL_INTERVAL)

        while not self._stop_event.is_set():
            if self._restart_config is None:
                logger.warning("[RESTART_LOOP] restart_config_none, breaking")
                break

            process_running = self.is_running()
            logger.debug("[RESTART_LOOP] process_running=%s", process_running)

            if not process_running:
                if self._restart_config.auto_restart:
                    logger.warning("[RESTART_LOOP] process_exited, auto_restart_enabled")
                    self._do_restart("process exited unexpectedly")
                else:
                    self._log("Server crashed (auto-restart disabled)", "WARNING")
                    logger.warning("[RESTART_LOOP] process_exited, auto_restart_disabled")
                self._stop_event.wait(timeout=_POLL_INTERVAL)
                continue

            if ms is not None and self._restart_config.memory_threshold < 100.0:
                try:
                    stats: MemoryStats = ms.get_memory_stats()
                    logger.debug("[RESTART_LOOP] memory_percent=%f, threshold=%f", 
                                 stats.percent, self._restart_config.memory_threshold)
                    if stats.percent >= self._restart_config.memory_threshold:
                        logger.warning("[RESTART_LOOP] memory_threshold_exceeded")
                        self._do_restart(f"memory threshold exceeded ({stats.percent:.1f}%)")
                        self._stop_event.wait(timeout=_POLL_INTERVAL)
                        continue
                except Exception as e:
                    logger.warning("[RESTART_LOOP] get_memory_stats_error: %s", e)

            self._stop_event.wait(timeout=_POLL_INTERVAL)

    def _do_restart(self, reason: str) -> None:
        logger.info("[DO_RESTART] reason=%s", reason)
        
        if self._launch_config is None or self._restart_config is None:
            logger.warning("[DO_RESTART] config_none, skipping")
            return

        rc = self._restart_config
        rc.restart_count += 1
        logger.info("[DO_RESTART] restart_count=%d, max_restarts=%d", 
                    rc.restart_count, rc.max_restarts)

        if rc.restart_count > rc.max_restarts:
            logger.error("[DO_RESTART] limit_reached: max_restarts=%d", rc.max_restarts)
            self._log(
                f"Auto-restart limit reached ({rc.max_restarts}), giving up",
                "ERROR",
            )
            return

        self._log(f"Auto-restarting ({rc.restart_count}/{rc.max_restarts}): {reason}", "WARNING")

        self.stop()
        try:
            logger.info("[DO_RESTART] starting_new_process")
            self.start(self._launch_config)
            logger.info("[DO_RESTART] success")
        except ProcessError as exc:
            logger.error("[DO_RESTART] failed: %s", exc)
            self._log(f"Auto-restart failed: {exc}", "ERROR")

    def _read_output(self, stream, level: str) -> None:
        if stream is None:
            logger.warning("[READ_OUTPUT] stream_none, level=%s", level)
            return
        logger.info("[READ_OUTPUT] thread_started, level=%s", level)
        try:
            for line in iter(stream.readline, ""):
                line = line.rstrip("\n\r")
                if line:
                    tagged_line = f"[{level}] {line}"
                    logger.debug(tagged_line)
                    self._log(line, level if level in ("STDOUT", "STDERR") else level)
        except Exception as e:
            logger.warning("[READ_OUTPUT] exception: %s", e)

    def _log(self, message: str, level: str) -> None:
        log_method = {
            "DEBUG": logger.debug,
            "INFO": logger.info,
            "WARN": logger.warning,
            "WARNING": logger.warning,
            "ERROR": logger.error,
            "SYSTEM": logger.info,
        }.get(level, logger.info)
        log_method(message)

        if self._callback is not None:
            self._callback(message, level)
