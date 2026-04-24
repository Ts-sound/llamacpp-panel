import json
import pytest

from src.models.server_config import HistoryEntry, LaunchConfig, Parameter


class TestParameter:
    def test_to_dict_full(self):
        p = Parameter(
            name="-m",
            category="基础",
            required=True,
            value="model.gguf",
            description="模型文件路径",
        )
        d = p.to_dict()
        assert d == {
            "name": "-m",
            "value": "model.gguf",
            "category": "基础",
            "required": True,
            "description": "模型文件路径",
        }

    def test_to_dict_minimal(self):
        p = Parameter(name="-c", category="基础", required=False)
        d = p.to_dict()
        assert d["name"] == "-c"
        assert d["value"] is None
        assert d["required"] is False
        assert d["description"] == ""

    def test_from_dict_full(self):
        d = {
            "name": "-m",
            "value": "model.gguf",
            "category": "基础",
            "required": True,
            "description": "模型文件路径",
        }
        p = Parameter.from_dict(d)
        assert p.name == "-m"
        assert p.value == "model.gguf"
        assert p.category == "基础"
        assert p.required is True
        assert p.description == "模型文件路径"

    def test_from_dict_missing_optional(self):
        d = {"name": "-c", "category": "基础", "required": False}
        p = Parameter.from_dict(d)
        assert p.value is None
        assert p.description == ""

    def test_from_dict_none_value(self):
        d = {"name": "-m", "value": None, "category": "基础", "required": True}
        p = Parameter.from_dict(d)
        assert p.value is None

    def test_round_trip(self):
        original = Parameter(
            name="--threads",
            category="性能",
            required=False,
            value="4",
            description="线程数",
        )
        restored = Parameter.from_dict(original.to_dict())
        assert restored == original

    def test_json_serializable(self):
        p = Parameter(name="-m", category="基础", required=True, value="m.gguf")
        text = json.dumps(p.to_dict())
        restored = Parameter.from_dict(json.loads(text))
        assert restored == p


class TestLaunchConfig:
    def test_to_dict_with_parameters(self):
        cfg = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server -m model.gguf",
            parameters=[
                Parameter(name="-m", category="基础", required=True, value="model.gguf"),
                Parameter(name="-c", category="基础", required=False, value="2048"),
            ],
            selected_template="最小配置",
        )
        d = cfg.to_dict()
        assert d["server_path"] == "/usr/bin/server"
        assert d["shell_command"] == "/usr/bin/server -m model.gguf"
        assert d["selected_template"] == "最小配置"
        assert len(d["parameters"]) == 2

    def test_to_dict_empty_parameters(self):
        cfg = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server",
        )
        d = cfg.to_dict()
        assert d["parameters"] == []
        assert d["selected_template"] is None

    def test_from_dict_basic(self):
        d = {
            "server_path": "/usr/bin/server",
            "shell_command": "/usr/bin/server -m model.gguf",
            "parameters": [
                {"name": "-m", "category": "基础", "required": True, "value": "model.gguf"},
            ],
            "selected_template": "最小配置",
        }
        cfg = LaunchConfig.from_dict(d)
        assert cfg.server_path == "/usr/bin/server"
        assert cfg.shell_command == "/usr/bin/server -m model.gguf"
        assert len(cfg.parameters) == 1
        assert cfg.parameters[0].name == "-m"
        assert cfg.selected_template == "最小配置"

    def test_from_dict_missing_optional(self):
        d = {
            "server_path": "/usr/bin/server",
            "shell_command": "/usr/bin/server",
        }
        cfg = LaunchConfig.from_dict(d)
        assert cfg.parameters == []
        assert cfg.selected_template is None

    def test_from_dict_with_dict_parameters(self):
        d = {
            "server_path": "/s",
            "shell_command": "/s",
            "parameters": [
                {"name": "-c", "category": "基础", "required": False, "value": "4096"},
            ],
        }
        cfg = LaunchConfig.from_dict(d)
        assert isinstance(cfg.parameters[0], Parameter)
        assert cfg.parameters[0].value == "4096"

    def test_from_dict_with_parameter_objects(self):
        params = [Parameter(name="-m", category="基础", required=True)]
        d = {
            "server_path": "/s",
            "shell_command": "/s",
            "parameters": params,
        }
        cfg = LaunchConfig.from_dict(d)
        assert cfg.parameters[0] is params[0]

    def test_round_trip(self):
        original = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server -m model.gguf -c 4096",
            parameters=[
                Parameter(name="-m", category="基础", required=True, value="model.gguf"),
                Parameter(name="-c", category="基础", required=False, value="4096"),
            ],
            selected_template="全功能",
        )
        restored = LaunchConfig.from_dict(original.to_dict())
        assert restored.server_path == original.server_path
        assert restored.shell_command == original.shell_command
        assert restored.selected_template == original.selected_template
        assert len(restored.parameters) == len(original.parameters)
        for r, o in zip(restored.parameters, original.parameters):
            assert r == o


class TestHistoryEntry:
    def test_to_dict(self):
        h = HistoryEntry(server_path="/usr/bin/server", last_used="2024-01-01T12:00:00")
        d = h.to_dict()
        assert d == {
            "server_path": "/usr/bin/server",
            "last_used": "2024-01-01T12:00:00",
        }

    def test_from_dict(self):
        d = {
            "server_path": "/usr/bin/server",
            "last_used": "2024-01-01T12:00:00",
        }
        h = HistoryEntry.from_dict(d)
        assert h.server_path == "/usr/bin/server"
        assert h.last_used == "2024-01-01T12:00:00"

    def test_round_trip(self):
        original = HistoryEntry(server_path="/path/to/server", last_used="2024-06-01T00:00:00")
        restored = HistoryEntry.from_dict(original.to_dict())
        assert restored == original

    def test_json_serializable(self):
        h = HistoryEntry(server_path="/s", last_used="2024-01-01T00:00:00")
        text = json.dumps(h.to_dict())
        restored = HistoryEntry.from_dict(json.loads(text))
        assert restored == h
