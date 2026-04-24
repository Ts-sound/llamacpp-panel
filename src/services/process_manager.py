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

    def start(self, config: LaunchConfig) -> Popen[bytes]:
        args = shlex.split(config.shell_command)
        try:
            process = Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except (FileNotFoundError, PermissionError, OSError) as exc:
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
            raise ProcessError(
                f"Process exited immediately with code {process.returncode}",
                exit_code=process.returncode,
                stderr=stderr,
            )

        self._current_process = process
        self._log("Server started", "INFO")
        return process

    def stop(self, process: Popen[bytes] | None = None) -> None:
        target = process if process is not None else self._current_process
        if target is None:
            return
        kill_process(target, timeout=5)
        if target is self._current_process:
            self._current_process = None
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
        self._launch_config = config
        self._restart_config = restart_cfg
        self._stop_event.clear()

        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return

        self._monitor_thread = threading.Thread(
            target=self._restart_loop,
            args=(monitor_service,),
            daemon=True,
        )
        self._monitor_thread.start()
        self._log("Auto-restart enabled", "INFO")

    def disable_auto_restart(self) -> None:
        self._stop_event.set()
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        self._monitor_thread = None
        self._log("Auto-restart disabled", "INFO")

    def _restart_loop(self, monitor_service: object) -> None:
        from src.services.monitor_service import MonitorService

        ms: MonitorService | None
        ms = monitor_service if isinstance(monitor_service, MonitorService) else None

        while not self._stop_event.is_set():
            if self._restart_config is None:
                break

            process_running = self.is_running()

            if not process_running:
                if self._restart_config.auto_restart:
                    self._do_restart("process exited unexpectedly")
                else:
                    self._log("Server crashed (auto-restart disabled)", "WARNING")
                self._stop_event.wait(timeout=_POLL_INTERVAL)
                continue

            if ms is not None and self._restart_config.memory_threshold < 100.0:
                try:
                    stats: MemoryStats = ms.get_memory_stats()
                    if stats.percent >= self._restart_config.memory_threshold:
                        self._do_restart(f"memory threshold exceeded ({stats.percent:.1f}%)")
                        self._stop_event.wait(timeout=_POLL_INTERVAL)
                        continue
                except Exception:
                    pass

            self._stop_event.wait(timeout=_POLL_INTERVAL)

    def _do_restart(self, reason: str) -> None:
        if self._launch_config is None or self._restart_config is None:
            return

        rc = self._restart_config
        rc.restart_count += 1

        if rc.restart_count > rc.max_restarts:
            self._log(
                f"Auto-restart limit reached ({rc.max_restarts}), giving up",
                "ERROR",
            )
            return

        self._log(f"Auto-restarting ({rc.restart_count}/{rc.max_restarts}): {reason}", "WARNING")

        self.stop()
        try:
            self.start(self._launch_config)
        except ProcessError as exc:
            self._log(f"Auto-restart failed: {exc}", "ERROR")

    def _log(self, message: str, level: str) -> None:
        logger.log(
            {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}.get(
                level, logging.INFO
            ),
            message,
        )
        if self._callback is not None:
            self._callback(message, level)
