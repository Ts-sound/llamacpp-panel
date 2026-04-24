from unittest.mock import MagicMock, patch

import pytest

from src.models.errors import ProcessError
from src.models.monitor import MemoryStats
from src.models.restart_config import RestartConfig
from src.models.server_config import LaunchConfig, Parameter
from src.services.process_manager import ProcessManager


class TestStart:
    def test_start_success(self):
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.stdout = None
        mock_process.stderr = None

        manager = ProcessManager()
        config = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server -m model.gguf",
        )

        with patch("src.services.process_manager.popen_hidden", return_value=mock_process):
            result = manager.start(config)

        assert result is mock_process
        assert manager._current_process is mock_process

    def test_start_immediate_exit(self):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = MagicMock()
        mock_process.stderr.read.return_value = "error output"

        manager = ProcessManager()
        config = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server",
        )

        with patch("src.services.process_manager.popen_hidden", return_value=mock_process):
            with pytest.raises(ProcessError) as exc_info:
                manager.start(config)

        assert "exited immediately" in str(exc_info.value)
        assert exc_info.value.exit_code == 1
        assert exc_info.value.stderr == "error output"

    def test_start_file_not_found(self):
        manager = ProcessManager()
        config = LaunchConfig(
            server_path="/nonexistent",
            shell_command="/nonexistent",
        )

        with patch(
            "src.services.process_manager.popen_hidden",
            side_effect=FileNotFoundError("not found"),
        ):
            with pytest.raises(ProcessError) as exc_info:
                manager.start(config)
        assert "Failed to start process" in str(exc_info.value)

    def test_start_permission_error(self):
        manager = ProcessManager()
        config = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server",
        )

        with patch(
            "src.services.process_manager.popen_hidden",
            side_effect=PermissionError("denied"),
        ):
            with pytest.raises(ProcessError):
                manager.start(config)

    def test_start_with_callback(self):
        callback_calls = []

        def callback(msg, level):
            callback_calls.append((msg, level))

        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.stdout = None
        mock_process.stderr = None

        manager = ProcessManager(callback=callback)
        config = LaunchConfig(server_path="/s", shell_command="/s")

        with patch("src.services.process_manager.popen_hidden", return_value=mock_process):
            manager.start(config)

        assert len(callback_calls) == 1
        assert "Server started" in callback_calls[0][0]


class TestStop:
    def test_stop_current_process(self):
        mock_process = MagicMock()

        manager = ProcessManager()
        manager._current_process = mock_process

        with patch("src.services.process_manager.kill_process") as mock_kill:
            manager.stop()

        mock_kill.assert_called_once_with(mock_process, timeout=5)
        assert manager._current_process is None

    def test_stop_specific_process(self):
        mock_process = MagicMock()

        manager = ProcessManager()
        with patch("src.services.process_manager.kill_process") as mock_kill:
            manager.stop(mock_process)

        mock_kill.assert_called_once_with(mock_process, timeout=5)

    def test_stop_none(self):
        manager = ProcessManager()
        with patch("src.services.process_manager.kill_process") as mock_kill:
            manager.stop()
        mock_kill.assert_not_called()

    def test_stop_with_callback(self):
        callback_calls = []

        def callback(msg, level):
            callback_calls.append((msg, level))

        mock_process = MagicMock()
        manager = ProcessManager(callback=callback)
        manager._current_process = mock_process

        with patch("src.services.process_manager.kill_process"):
            manager.stop()

        assert any("Server stopped" in c[0] for c in callback_calls)


class TestIsRunning:
    def test_running_process(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        manager = ProcessManager()
        manager._current_process = mock_process

        assert manager.is_running() is True

    def test_exited_process(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = 0

        manager = ProcessManager()
        manager._current_process = mock_process

        assert manager.is_running() is False

    def test_none_process(self):
        manager = ProcessManager()
        assert manager.is_running() is False

    def test_specific_process(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        manager = ProcessManager()
        assert manager.is_running(mock_process) is True

    def test_specific_exited_process(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = 1

        manager = ProcessManager()
        assert manager.is_running(mock_process) is False


class TestAutoRestart:
    def test_enable_auto_restart(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        manager = ProcessManager()
        manager._current_process = mock_process

        config = LaunchConfig(server_path="/s", shell_command="/s")
        restart_cfg = RestartConfig(auto_restart=True)
        mock_monitor = MagicMock()

        manager.enable_auto_restart(config, restart_cfg, mock_monitor)
        assert manager._launch_config is config
        assert manager._restart_config is restart_cfg

        manager.disable_auto_restart()

    def test_disable_auto_restart(self):
        manager = ProcessManager()
        manager.disable_auto_restart()

    def test_auto_restart_process_exit(self):
        callback_calls = []

        def callback(msg, level):
            callback_calls.append((msg, level))

        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.poll.return_value = 1

        mock_new_process = MagicMock()
        mock_new_process.returncode = None
        mock_new_process.poll.return_value = None

        manager = ProcessManager(callback=callback)
        manager._current_process = mock_process

        config = LaunchConfig(server_path="/s", shell_command="/s")
        restart_cfg = RestartConfig(auto_restart=True, max_restarts=3, restart_interval=0)
        mock_monitor = MagicMock()

        with patch("src.services.process_manager.popen_hidden", return_value=mock_new_process):
            manager.enable_auto_restart(config, restart_cfg, mock_monitor)

            import time

            time.sleep(1.0)

            manager.disable_auto_restart()

        assert any("自动重启" in c[0] for c in callback_calls)

    def test_auto_restart_memory_threshold(self):
        callback_calls = []

        def callback(msg, level):
            callback_calls.append((msg, level))

        mock_process = MagicMock()
        mock_process.poll.return_value = None

        mock_new_process = MagicMock()
        mock_new_process.returncode = None
        mock_new_process.poll.return_value = None

        manager = ProcessManager(callback=callback)
        manager._current_process = mock_process

        config = LaunchConfig(server_path="/s", shell_command="/s")
        restart_cfg = RestartConfig(auto_restart=True, memory_threshold=80.0)

        mock_stats = MemoryStats(total=100, available=10, percent=90.0, used=90)

        from src.services.monitor_service import MonitorService

        mock_monitor = MagicMock(spec=MonitorService)
        mock_monitor.get_memory_stats.return_value = mock_stats

        with patch("src.services.process_manager.popen_hidden", return_value=mock_new_process), patch(
            "src.services.process_manager._POLL_INTERVAL", 0.2
        ):
            manager.enable_auto_restart(config, restart_cfg, mock_monitor)

            import time

            time.sleep(1.5)

            manager.disable_auto_restart()

        assert any("memory threshold" in c[0].lower() for c in callback_calls)

    def test_auto_restart_limit_reached(self):
        callback_calls = []

        def callback(msg, level):
            callback_calls.append((msg, level))

        mock_process = MagicMock()
        mock_process.poll.return_value = 1

        manager = ProcessManager(callback=callback)
        manager._current_process = mock_process

        config = LaunchConfig(server_path="/s", shell_command="/s")
        restart_cfg = RestartConfig(auto_restart=True, max_restarts=1, restart_interval=0)
        mock_monitor = MagicMock()

        with patch("src.services.process_manager._POLL_INTERVAL", 0.2):
            manager.enable_auto_restart(config, restart_cfg, mock_monitor)

            import time

            time.sleep(2.0)

            manager.disable_auto_restart()

        assert any("limit reached" in c[0].lower() for c in callback_calls)

    def test_auto_restart_disabled_on_crash(self):
        callback_calls = []

        def callback(msg, level):
            callback_calls.append((msg, level))

        mock_process = MagicMock()
        mock_process.poll.return_value = 1

        manager = ProcessManager(callback=callback)
        manager._current_process = mock_process

        config = LaunchConfig(server_path="/s", shell_command="/s")
        restart_cfg = RestartConfig(auto_restart=False)
        mock_monitor = MagicMock()

        manager.enable_auto_restart(config, restart_cfg, mock_monitor)

        import time

        time.sleep(0.5)

        manager.disable_auto_restart()

        assert any("auto-restart disabled" in c[0].lower() for c in callback_calls)
