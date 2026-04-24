"""Shared pytest fixtures for llamacpp-panel tests."""

import sys
import tempfile
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# Mock tkinter for headless environments
if "tkinter" not in sys.modules:
    tkinter_mock = ModuleType("tkinter")
    tkinter_mock.filedialog = MagicMock()
    tkinter_mock.Misc = MagicMock

    filedialog_mock = ModuleType("tkinter.filedialog")
    filedialog_mock.askopenfilename = MagicMock()
    filedialog_mock.askdirectory = MagicMock()
    filedialog_mock.asksaveasfilename = MagicMock()
    sys.modules["tkinter.filedialog"] = filedialog_mock

    sys.modules["tkinter"] = tkinter_mock

from src.models.monitor import GPUStats, MemoryStats
from src.models.restart_config import RestartConfig, RestartLogEntry
from src.models.server_config import HistoryEntry, LaunchConfig, Parameter
from src.models.ssh_config import SSHConfig


@pytest.fixture
def sample_parameter():
    """A basic Parameter instance."""
    return Parameter(
        name="-m",
        category="基础",
        required=True,
        value="model.gguf",
        description="模型文件路径",
    )


@pytest.fixture
def sample_parameters():
    """A list of Parameter instances for a full config."""
    return [
        Parameter(name="-m", category="基础", required=True, value="model.gguf"),
        Parameter(name="-c", category="基础", required=False, value="4096"),
        Parameter(name="-ngl", category="GPU", required=False, value="99"),
        Parameter(name="--threads", category="性能", required=False, value="4"),
        Parameter(name="--host", category="网络", required=False, value="127.0.0.1"),
        Parameter(name="--port", category="网络", required=False, value="8080"),
    ]


@pytest.fixture
def sample_launch_config(sample_parameters):
    """A complete LaunchConfig instance."""
    return LaunchConfig(
        server_path="/usr/bin/server",
        shell_command="/usr/bin/server -m model.gguf -c 4096",
        parameters=sample_parameters,
        selected_template="全功能",
    )


@pytest.fixture
def minimal_launch_config():
    """A minimal LaunchConfig with no parameters."""
    return LaunchConfig(
        server_path="/usr/bin/server",
        shell_command="/usr/bin/server",
    )


@pytest.fixture
def sample_restart_config():
    """A RestartConfig with custom values."""
    return RestartConfig(
        auto_restart=True,
        max_restarts=5,
        memory_threshold=80.0,
        restart_count=1,
    )


@pytest.fixture
def default_restart_config():
    """A RestartConfig with all defaults."""
    return RestartConfig()


@pytest.fixture
def sample_ssh_config():
    """A SSHConfig instance."""
    return SSHConfig(
        local_port=8080,
        remote_port=8080,
        remote_host="172.18.122.71",
        username="root",
        enabled=True,
    )


@pytest.fixture
def default_ssh_config():
    """A SSHConfig with enabled=False."""
    return SSHConfig(
        local_port=8080,
        remote_port=8080,
        remote_host="172.18.122.71",
        username="root",
    )


@pytest.fixture
def sample_history_entry():
    """A HistoryEntry instance."""
    return HistoryEntry(
        server_path="/usr/bin/server",
        last_used="2024-01-01T12:00:00",
    )


@pytest.fixture
def sample_memory_stats():
    """A MemoryStats instance representing 50% usage."""
    return MemoryStats(
        total=16000000000,
        available=8000000000,
        percent=50.0,
        used=8000000000,
    )


@pytest.fixture
def sample_gpu_stats():
    """A GPUStats instance representing 50% usage."""
    return GPUStats(
        total=8589934592,
        used=4294967296,
        percent=50.0,
    )


@pytest.fixture
def sample_restart_log_entry():
    """A RestartLogEntry instance."""
    return RestartLogEntry(
        timestamp="2024-01-01T12:00:00",
        reason="memory threshold exceeded",
        exit_code=1,
    )


@pytest.fixture
def temp_config_file(tmp_path):
    """A temporary config file path."""
    return str(tmp_path / "test_config.json")


@pytest.fixture
def mock_process():
    """A MagicMock representing a subprocess Popen."""
    proc = MagicMock()
    proc.returncode = None
    proc.poll.return_value = None
    proc.pid = 12345
    proc.stdout = None
    proc.stderr = None
    return proc


@pytest.fixture
def mock_monitor_service(sample_memory_stats):
    """A MagicMock representing a MonitorService."""
    svc = MagicMock()
    svc.get_memory_stats.return_value = sample_memory_stats
    svc.get_gpu_stats.return_value = sample_gpu_stats
    return svc
