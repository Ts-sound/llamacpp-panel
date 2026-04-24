from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SSHConfig:
    local_port: int
    remote_port: int
    remote_host: str
    username: str
    ssh_port: int = 22
    enabled: bool = False
    password: str = ""
    key_file: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_port": self.local_port,
            "remote_port": self.remote_port,
            "remote_host": self.remote_host,
            "username": self.username,
            "ssh_port": self.ssh_port,
            "enabled": self.enabled,
            "password": self.password,
            "key_file": self.key_file,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SSHConfig:
        return cls(
            local_port=d["local_port"],
            remote_port=d["remote_port"],
            remote_host=d["remote_host"],
            username=d["username"],
            ssh_port=d.get("ssh_port", 22),
            enabled=d.get("enabled", False),
            password=d.get("password", ""),
            key_file=d.get("key_file", ""),
        )


class SSHState:
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
