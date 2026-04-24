"""Default configuration constants for llamacpp-panel."""

import os

MONITOR_INTERVAL: float = 3.0
MAX_RESTARTS: int = 3
MEMORY_THRESHOLD: float = 90.0

SSH_LOCAL_PORT: int = 8080
SSH_REMOTE_PORT: int = 8080
SSH_REMOTE_HOST: str = "172.18.122.71"
SSH_USERNAME: str = "root"
SSH_PORT: int = 22

CONFIG_PATH: str = "config/app_config.json"
CONFIG_DIR: str = os.path.dirname(CONFIG_PATH) or "config"

MAX_LOG_LINES: int = 10000
LOG_KEEP_LINES: int = 5000

PROCESS_STOP_TIMEOUT: int = 5

MEMORY_WARNING_THRESHOLD: float = 80.0
MEMORY_DANGER_THRESHOLD: float = 90.0
