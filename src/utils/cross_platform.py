from __future__ import annotations

import os
import signal
import sys
from subprocess import Popen


def get_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    return "linux"


def get_server_executable_name() -> str:
    if get_platform() == "windows":
        return "server.exe"
    return "server"


def kill_process(process: Popen[bytes] | None, timeout: int = 5) -> None:
    if process is None:
        return

    if get_platform() == "windows":
        try:
            process.send_signal(  # type: ignore[arg-type]
                getattr(__import__("subprocess"), "CTRL_BREAK_EVENT")  # type: ignore[arg-type]
            )
        except (OSError, AttributeError):
            pass
        process.terminate()
        try:
            process.wait(timeout=timeout)
        except Exception:
            process.kill()
            process.wait()
        return

    try:
        process.terminate()
        try:
            process.wait(timeout=timeout)
        except Exception:
            process.kill()
            process.wait()
    except Exception:
        pass


def get_cpu_count() -> int:
    try:
        import os

        count = os.cpu_count()
        if count is not None and count > 0:
            return count
    except Exception:
        pass
    return 4
