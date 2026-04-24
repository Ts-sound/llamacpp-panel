from __future__ import annotations

import subprocess
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

    pid = process.pid
    
    if get_platform() == "windows":
        try:
            process.send_signal(subprocess.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
        except (OSError, AttributeError, ProcessLookupError):
            pass
        try:
            process.terminate()
            process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, TimeoutError):
            try:
                process.kill()
                process.wait(timeout=2)
            except Exception:
                pass
        except Exception:
            pass
        return

    try:
        process.terminate()
        process.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, TimeoutError):
        try:
            process.kill()
            process.wait(timeout=2)
        except Exception:
            pass
    except (OSError, ProcessLookupError):
        pass
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
