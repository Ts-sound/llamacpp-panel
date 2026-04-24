from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from src.config import CONFIG_PATH
from src.models.errors import ConfigError
from src.models.restart_config import RestartConfig
from src.models.server_config import HistoryEntry, LaunchConfig
from src.models.ssh_config import SSHConfig

logger = logging.getLogger(__name__)


class ConfigService:
    def __init__(self, config_path: str = None) -> None:
        self._config_path = Path(config_path) if config_path else Path(CONFIG_PATH)
        self._lock = threading.Lock()
        self._history: list[HistoryEntry] = []

    def save(
        self,
        launch_config: LaunchConfig,
        restart_config: RestartConfig,
        ssh_config: SSHConfig,
    ) -> None:
        with self._lock:
            data: dict[str, Any] = {
                "launch": launch_config.to_dict(),
                "restart": restart_config.to_dict(),
                "ssh": ssh_config.to_dict(),
                "history": [h.to_dict() for h in self._history],
            }

            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                fd, tmp_path = tempfile.mkstemp(
                    dir=str(self._config_path.parent),
                    suffix=".tmp",
                )
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    Path(tmp_path).replace(self._config_path)
                except Exception:
                    Path(tmp_path).unlink(missing_ok=True)
                    raise
            except Exception as e:
                raise ConfigError(f"Failed to save config: {e}") from e

    def load(
        self,
    ) -> tuple[LaunchConfig, RestartConfig, SSHConfig] | None:
        with self._lock:
            if not self._config_path.exists():
                return None

            try:
                content = self._config_path.read_text(encoding="utf-8")
                data: dict[str, Any] = json.loads(content)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load config: %s", e)
                return None

            launch = LaunchConfig.from_dict(data.get("launch", {}))
            restart = RestartConfig.from_dict(data.get("restart", {}))
            ssh = SSHConfig.from_dict(data.get("ssh", {}))

            self._history = [
                HistoryEntry.from_dict(h) for h in data.get("history", [])
            ]

            return launch, restart, ssh

    def save_history(self, entry: HistoryEntry) -> None:
        with self._lock:
            for i, existing in enumerate(self._history):
                if existing.server_path == entry.server_path:
                    self._history[i] = entry
                    return
            self._history.append(entry)

    def get_history(self) -> list[HistoryEntry]:
        with self._lock:
            return sorted(self._history, key=lambda e: e.last_used, reverse=True)
