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
        logger.info("[SSH_BUILD_CMD] local_port=%d, remote_port=%d, host=%s, user=%s",
                    cfg.local_port, cfg.remote_port, cfg.remote_host, cfg.username)
        logger.debug("[SSH_BUILD_CMD] key_file=%s, password_set=%s", 
                     cfg.key_file, bool(cfg.password))
        
        parts = ["ssh"]
        if cfg.password:
            parts = ["sshpass", "-p", cfg.password] + parts
        parts.extend([
            "-R",
            f"0.0.0.0:{cfg.remote_port}:127.0.0.1:{cfg.local_port}",
            "-o",
            "StrictHostKeyChecking=no",
            "-N",
        ])
        if cfg.key_file:
            parts.extend(["-i", cfg.key_file])
        parts.append(f"{cfg.username}@{cfg.remote_host}")
        
        command = " ".join(shlex.quote(p) for p in parts)
        logger.info("[SSH_BUILD_CMD] result=%s", command)
        return command

    def connect(self, cfg: SSHConfig) -> Popen[bytes]:
        command = self.build_command(cfg)
        logger.info("[SSH_CONNECT] host=%s, user=%s, command=%s", 
                    cfg.remote_host, cfg.username, command)
        
        try:
            process = Popen(
                shlex.split(command),
                stdout=PIPE,
                stderr=PIPE,
            )
            logger.info("[SSH_CONNECT] pid=%d, process_started", process.pid)
        except OSError as e:
            logger.error("[SSH_CONNECT] error: %s", e)
            raise SSHError(f"Failed to start SSH process: {e}")
        
        return process

    def disconnect(self, process: Popen[bytes] | None) -> None:
        with self._lock:
            if process is None:
                logger.info("[SSH_DISCONNECT] no_process")
                return
            logger.info("[SSH_DISCONNECT] pid=%d, stopping", process.pid)
            kill_process(process)
            logger.info("[SSH_DISCONNECT] pid=%d, stopped", process.pid)

    def get_state(self, process: Popen[bytes] | None) -> str:
        if process is None:
            return SSHState.DISCONNECTED
        if process.poll() is None:
            return SSHState.CONNECTED
        return SSHState.DISCONNECTED
