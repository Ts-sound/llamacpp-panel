from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Parameter:
    name: str
    category: str
    required: bool
    value: str | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "category": self.category,
            "required": self.required,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Parameter:
        return cls(
            name=d["name"],
            value=d.get("value"),
            category=d["category"],
            required=d["required"],
            description=d.get("description", ""),
        )


@dataclass
class LaunchConfig:
    server_path: str
    shell_command: str
    parameters: list[Parameter] = field(default_factory=list)
    selected_template: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_path": self.server_path,
            "parameters": [p.to_dict() for p in self.parameters],
            "selected_template": self.selected_template,
            "shell_command": self.shell_command,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LaunchConfig:
        return cls(
            server_path=d["server_path"],
            parameters=[
                Parameter.from_dict(p) if isinstance(p, dict) else p
                for p in d.get("parameters", [])
            ],
            selected_template=d.get("selected_template"),
            shell_command=d["shell_command"],
        )


@dataclass
class HistoryEntry:
    server_path: str
    last_used: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_path": self.server_path,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> HistoryEntry:
        return cls(
            server_path=d["server_path"],
            last_used=d["last_used"],
        )
