"""Log panel widget for displaying timestamped, color-coded log messages."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from src.config import LOG_KEEP_LINES, MAX_LOG_LINES


class LogPanel(tk.Frame):
    """运行日志面板 - 显示带时间戳和颜色标记的运行日志."""

    COLORS: dict[str, str] = {
        "INFO": "#000000",
        "WARN": "#CC6600",
        "ERROR": "#CC0000",
        "SYSTEM": "#0066CC",
    }

    def __init__(self, parent: tk.Widget | None = None, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)

        self._header_frame = ttk.Frame(self)
        self._header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        self._lbl_title = ttk.Label(
            self._header_frame, text="运行日志", font=("", 10, "bold")
        )
        self._lbl_title.pack(side=tk.LEFT)

        self._btn_toggle = ttk.Button(
            self._header_frame, text="折叠", width=6, command=self.toggle_visibility
        )
        self._btn_toggle.pack(side=tk.RIGHT)

        self._content_frame = ttk.Frame(self)

        self._txt_log = ScrolledText(
            self._content_frame,
            height=10,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Courier", 9),
        )
        self._txt_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        for level, color in self.COLORS.items():
            self._txt_log.tag_configure(level.lower(), foreground=color)

        self._content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

    def log(self, message: str, level: str = "INFO") -> None:
        """追加一条带时间戳的日志，自动滚动，超过上限时自动清理."""
        tag = level.lower()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {message}\n"

        self._txt_log.configure(state=tk.NORMAL)
        self._txt_log.insert(tk.END, line, tag)
        self._txt_log.see(tk.END)
        self._txt_log.configure(state=tk.DISABLED)

        if int(self._txt_log.index(tk.END + "-1c").split(".")[0]) > MAX_LOG_LINES:
            self._cleanup()

    def _cleanup(self) -> None:
        """移除旧日志，保留最近的 LOG_KEEP_LINES 行."""
        self._txt_log.configure(state=tk.NORMAL)
        self._txt_log.delete("1.0", f"{LOG_KEEP_LINES}.0")
        self._txt_log.configure(state=tk.DISABLED)

    def toggle_visibility(self) -> None:
        """折叠/展开日志内容区域."""
        if self._content_frame.winfo_ismapped():
            self._content_frame.pack_forget()
            self._btn_toggle.config(text="展开")
        else:
            self._content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
            self._btn_toggle.config(text="折叠")

    def clear(self) -> None:
        """清空所有日志内容."""
        self._txt_log.configure(state=tk.NORMAL)
        self._txt_log.delete("1.0", tk.END)
        self._txt_log.configure(state=tk.DISABLED)
