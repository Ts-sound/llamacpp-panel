from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SSHConfig:
    local_port: int
    remote_port: int
    remote_host: str
    username: str
    enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_port": self.local_port,
            "remote_port": self.remote_port,
            "remote_host": self.remote_host,
            "username": self.username,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SSHConfig:
        return cls(
            local_port=d["local_port"],
            remote_port=d["remote_port"],
            remote_host=d["remote_host"],
            username=d["username"],
            enabled=d.get("enabled", False),
        )


class SSHState:
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
