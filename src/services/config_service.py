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
        logger.info("[SAVE_CONFIG] path=%s", self._config_path)
        
        with self._lock:
            data: dict[str, Any] = {
                "launch": launch_config.to_dict(),
                "restart": restart_config.to_dict(),
                "ssh": ssh_config.to_dict(),
                "history": [h.to_dict() for h in self._history],
            }
            logger.debug("[SAVE_CONFIG] data_keys=%s", list(data.keys()))

            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                fd, tmp_path = tempfile.mkstemp(
                    dir=str(self._config_path.parent),
                    suffix=".tmp",
                )
                logger.debug("[SAVE_CONFIG] tmp_path=%s", tmp_path)
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    Path(tmp_path).replace(self._config_path)
                    logger.info("[SAVE_CONFIG] success: %s", self._config_path)
                except Exception as e:
                    Path(tmp_path).unlink(missing_ok=True)
                    logger.error("[SAVE_CONFIG] write_error: %s", e)
                    raise
            except Exception as e:
                logger.error("[SAVE_CONFIG] error: %s", e)
                raise ConfigError(f"Failed to save config: {e}") from e

    def load(
        self,
    ) -> tuple[LaunchConfig, RestartConfig, SSHConfig] | None:
        logger.info("[LOAD_CONFIG] path=%s", self._config_path)
        
        with self._lock:
            if not self._config_path.exists():
                logger.info("[LOAD_CONFIG] file_not_found, returning_none")
                return None

            try:
                content = self._config_path.read_text(encoding="utf-8")
                data: dict[str, Any] = json.loads(content)
                logger.debug("[LOAD_CONFIG] data_keys=%s", list(data.keys()))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("[LOAD_CONFIG] parse_error: %s", e)
                return None

            launch = LaunchConfig.from_dict(data.get("launch", {}))
            restart = RestartConfig.from_dict(data.get("restart", {}))
            ssh = SSHConfig.from_dict(data.get("ssh", {}))
            logger.info("[LOAD_CONFIG] launch_server_path=%s, param_count=%d",
                        launch.server_path, len(launch.parameters))
            logger.info("[LOAD_CONFIG] restart_auto_restart=%s, max_restarts=%d",
                        restart.auto_restart, restart.max_restarts)

            self._history = [
                HistoryEntry.from_dict(h) for h in data.get("history", [])
            ]

            logger.info("[LOAD_CONFIG] success")
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
