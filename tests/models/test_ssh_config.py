import json

from src.models.ssh_config import SSHConfig, SSHState


class TestSSHConfig:
    def test_to_dict_default(self):
        cfg = SSHConfig(
            local_port=8080,
            remote_port=8080,
            remote_host="172.18.122.71",
            username="root",
        )
        d = cfg.to_dict()
        assert d == {
            "local_port": 8080,
            "remote_port": 8080,
            "remote_host": "172.18.122.71",
            "username": "root",
            "ssh_port": 22,
            "enabled": False,
            "password": "",
            "key_file": "",
        }

    def test_to_dict_enabled(self):
        cfg = SSHConfig(
            local_port=9090,
            remote_port=9090,
            remote_host="example.com",
            username="admin",
            enabled=True,
        )
        d = cfg.to_dict()
        assert d["enabled"] is True

    def test_from_dict_full(self):
        d = {
            "local_port": 8080,
            "remote_port": 8080,
            "remote_host": "172.18.122.71",
            "username": "root",
            "enabled": True,
        }
        cfg = SSHConfig.from_dict(d)
        assert cfg.local_port == 8080
        assert cfg.remote_port == 8080
        assert cfg.remote_host == "172.18.122.71"
        assert cfg.username == "root"
        assert cfg.enabled is True

    def test_from_dict_missing_enabled(self):
        d = {
            "local_port": 8080,
            "remote_port": 8080,
            "remote_host": "host",
            "username": "user",
        }
        cfg = SSHConfig.from_dict(d)
        assert cfg.enabled is False

    def test_round_trip(self):
        original = SSHConfig(
            local_port=8080,
            remote_port=9090,
            remote_host="example.com",
            username="admin",
            enabled=True,
        )
        restored = SSHConfig.from_dict(original.to_dict())
        assert restored == original

    def test_json_serializable(self):
        cfg = SSHConfig(
            local_port=8080,
            remote_port=8080,
            remote_host="172.18.122.71",
            username="root",
        )
        text = json.dumps(cfg.to_dict())
        restored = SSHConfig.from_dict(json.loads(text))
        assert restored == cfg

    def test_different_ports(self):
        cfg = SSHConfig(
            local_port=3000,
            remote_port=8080,
            remote_host="host",
            username="user",
        )
        assert cfg.local_port != cfg.remote_port


class TestSSHState:
    def test_disconnected(self):
        assert SSHState.DISCONNECTED == "disconnected"

    def test_connecting(self):
        assert SSHState.CONNECTING == "connecting"

    def test_connected(self):
        assert SSHState.CONNECTED == "connected"

    def test_states_are_strings(self):
        assert isinstance(SSHState.DISCONNECTED, str)
        assert isinstance(SSHState.CONNECTING, str)
        assert isinstance(SSHState.CONNECTED, str)

    def test_states_unique(self):
        states = [SSHState.DISCONNECTED, SSHState.CONNECTING, SSHState.CONNECTED]
        assert len(set(states)) == 3

    def test_state_not_mutable_via_instance(self):
        assert SSHState.DISCONNECTED == "disconnected"
        SSHState.DISCONNECTED = "modified"
        assert SSHState.DISCONNECTED == "modified"
        SSHState.DISCONNECTED = "disconnected"
