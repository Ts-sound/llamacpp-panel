from __future__ import annotations

import os
import pathlib
import tkinter
from tkinter import filedialog


def select_server_file(parent: tkinter.Misc) -> str | None:
    platform = os.environ.get("LLAMACPP_PANEL_PLATFORM", "")
    if not platform:
        import sys
        platform = "windows" if sys.platform.startswith("win") else "linux"

    if platform == "windows":
        file_types = [("Server Executable", "server.exe")]
    else:
        file_types = [("Server Binary", "server")]

    path = filedialog.askopenfilename(
        parent=parent,
        title="Select Server Executable",
        filetypes=file_types,
    )

    if path:
        return normalize_path(path)
    return None


def validate_executable(path: str) -> bool:
    normalized = normalize_path(path)
    p = pathlib.Path(normalized)
    if not p.is_file():
        return False
    if not os.access(normalized, os.X_OK):
        return False
    return True


def normalize_path(path: str) -> str:
    return str(pathlib.Path(path).expanduser().resolve())
