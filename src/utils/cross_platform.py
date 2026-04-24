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

    import logging
    logger = logging.getLogger(__name__)
    
    pid = process.pid
    logger.info("[KILL_PROCESS] pid=%d, platform=%s, starting", pid, get_platform())
    
    if get_platform() == "windows":
        logger.info("[KILL_PROCESS] pid=%d, windows_branch", pid)
        try:
            process.send_signal(subprocess.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
            logger.info("[KILL_PROCESS] pid=%d, CTRL_BREAK_sent", pid)
        except (OSError, AttributeError, ProcessLookupError) as e:
            logger.info("[KILL_PROCESS] pid=%d, CTRL_BREAK_error: %s", pid, e)
        try:
            process.terminate()
            logger.info("[KILL_PROCESS] pid=%d, terminate_sent, waiting", pid)
            process.wait(timeout=timeout)
            logger.info("[KILL_PROCESS] pid=%d, terminated", pid)
        except (subprocess.TimeoutExpired, TimeoutError):
            logger.warning("[KILL_PROCESS] pid=%d, terminate_timeout, killing", pid)
            try:
                process.kill()
                process.wait(timeout=2)
                logger.info("[KILL_PROCESS] pid=%d, killed", pid)
            except Exception as e:
                logger.error("[KILL_PROCESS] pid=%d, kill_error: %s", pid, e)
        except Exception as e:
            logger.error("[KILL_PROCESS] pid=%d, terminate_error: %s", pid, e)
        return

    logger.info("[KILL_PROCESS] pid=%d, linux_branch", pid)
    try:
        process.terminate()
        logger.info("[KILL_PROCESS] pid=%d, terminate_sent, waiting", pid)
        process.wait(timeout=timeout)
        logger.info("[KILL_PROCESS] pid=%d, terminated", pid)
    except (subprocess.TimeoutExpired, TimeoutError):
        logger.warning("[KILL_PROCESS] pid=%d, terminate_timeout, killing", pid)
        try:
            process.kill()
            process.wait(timeout=2)
            logger.info("[KILL_PROCESS] pid=%d, killed", pid)
        except Exception as e:
            logger.error("[KILL_PROCESS] pid=%d, kill_error: %s", pid, e)
    except (OSError, ProcessLookupError) as e:
        logger.info("[KILL_PROCESS] pid=%d, process_not_found: %s", pid, e)
    except Exception as e:
        logger.error("[KILL_PROCESS] pid=%d, terminate_error: %s", pid, e)


def get_cpu_count() -> int:
    try:
        import os

        count = os.cpu_count()
        if count is not None and count > 0:
            return count
    except Exception:
        pass
    return 4
