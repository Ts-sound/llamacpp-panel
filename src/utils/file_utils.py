from __future__ import annotations

import os
import pathlib
import sys
import tkinter
from tkinter import filedialog


def select_server_file(parent: tkinter.Misc) -> str | None:
    if sys.platform == "win32":
        file_types = [("可执行文件", "*.exe")]
    else:
        file_types = [("所有文件", "*")]
    path = filedialog.askopenfilename(
        parent=parent,
        title="选择启动文件",
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
