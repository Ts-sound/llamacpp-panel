from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RestartConfig:
    auto_restart: bool = False
    max_restarts: int = 3
    memory_threshold: float = 90.0
    restart_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "auto_restart": self.auto_restart,
            "max_restarts": self.max_restarts,
            "memory_threshold": self.memory_threshold,
            "restart_count": self.restart_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RestartConfig:
        return cls(
            auto_restart=d.get("auto_restart", False),
            max_restarts=d.get("max_restarts", 3),
            memory_threshold=d.get("memory_threshold", 90.0),
            restart_count=d.get("restart_count", 0),
        )


@dataclass
class RestartLogEntry:
    timestamp: str
    reason: str
    exit_code: int | None = None
