"""SSH tunnel configuration panel for llamacpp-panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from src.config import (
    SSH_LOCAL_PORT,
    SSH_PORT,
    SSH_REMOTE_HOST,
    SSH_REMOTE_PORT,
    SSH_USERNAME,
)
from src.models.ssh_config import SSHConfig, SSHState
from src.services.ssh_service import SSHService


class SSHPanel(tk.Frame):
    def __init__(
        self,
        master: tk.Master | None,
        ssh_service: SSHService,
        on_connect: Callable[[SSHConfig], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self._service = ssh_service
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect

        self._local_port_var = tk.StringVar(value=str(SSH_LOCAL_PORT))
        self._remote_port_var = tk.StringVar(value=str(SSH_REMOTE_PORT))
        self._remote_host_var = tk.StringVar(value=SSH_REMOTE_HOST)
        self._username_var = tk.StringVar(value=SSH_USERNAME)
        self._ssh_port_var = tk.StringVar(value=str(SSH_PORT))
        self._key_file_var = tk.StringVar(value="")

        self._state = SSHState.DISCONNECTED
        self._indicator: tk.Canvas | None = None
        self._btn_connect: ttk.Button | None = None
        self._btn_disconnect: ttk.Button | None = None
        self._full_ssh_cmd: str = ""

        self._build_ui()

    def _build_ui(self) -> None:
        for i in range(4):
            self.columnconfigure(i, weight=1)

        self._build_config_grid()
        self._build_status_row()
        self._build_buttons()
        self._build_command_preview()

    def _build_config_grid(self) -> None:
        labels = [
            ("本地端口:", 0),
            ("远程端口:", 0),
            ("SSH端口:", 0),
            ("远程IP:", 2),
            ("用户名:", 2),
            ("密钥:", 2),
        ]
        vars_list = [
            self._local_port_var,
            self._remote_port_var,
            self._ssh_port_var,
            self._remote_host_var,
            self._username_var,
            self._key_file_var,
        ]

        row = 0
        for label_text, col_offset in labels:
            ttk.Label(self, text=label_text).grid(
                row=row, column=col_offset, sticky=tk.W, padx=5, pady=3,
            )
            if label_text == "密钥:":
                entry = ttk.Entry(self, textvariable=vars_list[row], width=18)
                btn_browse = ttk.Button(
                    self, text="浏览", width=4,
                    command=lambda: self._browse_key_file(entry),
                )
                entry.grid(row=row, column=col_offset + 1, sticky=tk.W, padx=5, pady=3)
                btn_browse.grid(row=row, column=col_offset + 2, sticky=tk.W, padx=5, pady=3)
            else:
                entry = ttk.Entry(self, textvariable=vars_list[row], width=18)
                entry.grid(row=row, column=col_offset + 1, sticky=tk.W, padx=5, pady=3)
            row += 1

    def _browse_key_file(self, entry: ttk.Entry) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(parent=self, title="Select SSH Key File")
        if path:
            from src.utils.file_utils import normalize_path
            entry.delete(0, tk.END)
            entry.insert(0, normalize_path(path))

    def _build_status_row(self) -> None:
        row = 6
        self._indicator = tk.Canvas(
            self, width=12, height=12, highlightthickness=0,
        )
        self._indicator.grid(row=row, column=0, padx=5, pady=3, sticky=tk.W)
        self._draw_circle(SSHState.DISCONNECTED)

    def _build_buttons(self) -> None:
        row = 7
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=5)

        self._btn_connect = ttk.Button(
            btn_frame, text="连接", command=self._on_connect_clicked,
        )
        self._btn_connect.pack(side=tk.LEFT, padx=5)

        self._btn_disconnect = ttk.Button(
            btn_frame, text="断开", command=self._on_disconnect_clicked,
            state=tk.DISABLED,
        )
        self._btn_disconnect.pack(side=tk.LEFT, padx=5)

    def _build_command_preview(self) -> None:
        row = 8
        ttk.Label(self, text="命令:").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=3)
        self._cmd_preview = ttk.Label(self, text="", foreground="#555", wraplength=400)
        self._cmd_preview.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=5, pady=3)
        btn_copy = ttk.Button(self, text="复制", width=4, command=self._on_copy_cmd)
        btn_copy.grid(row=row, column=4, sticky=tk.W, padx=5, pady=3)
        for var in [self._local_port_var, self._remote_port_var, self._remote_host_var, 
                     self._username_var, self._key_file_var, self._ssh_port_var]:
            var.trace_add("write", lambda *a: self._update_cmd_preview())
        self._update_cmd_preview()

    def _update_cmd_preview(self) -> None:
        cfg = self.get_config()
        cmd = self._service.build_command(cfg)
        self._full_ssh_cmd = cmd
        self._cmd_preview.config(text=cmd)

    def _on_copy_cmd(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self._full_ssh_cmd)

    def _draw_circle(self, state: str) -> None:
        if self._indicator is None:
            return
        self._indicator.delete("all")
        color = self._state_color(state)
        self._indicator.create_oval(
            1, 1, 11, 11, fill=color, outline="",
        )

    @staticmethod
    def _state_color(state: str) -> str:
        return {
            SSHState.DISCONNECTED: "#888888",
            SSHState.CONNECTING: "#FFA500",
            SSHState.CONNECTED: "#00CC00",
        }.get(state, "#888888")

    def get_config(self) -> SSHConfig:
        return SSHConfig(
            local_port=int(self._local_port_var.get()),
            remote_port=int(self._remote_port_var.get()),
            remote_host=self._remote_host_var.get(),
            username=self._username_var.get(),
            ssh_port=int(self._ssh_port_var.get()),
            key_file=self._key_file_var.get(),
        )

    def update_status(self, state: str) -> None:
        self._state = state
        self._draw_circle(state)

        if self._btn_connect is not None:
            connect_state = (
                tk.NORMAL if state == SSHState.DISCONNECTED else tk.DISABLED
            )
            self._btn_connect.config(state=connect_state)

        if self._btn_disconnect is not None:
            disconnect_state = (
                tk.NORMAL if state in (SSHState.CONNECTING, SSHState.CONNECTED) else tk.DISABLED
            )
            self._btn_disconnect.config(state=disconnect_state)

    def _on_connect_clicked(self) -> None:
        if self._on_connect is not None:
            self._on_connect(self.get_config())

    def _on_disconnect_clicked(self) -> None:
        if self._on_disconnect is not None:
            self._on_disconnect()
