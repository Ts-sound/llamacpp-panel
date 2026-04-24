import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.models.restart_config import RestartConfig
from src.models.server_config import HistoryEntry, LaunchConfig, Parameter
from src.models.ssh_config import SSHConfig
from src.services.config_service import ConfigService
from src.models.errors import ConfigError


class TestSaveLoadRoundTrip:
    def test_save_and_load(self, tmp_path):
        config_file = tmp_path / "config.json"
        svc = ConfigService(str(config_file))

        launch = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server -m model.gguf",
            parameters=[
                Parameter(name="-m", category="基础", required=True, value="model.gguf"),
            ],
            selected_template="最小配置",
        )
        restart = RestartConfig(auto_restart=True, max_restarts=5)
        ssh = SSHConfig(
            local_port=8080,
            remote_port=8080,
            remote_host="172.18.122.71",
            username="root",
            enabled=True,
        )

        svc.save(launch, restart, ssh)
        result = svc.load()

        assert result is not None
        l, r, s = result
        assert l.server_path == "/usr/bin/server"
        assert l.selected_template == "最小配置"
        assert len(l.parameters) == 1
        assert r.auto_restart is True
        assert r.max_restarts == 5
        assert s.enabled is True
        assert s.local_port == 8080

    def test_load_nonexistent(self, tmp_path):
        config_file = tmp_path / "nonexistent.json"
        svc = ConfigService(str(config_file))
        result = svc.load()
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json", encoding="utf-8")
        svc = ConfigService(str(config_file))
        result = svc.load()
        assert result is None

    def test_empty_config_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("", encoding="utf-8")
        svc = ConfigService(str(config_file))
        result = svc.load()
        assert result is None

    def test_partial_data(self, tmp_path):
        config_file = tmp_path / "config.json"
        data = {
            "launch": {"server_path": "/s", "shell_command": "/s"},
            "ssh": {"local_port": 8080, "remote_port": 8080, "remote_host": "h", "username": "u"},
        }
        config_file.write_text(json.dumps(data), encoding="utf-8")
        svc = ConfigService(str(config_file))
        result = svc.load()
        assert result is not None
        l, r, s = result
        assert l.server_path == "/s"
        assert r.auto_restart is False
        assert s.enabled is False

    def test_config_path_created(self, tmp_path):
        nested = tmp_path / "a" / "b" / "config.json"
        svc = ConfigService(str(nested))

        launch = LaunchConfig(server_path="/s", shell_command="/s")
        restart = RestartConfig()
        ssh = SSHConfig(local_port=8080, remote_port=8080, remote_host="h", username="u")

        svc.save(launch, restart, ssh)
        assert nested.exists()


class TestHistory:
    def test_save_and_get_history(self, tmp_path):
        config_file = tmp_path / "config.json"
        svc = ConfigService(str(config_file))

        entry1 = HistoryEntry(server_path="/path/a", last_used="2024-01-02T00:00:00")
        entry2 = HistoryEntry(server_path="/path/b", last_used="2024-01-01T00:00:00")
        entry3 = HistoryEntry(server_path="/path/c", last_used="2024-01-03T00:00:00")

        svc.save_history(entry1)
        svc.save_history(entry2)
        svc.save_history(entry3)

        history = svc.get_history()
        assert len(history) == 3
        assert history[0].server_path == "/path/c"
        assert history[1].server_path == "/path/a"
        assert history[2].server_path == "/path/b"

    def test_duplicate_server_path_updates(self, tmp_path):
        config_file = tmp_path / "config.json"
        svc = ConfigService(str(config_file))

        svc.save_history(HistoryEntry(server_path="/s", last_used="2024-01-01T00:00:00"))
        svc.save_history(HistoryEntry(server_path="/s", last_used="2024-06-01T00:00:00"))

        history = svc.get_history()
        assert len(history) == 1
        assert history[0].last_used == "2024-06-01T00:00:00"

    def test_history_persists_in_save_load(self, tmp_path):
        config_file = tmp_path / "config.json"
        svc1 = ConfigService(str(config_file))

        svc1.save_history(HistoryEntry(server_path="/s", last_used="2024-01-01T00:00:00"))

        launch = LaunchConfig(server_path="/s", shell_command="/s")
        restart = RestartConfig()
        ssh = SSHConfig(local_port=8080, remote_port=8080, remote_host="h", username="u")
        svc1.save(launch, restart, ssh)

        svc2 = ConfigService(str(config_file))
        result = svc2.load()
        assert result is not None

        history = svc2.get_history()
        assert len(history) == 1
        assert history[0].server_path == "/s"

    def test_empty_history(self, tmp_path):
        config_file = tmp_path / "config.json"
        svc = ConfigService(str(config_file))
        assert svc.get_history() == []

    def test_history_sorted_descending(self, tmp_path):
        config_file = tmp_path / "config.json"
        svc = ConfigService(str(config_file))

        dates = ["2024-03-01", "2024-01-01", "2024-02-01"]
        for i, d in enumerate(dates):
            svc.save_history(HistoryEntry(server_path=f"/s{i}", last_used=f"{d}T00:00:00"))

        history = svc.get_history()
        timestamps = [h.last_used for h in history]
        assert timestamps == sorted(timestamps, reverse=True)


class TestConfigError:
    def test_save_raises_on_io_error(self, tmp_path):
        """ConfigError is raised when save fails due to I/O error."""
        svc = ConfigService(str(tmp_path / "config.json"))

        launch = LaunchConfig(server_path="/s", shell_command="/s")
        restart = RestartConfig()
        ssh = SSHConfig(local_port=8080, remote_port=8080, remote_host="h", username="u")

        with patch.object(Path, "replace", side_effect=OSError("disk full")):
            with pytest.raises(ConfigError):
                svc.save(launch, restart, ssh)
