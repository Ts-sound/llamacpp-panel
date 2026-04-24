from unittest.mock import MagicMock, patch

import pytest

from src.models.monitor import GPUStats, MemoryStats
from src.services.monitor_service import MonitorService


class TestGetMemoryStats:
    def test_returns_memory_stats(self):
        mock_mem = MagicMock()
        mock_mem.total = 16000000000
        mock_mem.available = 8000000000
        mock_mem.percent = 50.0
        mock_mem.used = 8000000000

        svc = MonitorService()
        with patch("src.services.monitor_service.psutil.virtual_memory", return_value=mock_mem):
            stats = svc.get_memory_stats()

        assert isinstance(stats, MemoryStats)
        assert stats.total == 16000000000
        assert stats.available == 8000000000
        assert stats.percent == 50.0
        assert stats.used == 8000000000

    def test_full_memory(self):
        mock_mem = MagicMock()
        mock_mem.total = 1000
        mock_mem.available = 0
        mock_mem.percent = 100.0
        mock_mem.used = 1000

        svc = MonitorService()
        with patch("src.services.monitor_service.psutil.virtual_memory", return_value=mock_mem):
            stats = svc.get_memory_stats()

        assert stats.percent == 100.0
        assert stats.available == 0

    def test_low_memory(self):
        mock_mem = MagicMock()
        mock_mem.total = 1000
        mock_mem.available = 990
        mock_mem.percent = 1.0
        mock_mem.used = 10

        svc = MonitorService()
        with patch("src.services.monitor_service.psutil.virtual_memory", return_value=mock_mem):
            stats = svc.get_memory_stats()

        assert stats.percent == 1.0


class TestGetGpuStats:
    def test_successful_gpu_query(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "8192, 4096\n"

        svc = MonitorService()
        with patch("src.services.monitor_service.subprocess.run", return_value=mock_result):
            stats = svc.get_gpu_stats()

        assert isinstance(stats, GPUStats)
        assert stats.total == 8192 * 1024 * 1024
        assert stats.used == 4096 * 1024 * 1024
        assert stats.percent == 50.0

    def test_gpu_command_failure(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        svc = MonitorService()
        with patch("src.services.monitor_service.subprocess.run", return_value=mock_result):
            stats = svc.get_gpu_stats()

        assert stats is None

    def test_gpu_empty_output(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  \n"

        svc = MonitorService()
        with patch("src.services.monitor_service.subprocess.run", return_value=mock_result):
            stats = svc.get_gpu_stats()

        assert stats is None

    def test_gpu_not_found(self):
        svc = MonitorService()
        with patch(
            "src.services.monitor_service.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            stats = svc.get_gpu_stats()
        assert stats is None

    def test_gpu_timeout(self):
        svc = MonitorService()
        import subprocess

        with patch(
            "src.services.monitor_service.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=5),
        ):
            stats = svc.get_gpu_stats()
        assert stats is None

    def test_gpu_invalid_output(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not,a,number\n"

        svc = MonitorService()
        with patch("src.services.monitor_service.subprocess.run", return_value=mock_result):
            stats = svc.get_gpu_stats()
        assert stats is None

    def test_gpu_zero_total(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "0, 0\n"

        svc = MonitorService()
        with patch("src.services.monitor_service.subprocess.run", return_value=mock_result):
            stats = svc.get_gpu_stats()

        assert stats is not None
        assert stats.total == 0
        assert stats.percent == 0.0


class TestMonitoringLifecycle:
    def test_start_stop_monitoring(self):
        callback_called = []

        def callback(stats, gpu_stats):
            callback_called.append(stats)

        mock_mem = MagicMock()
        mock_mem.total = 1000
        mock_mem.available = 500
        mock_mem.percent = 50.0
        mock_mem.used = 500

        svc = MonitorService()
        with (
            patch("src.services.monitor_service.psutil.virtual_memory", return_value=mock_mem),
            patch.object(svc, "get_gpu_stats", return_value=None),
        ):
            svc.start_monitoring(interval=0.1, callback=callback)
            import time

            time.sleep(0.3)
            svc.stop_monitoring()

        assert len(callback_called) > 0
        assert isinstance(callback_called[0], MemoryStats)

    def test_callback_parameter_in_constructor(self):
        called = []

        def cb(stats, gpu_stats):
            called.append(stats)

        mock_mem = MagicMock()
        mock_mem.total = 100
        mock_mem.available = 50
        mock_mem.percent = 50.0
        mock_mem.used = 50

        svc = MonitorService(callback=cb)
        with (
            patch("src.services.monitor_service.psutil.virtual_memory", return_value=mock_mem),
            patch.object(svc, "get_gpu_stats", return_value=None),
        ):
            svc.start_monitoring(interval=0.1)
            import time

            time.sleep(0.3)
            svc.stop_monitoring()

        assert len(called) > 0

    def test_stop_without_start(self):
        svc = MonitorService()
        svc.stop_monitoring()

    def test_double_start(self):
        mock_mem = MagicMock()
        mock_mem.total = 100
        mock_mem.available = 50
        mock_mem.percent = 50.0
        mock_mem.used = 50

        svc = MonitorService()
        with patch("src.services.monitor_service.psutil.virtual_memory", return_value=mock_mem):
            svc.start_monitoring(interval=0.5)
            svc.start_monitoring(interval=0.5)
            svc.stop_monitoring()
