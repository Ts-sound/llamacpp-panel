from __future__ import annotations

import threading
from typing import Callable

import psutil

from src.models.monitor import GPUStats, MemoryStats
from src.utils.cross_platform import run_hidden


class MonitorService:
    def __init__(self, callback: Callable[[MemoryStats, GPUStats | None], None] | None = None) -> None:
        self._callback = callback
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def get_memory_stats(self) -> MemoryStats:
        mem = psutil.virtual_memory()
        return MemoryStats(
            total=mem.total,
            available=mem.available,
            percent=mem.percent,
            used=mem.used,
        )

    def get_gpu_stats(self) -> GPUStats | None:
        try:
            result = run_hidden(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total,memory.used",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return None

            line = result.stdout.strip()
            if not line:
                return None

            parts = [p.strip() for p in line.split(",")]
            total_mib = int(parts[0])
            used_mib = int(parts[1])

            return GPUStats(
                total=total_mib * 1024 * 1024,
                used=used_mib * 1024 * 1024,
                percent=(used_mib / total_mib * 100.0) if total_mib > 0 else 0.0,
            )
        except (FileNotFoundError, TimeoutError, ValueError, IndexError):
            return None

    def start_monitoring(
        self, interval: float = 3.0, callback: Callable[[MemoryStats, GPUStats | None], None] | None = None
    ) -> None:
        if callback is not None:
            self._callback = callback

        self._stop_event.clear()

        if self._thread is not None and self._thread.is_alive():
            return

        self._thread = threading.Thread(
            target=self._monitor_loop, args=(interval,), daemon=True
        )
        self._thread.start()

    def stop_monitoring(self) -> None:
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5.0)

    def _monitor_loop(self, interval: float) -> None:
        while not self._stop_event.is_set():
            try:
                stats = self.get_memory_stats()
                gpu_stats = self.get_gpu_stats()
                if self._callback is not None:
                    self._callback(stats, gpu_stats)
            except Exception:
                pass
            self._stop_event.wait(timeout=interval)
