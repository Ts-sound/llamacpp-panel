from unittest.mock import MagicMock, patch

import pytest

from src.models.errors import SSHError
from src.models.ssh_config import SSHConfig, SSHState
from src.services.ssh_service import SSHService


class TestBuildCommand:
    def setup_method(self):
        self.service = SSHService()

    def test_basic_command(self):
        cfg = SSHConfig(
            local_port=8080,
            remote_port=8080,
            remote_host="172.18.122.71",
            username="root",
        )
        cmd = self.service.build_command(cfg)
        assert "ssh" in cmd
        assert "-R" in cmd
        assert "-N" in cmd
        assert "0.0.0.0:8080:127.0.0.1:8080" in cmd
        assert "root@172.18.122.71" in cmd
        assert "StrictHostKeyChecking=no" in cmd

    def test_different_ports(self):
        cfg = SSHConfig(
            local_port=3000,
            remote_port=9090,
            remote_host="example.com",
            username="admin",
        )
        cmd = self.service.build_command(cfg)
        assert "0.0.0.0:9090:127.0.0.1:3000" in cmd
        assert "admin@example.com" in cmd

    def test_quoted_arguments(self):
        cfg = SSHConfig(
            local_port=8080,
            remote_port=8080,
            remote_host="my host.com",
            username="my user",
        )
        cmd = self.service.build_command(cfg)
        assert "my" in cmd


class TestConnect:
    def setup_method(self):
        self.service = SSHService()

    def test_connect_success(self):
        cfg = SSHConfig(
            local_port=8080,
            remote_port=8080,
            remote_host="172.18.122.71",
            username="root",
        )
        mock_process = MagicMock()
        mock_process.pid = 12345

        with patch("src.services.ssh_service.Popen", return_value=mock_process) as mock_popen:
            result = self.service.connect(cfg)

        assert result is mock_process
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert "ssh" in args[0]

    def test_connect_os_error(self):
        cfg = SSHConfig(
            local_port=8080,
            remote_port=8080,
            remote_host="nonexistent",
            username="root",
        )

        with patch(
            "src.services.ssh_service.Popen",
            side_effect=OSError("ssh not found"),
        ):
            with pytest.raises(SSHError) as exc_info:
                self.service.connect(cfg)
        assert "Failed to start SSH process" in str(exc_info.value)


class TestDisconnect:
    def setup_method(self):
        self.service = SSHService()

    def test_disconnect_none(self):
        self.service.disconnect(None)

    def test_disconnect_process(self):
        mock_process = MagicMock()

        with patch("src.services.ssh_service.kill_process") as mock_kill:
            self.service.disconnect(mock_process)

        mock_kill.assert_called_once_with(mock_process)


class TestGetState:
    def setup_method(self):
        self.service = SSHService()

    def test_none_process_disconnected(self):
        state = self.service.get_state(None)
        assert state == SSHState.DISCONNECTED

    def test_running_process_connected(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        state = self.service.get_state(mock_process)
        assert state == SSHState.CONNECTED

    def test_exited_process_disconnected(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = 1

        state = self.service.get_state(mock_process)
        assert state == SSHState.DISCONNECTED

    def test_state_is_string_constant(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        state = self.service.get_state(mock_process)
        assert state == SSHState.CONNECTED
        assert state == "connected"
