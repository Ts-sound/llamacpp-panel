# 工具层设计文档

## 1. 模块总览

| 文件 | 函数 | 说明 |
|------|------|------|
| `file_utils.py` | `select_server_file` | 打开文件选择对话框 |
| `file_utils.py` | `validate_executable` | 检查文件是否存在且可执行 |
| `file_utils.py` | `normalize_path` | 规范化路径 |
| `cross_platform.py` | `get_platform` | 返回当前平台标识 |
| `cross_platform.py` | `get_server_executable_name` | 返回可执行文件名 |
| `cross_platform.py` | `kill_process` | 跨平台安全终止进程 |
| `cross_platform.py` | `get_cpu_count` | 返回系统 CPU 核心数 |

## 2. file_utils.py

### select_server_file

| 项 | 说明 |
|----|------|
| 输入 | parent: tk.Misc (Tkinter 父窗口) |
| 返回 | str\|None (选中路径或 None) |
| 行为 | 打开文件选择对话框，过滤 server 可执行文件 |

**平台差异:**
| 平台 | 过滤器 |
|------|--------|
| Windows | `Server Executable (server.exe)` |
| Linux | `Server Binary (server)` |

### validate_executable

| 项 | 说明 |
|----|------|
| 输入 | path: str |
| 返回 | bool |
| 行为 | 检查文件存在且可执行 |

### normalize_path

| 项 | 说明 |
|----|------|
| 输入 | path: str |
| 返回 | str (绝对路径) |
| 行为 | 展开 ~, 统一路径分隔符, 返回绝对路径 |

## 3. cross_platform.py

### get_platform

| 项 | 说明 |
|----|------|
| 输入 | 无 |
| 返回 | str: "windows" 或 "linux" |

### get_server_executable_name

| 项 | 说明 |
|----|------|
| 输入 | 无 |
| 返回 | str: "server.exe" (Windows) 或 "server" (Linux) |

### kill_process

| 项 | 说明 |
|----|------|
| 输入 | process: Popen\|None, timeout: int=5 |
| 返回 | None |
| 行为 | SIGTERM → 等待 timeout 秒 → SIGKILL |

**平台差异:**
| 平台 | 终止方式 |
|------|---------|
| Windows | CTRL_BREAK_EVENT + terminate |
| Linux | SIGTERM → SIGKILL |

### get_cpu_count

| 项 | 说明 |
|----|------|
| 输入 | 无 |
| 返回 | int (CPU 核心数, 失败时返回 4) |
