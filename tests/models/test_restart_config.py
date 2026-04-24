import json

from src.models.restart_config import RestartConfig, RestartLogEntry


class TestRestartConfig:
    def test_to_dict_defaults(self):
        cfg = RestartConfig()
        d = cfg.to_dict()
        assert d == {
            "auto_restart": False,
            "max_restarts": 3,
            "restart_interval": 5.0,
            "memory_threshold": 90.0,
            "restart_count": 0,
        }

    def test_to_dict_custom(self):
        cfg = RestartConfig(
            auto_restart=True,
            max_restarts=5,
            memory_threshold=80.0,
            restart_count=2,
        )
        d = cfg.to_dict()
        assert d["auto_restart"] is True
        assert d["max_restarts"] == 5
        assert d["memory_threshold"] == 80.0
        assert d["restart_count"] == 2

    def test_from_dict_full(self):
        d = {
            "auto_restart": True,
            "max_restarts": 5,
            "memory_threshold": 80.0,
            "restart_count": 2,
        }
        cfg = RestartConfig.from_dict(d)
        assert cfg.auto_restart is True
        assert cfg.max_restarts == 5
        assert cfg.memory_threshold == 80.0
        assert cfg.restart_count == 2

    def test_from_dict_empty(self):
        cfg = RestartConfig.from_dict({})
        assert cfg.auto_restart is False
        assert cfg.max_restarts == 3
        assert cfg.memory_threshold == 90.0
        assert cfg.restart_count == 0

    def test_from_dict_partial(self):
        d = {"auto_restart": True}
        cfg = RestartConfig.from_dict(d)
        assert cfg.auto_restart is True
        assert cfg.max_restarts == 3
        assert cfg.memory_threshold == 90.0

    def test_round_trip(self):
        original = RestartConfig(
            auto_restart=True,
            max_restarts=10,
            memory_threshold=75.0,
            restart_count=3,
        )
        restored = RestartConfig.from_dict(original.to_dict())
        assert restored == original

    def test_json_serializable(self):
        cfg = RestartConfig(auto_restart=True, max_restarts=5)
        text = json.dumps(cfg.to_dict())
        restored = RestartConfig.from_dict(json.loads(text))
        assert restored == cfg

    def test_default_values(self):
        cfg = RestartConfig()
        assert cfg.auto_restart is False
        assert cfg.max_restarts == 3
        assert cfg.memory_threshold == 90.0
        assert cfg.restart_count == 0


class TestRestartLogEntry:
    def test_instantiation_full(self):
        entry = RestartLogEntry(
            timestamp="2024-01-01T12:00:00",
            reason="memory threshold exceeded",
            exit_code=1,
        )
        assert entry.timestamp == "2024-01-01T12:00:00"
        assert entry.reason == "memory threshold exceeded"
        assert entry.exit_code == 1

    def test_instantiation_no_exit_code(self):
        entry = RestartLogEntry(
            timestamp="2024-01-01T12:00:00",
            reason="process exited",
        )
        assert entry.exit_code is None

    def test_dataclass_equality(self):
        a = RestartLogEntry(timestamp="t1", reason="r1", exit_code=0)
        b = RestartLogEntry(timestamp="t1", reason="r1", exit_code=0)
        assert a == b

    def test_none_exit_code(self):
        entry = RestartLogEntry(timestamp="t1", reason="r1")
        assert entry.exit_code is None

    def test_dataclass_repr(self):
        entry = RestartLogEntry(timestamp="t1", reason="r1")
        r = repr(entry)
        assert "RestartLogEntry" in r
