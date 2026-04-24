from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MemoryStats:
    total: int
    available: int
    percent: float
    used: int


@dataclass
class GPUStats:
    total: int | None = None
    used: int | None = None
    percent: float | None = None
