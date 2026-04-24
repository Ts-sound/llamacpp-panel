from __future__ import annotations

import logging
import shlex
import threading
from subprocess import PIPE, Popen

from src.models.errors import SSHError
from src.models.ssh_config import SSHConfig, SSHState
from src.utils.cross_platform import kill_process

logger = logging.getLogger(__name__)


class SSHService:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    def build_command(self, cfg: SSHConfig) -> str:
        parts = [
            "ssh",
            "-R",
            f"0.0.0.0:{cfg.remote_port}:127.0.0.1:{cfg.local_port}",
            "-o",
            "StrictHostKeyChecking=no",
            "-N",
            f"{cfg.username}@{cfg.remote_host}",
        ]
        return " ".join(shlex.quote(p) for p in parts)

    def connect(self, cfg: SSHConfig) -> Popen[bytes]:
        command = self.build_command(cfg)
        logger.info("SSH connecting: %s", command)
        try:
            process = Popen(
                shlex.split(command),
                stdout=PIPE,
                stderr=PIPE,
            )
        except OSError as e:
            raise SSHError(f"Failed to start SSH process: {e}")
        logger.info("SSH process started, pid=%s", process.pid)
        return process

    def disconnect(self, process: Popen[bytes] | None) -> None:
        with self._lock:
            if process is None:
                return
            logger.info("Disconnecting SSH process, pid=%s", process.pid)
            kill_process(process)

    def get_state(self, process: Popen[bytes] | None) -> str:
        if process is None:
            return SSHState.DISCONNECTED
        if process.poll() is None:
            return SSHState.CONNECTED
        return SSHState.DISCONNECTED
