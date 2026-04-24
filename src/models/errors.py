from __future__ import annotations


class ProcessError(Exception):
    def __init__(self, message: str, exit_code: int | None = None, stderr: str | None = None) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr


class SSHError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
