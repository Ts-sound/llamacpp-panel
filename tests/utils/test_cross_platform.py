import sys
from unittest.mock import patch

import pytest

from src.utils.cross_platform import (
    get_cpu_count,
    get_platform,
    get_server_executable_name,
    kill_process,
)


class TestGetPlatform:
    def test_linux(self):
        with patch.object(sys, "platform", "linux"):
            assert get_platform() == "linux"

    def test_windows(self):
        with patch.object(sys, "platform", "win32"):
            assert get_platform() == "windows"

    def test_linux_with_version(self):
        with patch.object(sys, "platform", "linux2"):
            assert get_platform() == "linux"

    def test_returns_string(self):
        with patch.object(sys, "platform", "linux"):
            result = get_platform()
            assert isinstance(result, str)


class TestGetServerExecutableName:
    def test_linux(self):
        with patch("src.utils.cross_platform.get_platform", return_value="linux"):
            assert get_server_executable_name() == "server"

    def test_windows(self):
        with patch("src.utils.cross_platform.get_platform", return_value="windows"):
            assert get_server_executable_name() == "server.exe"


class TestKillProcess:
    def test_none_process(self):
        kill_process(None)

    def test_linux_terminate(self):
        mock_proc = MagicMock()
        mock_proc.wait.side_effect = [TimeoutError(), None]

        with patch("src.utils.cross_platform.get_platform", return_value="linux"):
            kill_process(mock_proc)

        mock_proc.terminate.assert_called_once()

    def test_linux_fallback_to_kill(self):
        mock_proc = MagicMock()
        mock_proc.wait.side_effect = [TimeoutError(), None]

        with patch("src.utils.cross_platform.get_platform", return_value="linux"):
            kill_process(mock_proc, timeout=0)

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()

    def test_linux_exception_ignored(self):
        mock_proc = MagicMock()
        mock_proc.terminate.side_effect = Exception("fail")

        with patch("src.utils.cross_platform.get_platform", return_value="linux"):
            kill_process(mock_proc)

    def test_windows_terminate(self):
        mock_proc = MagicMock()

        with patch("src.utils.cross_platform.get_platform", return_value="windows"):
            kill_process(mock_proc)

        mock_proc.terminate.assert_called_once()


class TestGetCpuCount:
    def test_returns_int(self):
        result = get_cpu_count()
        assert isinstance(result, int)
        assert result > 0

    def test_default_on_none(self):
        with patch("os.cpu_count", return_value=None):
            assert get_cpu_count() == 4

    def test_default_on_zero(self):
        with patch("os.cpu_count", return_value=0):
            assert get_cpu_count() == 4

    def test_actual_count(self):
        with patch("os.cpu_count", return_value=8):
            assert get_cpu_count() == 8

    def test_exception_fallback(self):
        with patch("os.cpu_count", side_effect=Exception("fail")):
            assert get_cpu_count() == 4


from unittest.mock import MagicMock
