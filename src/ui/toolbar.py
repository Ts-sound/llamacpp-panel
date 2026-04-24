"""Toolbar widget with memory/GPU bars, control buttons, and auto-restart toggle."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from src.config import MEMORY_DANGER_THRESHOLD, MEMORY_WARNING_THRESHOLD
from src.models.monitor import GPUStats, MemoryStats

_BUTTON_STATES: dict[str, dict[str, bool]] = {
    "stopped":  {"start": True,  "stop": False, "restart": False},
    "running":  {"start": False, "stop": True,  "restart": True},
    "starting": {"start": False, "stop": True,  "restart": False},
    "crashed":  {"start": True,  "stop": False, "restart": True},
}


class _MemoryBar(ttk.Frame):
    """Memory usage bar with label and progress indicator."""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        self.lbl = ttk.Label(self, text="MEM: --% / --G", width=18)
        self.lbl.pack(side=tk.LEFT)
        self.bar = ttk.Progressbar(
            self, orient=tk.HORIZONTAL, length=140, mode="determinate"
        )
        self.bar.pack(side=tk.LEFT, padx=(4, 0))

    def update(self, stats: MemoryStats) -> None:
        total_gb = stats.total / (1024 ** 3)
        self.lbl.configure(text=f"MEM: {stats.percent:.0f}% / {total_gb:.0f}G")
        self.bar.configure(value=stats.percent)


class _GPUBbar(ttk.Frame):
    """GPU usage bar, initially hidden until GPU stats arrive."""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        self.lbl = ttk.Label(self, text="GPU: --% / --G", width=18)
        self.lbl.pack(side=tk.LEFT)
        self.bar = ttk.Progressbar(
            self, orient=tk.HORIZONTAL, length=120, mode="determinate"
        )
        self.bar.pack(side=tk.LEFT, padx=(4, 0))

    def show(self) -> None:
        self.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)

    def hide(self) -> None:
        self.pack_forget()

    def update(self, stats: GPUStats) -> None:
        if stats.total is not None and stats.used is not None:
            total_gb = stats.total / (1024 ** 3)
            self.lbl.configure(text=f"GPU: {stats.percent:.0f}% / {total_gb:.0f}G")
        if stats.percent is not None:
            self.bar.configure(value=stats.percent)


class _ControlButtons(ttk.Frame):
    """Start / Stop / Restart buttons with state management."""

    def __init__(
        self,
        master: tk.Widget,
        *,
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_restart: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.btn_start = ttk.Button(self, text="Start", width=8)
        self.btn_stop = ttk.Button(self, text="Stop", width=8)
        self.btn_restart = ttk.Button(self, text="Restart", width=8)
        self.btn_start.pack(side=tk.LEFT, padx=2)
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

        self.btn_start.configure(command=on_start)
        self.btn_stop.configure(command=on_stop)
        self.btn_restart.configure(command=on_restart)

    def set_state(self, state: str) -> None:
        flags = _BUTTON_STATES.get(state, {})
        self.btn_start.configure(state=flags.get("start", False))
        self.btn_stop.configure(state=flags.get("stop", False))
        self.btn_restart.configure(state=flags.get("restart", False))


class _AutoRestartToggle(ttk.Frame):
    """Auto-restart checkbox."""

    def __init__(
        self,
        master: tk.Widget,
        on_toggled: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.var = tk.BooleanVar(value=False)
        self.cb = ttk.Checkbutton(
            self, text="Auto Restart", variable=self.var, command=lambda: None
        )
        self.cb.pack(side=tk.LEFT)
        self._on_toggled = on_toggled

    def set_command(self, on_toggled: Callable[[bool], None]) -> None:
        self._on_toggled = on_toggled

    def on_toggle(self) -> None:
        if self._on_toggled:
            self._on_toggled(self.var.get())


class Toolbar(ttk.Frame):
    """Top toolbar: resource bars + control buttons + auto-restart toggle."""

    def __init__(
        self,
        master: tk.Widget,
        *,
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_restart: Callable[[], None] | None = None,
        on_auto_restart: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(master, height=50)
        self.pack_propagate(False)

        self._register_styles()

        self.memory_bar = _MemoryBar(self)
        self.memory_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)

        self.gpu_bar = _GPUBbar(self)

        self.control_buttons = _ControlButtons(
            self, on_start=on_start, on_stop=on_stop, on_restart=on_restart
        )
        self.control_buttons.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)

        self.auto_restart = _AutoRestartToggle(self, on_toggled=on_auto_restart)
        self.auto_restart.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)

        self.auto_restart.cb.configure(command=self.auto_restart.on_toggle)

    # -- style registration --

    @staticmethod
    def _register_styles() -> None:
        style = ttk.Style()
        style.configure(
            "Normal.Horizontal.TProgressbar",
            troughcolor="#E0E0E0",
            background="#4CAF50",
        )
        style.configure(
            "Warning.Horizontal.TProgressbar",
            troughcolor="#E0E0E0",
            background="#FF9800",
        )
        style.configure(
            "Danger.Horizontal.TProgressbar",
            troughcolor="#E0E0E0",
            background="#F44336",
        )

    # -- public API --

    def update_memory_display(self, stats: MemoryStats) -> None:
        """Update memory bar text and colour based on thresholds."""
        self.memory_bar.update(stats)
        bar_style: str
        if stats.percent >= MEMORY_DANGER_THRESHOLD:
            bar_style = "Danger.Horizontal.TProgressbar"
        elif stats.percent >= MEMORY_WARNING_THRESHOLD:
            bar_style = "Warning.Horizontal.TProgressbar"
        else:
            bar_style = "Normal.Horizontal.TProgressbar"
        self.memory_bar.bar.configure(style=bar_style)

    def update_gpu_display(self, stats: GPUStats | None) -> None:
        """Show/hide GPU bar and update values."""
        if stats is None:
            self.gpu_bar.hide()
            return
        self.gpu_bar.show()
        self.gpu_bar.update(stats)

    def set_button_state(self, state: str) -> None:
        """Set button enabled/disabled state from the state table."""
        self.control_buttons.set_state(state)
