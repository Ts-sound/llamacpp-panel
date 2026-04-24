"""Toolbar widget with status bars, control buttons, and configuration."""

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

_SERVER_COLORS: dict[str, str] = {
    "stopped": "#888888",
    "running": "#00CC00",
    "starting": "#FFA500",
    "crashed": "#CC0000",
}

_SSH_COLORS: dict[str, str] = {
    "disconnected": "#888888",
    "connecting": "#FFA500",
    "connected": "#00CC00",
}


class _StatusIndicator(ttk.Frame):
    """Status indicator with label, circle, and optional progress bar."""

    def __init__(
        self,
        master: tk.Widget,
        label: str,
        show_bar: bool = True,
        bar_length: int = 120,
    ) -> None:
        super().__init__(master)
        
        self._label_text = label
        self.lbl = ttk.Label(self, text=f"{label}: N/A", width=16)
        self.lbl.pack(side=tk.LEFT)
        
        self._indicator = tk.Canvas(self, width=12, height=12, highlightthickness=0)
        self._indicator.pack(side=tk.LEFT, padx=(4, 0))
        
        if show_bar:
            self.bar = ttk.Progressbar(
                self, orient=tk.HORIZONTAL, length=bar_length, mode="determinate"
            )
            self.bar.pack(side=tk.LEFT, padx=(4, 0))
        else:
            self.bar = None
        
        self._draw_circle("#888888")

    def _draw_circle(self, color: str) -> None:
        self._indicator.delete("all")
        self._indicator.create_oval(1, 1, 11, 11, fill=color, outline="")

    def update_status(self, status: str, text: str | None = None) -> None:
        color = _SERVER_COLORS.get(status, "#888888")
        self._draw_circle(color)
        if text:
            self.lbl.configure(text=f"{self._label_text}: {text}")
        else:
            self.lbl.configure(text=f"{self._label_text}: {status}")

    def update_bar(self, value: float, style: str = "Normal.Horizontal.TProgressbar") -> None:
        if self.bar:
            self.bar.configure(value=value, style=style)

    def update_text(self, text: str) -> None:
        self.lbl.configure(text=f"{self._label_text}: {text}")


class _SSHIndicator(ttk.Frame):
    """SSH status indicator."""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        
        self.lbl = ttk.Label(self, text="SSH: 未连接", width=12)
        self.lbl.pack(side=tk.LEFT)
        
        self._indicator = tk.Canvas(self, width=12, height=12, highlightthickness=0)
        self._indicator.pack(side=tk.LEFT, padx=(4, 0))
        
        self._draw_circle("disconnected")

    def _draw_circle(self, status: str) -> None:
        self._indicator.delete("all")
        color = _SSH_COLORS.get(status, "#888888")
        self._indicator.create_oval(1, 1, 11, 11, fill=color, outline="")

    def update_status(self, status: str) -> None:
        self._draw_circle(status)
        labels = {
            "disconnected": "未连接",
            "connecting": "连接中",
            "connected": "已连接",
        }
        self.lbl.configure(text=f"SSH: {labels.get(status, status)}")


class _ControlButtons(ttk.Frame):
    """Start / Stop / Restart buttons."""

    def __init__(
        self,
        master: tk.Widget,
        *,
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_restart: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        
        self.btn_start = ttk.Button(self, text="启动", width=8)
        self.btn_stop = ttk.Button(self, text="停止", width=8)
        self.btn_restart = ttk.Button(self, text="重启", width=8)
        
        self.btn_start.pack(side=tk.LEFT, padx=2)
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        self.btn_restart.pack(side=tk.LEFT, padx=2)

        if on_start:
            self.btn_start.configure(command=on_start)
        if on_stop:
            self.btn_stop.configure(command=on_stop)
        if on_restart:
            self.btn_restart.configure(command=on_restart)

    def set_state(self, state: str) -> None:
        flags = _BUTTON_STATES.get(state, {})
        self.btn_start.configure(state="normal" if flags.get("start", False) else "disabled")
        self.btn_stop.configure(state="normal" if flags.get("stop", False) else "disabled")
        self.btn_restart.configure(state="normal" if flags.get("restart", False) else "disabled")


class _AutoRestartConfig(ttk.Frame):
    """Auto-restart toggle with configurable parameters."""

    def __init__(
        self,
        master: tk.Widget,
        on_toggled: Callable[[bool], None] | None = None,
        on_config_changed: Callable[[int, float, float], None] | None = None,
    ) -> None:
        super().__init__(master)
        
        self._on_toggled = on_toggled
        self._on_config_changed = on_config_changed
        
        self.var = tk.BooleanVar(value=False)
        self.cb = ttk.Checkbutton(
            self, text="自动重启", variable=self.var, command=self._on_toggle
        )
        self.cb.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(self, text="次数:").pack(side=tk.LEFT)
        self.max_restarts_var = tk.StringVar(value="3")
        self.max_restarts_entry = ttk.Entry(self, textvariable=self.max_restarts_var, width=4)
        self.max_restarts_entry.pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(self, text="间隔:").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value="5")
        self.interval_entry = ttk.Entry(self, textvariable=self.interval_var, width=4)
        self.interval_entry.pack(side=tk.LEFT, padx=(2, 5))
        ttk.Label(self, text="秒").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(self, text="内存:").pack(side=tk.LEFT)
        self.threshold_var = tk.StringVar(value="90")
        self.threshold_entry = ttk.Entry(self, textvariable=self.threshold_var, width=4)
        self.threshold_entry.pack(side=tk.LEFT, padx=(2, 5))
        ttk.Label(self, text="%").pack(side=tk.LEFT)
        
        self.max_restarts_entry.bind("<Return>", self._on_config_change)
        self.interval_entry.bind("<Return>", self._on_config_change)
        self.threshold_entry.bind("<Return>", self._on_config_change)
        self.max_restarts_entry.bind("<FocusOut>", self._on_config_change)
        self.interval_entry.bind("<FocusOut>", self._on_config_change)
        self.threshold_entry.bind("<FocusOut>", self._on_config_change)

    def _on_toggle(self) -> None:
        if self._on_toggled:
            self._on_toggled(self.var.get())

    def _on_config_change(self, event: object = None) -> None:
        if self._on_config_changed:
            try:
                max_restarts = int(self.max_restarts_var.get())
                interval = float(self.interval_var.get())
                threshold = float(self.threshold_var.get())
                self._on_config_changed(max_restarts, interval, threshold)
            except ValueError:
                pass

    def get_config(self) -> tuple[int, float, float]:
        try:
            return (
                int(self.max_restarts_var.get()),
                float(self.interval_var.get()),
                float(self.threshold_var.get()),
            )
        except ValueError:
            return (3, 5.0, 90.0)

    def set_config(self, max_restarts: int, interval: float, threshold: float) -> None:
        self.max_restarts_var.set(str(max_restarts))
        self.interval_var.set(str(interval))
        self.threshold_var.set(str(threshold))


class _AutoStartSSH(ttk.Frame):
    """Checkbox to auto-start SSH tunnel when server is ready."""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        
        self.var = tk.BooleanVar(value=False)
        self.cb = ttk.Checkbutton(
            self, text="同时启动SSH", variable=self.var
        )
        self.cb.pack(side=tk.LEFT)

    def is_enabled(self) -> bool:
        return self.var.get()


class Toolbar(ttk.Frame):
    """Top toolbar with status bars, controls, and configuration."""

    def __init__(
        self,
        master: tk.Widget,
        *,
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_restart: Callable[[], None] | None = None,
        on_auto_restart: Callable[[bool], None] | None = None,
        on_auto_restart_config: Callable[[int, float, float], None] | None = None,
    ) -> None:
        super().__init__(master, height=80)
        self.pack_propagate(False)
        
        self._register_styles()
        
        for i in range(5):
            self.columnconfigure(i, weight=1 if i < 4 else 0)
        
        self._build_status_row()
        self._build_config_row(on_start, on_stop, on_restart, on_auto_restart, on_auto_restart_config)

    def _build_status_row(self) -> None:
        row = 0
        
        self.memory_indicator = _StatusIndicator(self, "MEM", show_bar=True, bar_length=100)
        self.memory_indicator.grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.gpu_indicator = _StatusIndicator(self, "GPU", show_bar=True, bar_length=100)
        self.gpu_indicator.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        self.server_indicator = _StatusIndicator(self, "SERVER", show_bar=False)
        self.server_indicator.grid(row=row, column=2, sticky=tk.W, padx=10, pady=5)
        
        self.ssh_indicator = _SSHIndicator(self)
        self.ssh_indicator.grid(row=row, column=3, sticky=tk.W, padx=10, pady=5)
        
        self.auto_start_ssh = _AutoStartSSH(self)
        self.auto_start_ssh.grid(row=row, column=4, sticky=tk.E, padx=10, pady=5)

    def _build_config_row(
        self,
        on_start: Callable[[], None] | None,
        on_stop: Callable[[], None] | None,
        on_restart: Callable[[], None] | None,
        on_auto_restart: Callable[[bool], None] | None,
        on_auto_restart_config: Callable[[int, float, float], None] | None,
    ) -> None:
        row = 1
        
        self.control_buttons = _ControlButtons(
            self, on_start=on_start, on_stop=on_stop, on_restart=on_restart
        )
        self.control_buttons.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        
        self.auto_restart_config = _AutoRestartConfig(
            self, on_toggled=on_auto_restart, on_config_changed=on_auto_restart_config
        )
        self.auto_restart_config.grid(row=row, column=2, columnspan=3, sticky=tk.E, padx=10, pady=5)

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

    def update_memory_display(self, stats: MemoryStats) -> None:
        total_gb = stats.total / (1024 ** 3)
        self.memory_indicator.update_text(f"{stats.percent:.0f}% / {total_gb:.0f}G")
        self.memory_indicator.bar.configure(value=stats.percent)
        
        if stats.percent >= MEMORY_DANGER_THRESHOLD:
            style = "Danger.Horizontal.TProgressbar"
        elif stats.percent >= MEMORY_WARNING_THRESHOLD:
            style = "Warning.Horizontal.TProgressbar"
        else:
            style = "Normal.Horizontal.TProgressbar"
        self.memory_indicator.bar.configure(style=style)

    def update_gpu_display(self, stats: GPUStats | None) -> None:
        if stats is None:
            self.gpu_indicator.update_text("N/A")
            self.gpu_indicator.bar.configure(value=0)
            return
        if stats.total is not None and stats.used is not None:
            total_gb = stats.total / (1024 ** 3)
            self.gpu_indicator.update_text(f"{stats.percent:.0f}% / {total_gb:.0f}G")
        if stats.percent is not None:
            self.gpu_indicator.bar.configure(value=stats.percent)

    def update_server_status(self, status: str) -> None:
        labels = {
            "stopped": "已停止",
            "running": "运行中",
            "starting": "启动中",
            "crashed": "已崩溃",
        }
        self.server_indicator.update_status(status, labels.get(status))

    def update_ssh_status(self, status: str) -> None:
        self.ssh_indicator.update_status(status)

    def set_button_state(self, state: str) -> None:
        self.control_buttons.set_state(state)
        self.update_server_status(state)

    def set_auto_restart_config(self, max_restarts: int, interval: float, threshold: float) -> None:
        self.auto_restart_config.set_config(max_restarts, interval, threshold)

    def get_auto_start_ssh(self) -> bool:
        return self.auto_start_ssh.is_enabled()