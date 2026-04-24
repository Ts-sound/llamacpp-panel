# UI 组件设计文档

## 1. 组件总览

| 文件 | 类 | 继承 | 尺寸 | 说明 |
|------|---|------|------|------|
| `app.py` | App | tk.Tk | 1000×700 | 主窗口, 组件编排, 服务依赖注入 |
| `toolbar.py` | Toolbar | tk.Frame | - | 资源仪表(垂直排列)+操作按钮 |
| `param_panel.py` | ParamPanel | tk.Frame | - | 参数配置面板 |
| `ssh_panel.py` | SSHPanel | tk.Frame | - | SSH 映射配置面板 |
| `log_panel.py` | LogPanel | tk.Frame | height=200 | 运行日志面板 |

## 2. App (主窗口)

**职责**: 
- 创建 Tkinter 根窗口
- 组装所有 UI 组件
- 注入所有服务实例
- 连接 UI 回调 → 服务方法
- 连接服务回调 → UI 更新方法
- 处理窗口关闭事件

**布局顺序:** Toolbar (top) → Notebook (expand) → LogPanel (bottom)

**核心方法:**

| 方法 | 说明 |
|------|------|
| `_on_start()` | 校验配置 → 启动进程 → 更新按钮状态 |
| `_on_stop()` | 停止进程 → 更新按钮状态 |
| `_on_restart()` | 停止旧进程 → 启动新进程 |
| `_on_monitor_update(stats, gpu_stats)` | 内存/GPU 回调 → 更新 Toolbar |
| `_on_auto_restart_toggle(enabled)` | 自动重启开关 |
| `_on_save_template(name)` | 保存模板到文件 |
| `_on_save_as_template()` | 弹出对话框保存新模板 |
| `_on_closing()` | 优雅关闭: 停止线程, 终止进程, 保存配置 |

**回调连接 (UI → Service):**

| UI 回调 | 绑定方法 |
|--------|---------|
| on_start_clicked | _on_start |
| on_stop_clicked | _on_stop |
| on_restart_clicked | _on_restart |
| on_auto_restart_toggled | _on_auto_restart_toggle |

**回调连接 (Service → UI):**

| 服务回调 | 绑定方法 |
|---------|---------|
| process_manager.log_callback | log_panel.log |
| monitor_service.callback | _on_monitor_update (含 GPU stats) |
| ssh_service.log_callback | log_panel.log |

**关闭流程:**
1. 停止当前进程
2. 停止内存监控线程
3. 停止自动重启线程
4. 保存配置到文件
5. 销毁窗口

## 3. Toolbar

**职责**: 显示系统资源状态，提供快捷操作按钮

**布局**: `pack(side=TOP, fill=X, padx=10, pady=2)` — 所有子组件垂直排列

**子组件:**

| 子组件 | 类型 | 说明 |
|--------|------|------|
| MemoryBar | tk.Frame | 内存进度条 + 标签, 垂直排列(顶部) |
| GPUBar | tk.Frame | GPU 进度条 + 标签, 垂直排列(MEM 下方, 无 GPU 时隐藏) |
| ControlButtons | tk.Frame | 启动/停止/重启按钮 |
| AutoRestartToggle | tk.Frame | 自动重启开关 |

**显示格式:**
- MemoryBar: `"MEM: {percent:.0f}% / {total_gb:.0f}G"`
- GPUBar: `"GPU: {percent:.0f}% / {total_gb:.0f}G"`

**按钮状态表:**

| 状态 | 启动 | 停止 | 重启 |
|------|------|------|------|
| 已停止 | 可用 | 禁用 | 禁用 |
| 运行中 | 禁用 | 可用 | 可用 |
| 启动中 | 禁用 | 可用 | 禁用 |
| 崩溃 | 可用 | 禁用 | 可用 |

**内存颜色规则:**
- < 80%: 绿色
- 80%-90%: 黄色
- > 90%: 红色

**回调接口:**

| 回调 | 签名 |
|------|------|
| on_start_clicked | `Callable[[], None]` |
| on_stop_clicked | `Callable[[], None]` |
| on_restart_clicked | `Callable[[], None]` |
| on_auto_restart_toggled | `Callable[[bool], None]` |

**更新方法:**

| 方法 | 输入 | 说明 |
|------|------|------|
| update_memory_display | MemoryStats | 更新内存进度条和颜色 |
| update_gpu_display | GPUStats\|None | 更新 GPU 进度条 |
| set_button_state | str (stopped/running/starting/crashed) | 更新按钮可用状态 |

## 4. ParamPanel

**职责**: 可视化配置 llama.cpp 启动参数

**布局结构:**

```
┌─ 参数配置 ────────────────────────────────────┐
│ [选择启动文件] /path/to/server  [历史记录▼]    │
│ 模板: [GPU加速▼] [加载] [保存] [另存为]        │
│ 模型: [浏览] xxx.gguf                          │
│ ┌───────────────────────────────────────────┐ │
│ │ 参数名 │ 值        │ 操作 │               │ │
│ │ -c     │ 4096      │ [删除]│               │ │
│ │ -ngl   │ 99        │ [删除]│               │ │
│ └───────────────────────────────────────────┘ │
│ [+ 添加参数]                                    │
│ 预览: /path/to/server -m xxx.gguf -c 4096 -ngl 99  [复制] │
└───────────────────────────────────────────────┘
```

**子组件:**

### FileSelectRow

| 控件 | 说明 | 交互 |
|------|------|------|
| btn_select_file | "选择启动文件" 打开文件对话框 | Windows: `*.exe` 过滤, Linux: 所有文件 |
| lbl_server_path | 显示当前路径（过长省略） | - |

### TemplateRow

| 控件 | 说明 | 交互 |
|------|------|------|
| cmb_template | 模板下拉 (动态加载 config/templates/*.json) | - |
| btn_load_template | 加载模板参数 | 读取模板 → 填充 ParamTable (不含 -m) |
| btn_save_template | 保存覆盖当前模板 | 从 ParamTable + 模型路径 → 保存 |
| btn_save_as_template | 另存为新模板 | 弹出对话框输入名称 → 保存 |

### ModelSelectRow (新增)

| 控件 | 说明 | 交互 |
|------|------|------|
| lbl_model_label | "模型:" | - |
| btn_browse | "浏览" | 打开 gguf 文件选择对话框 (*.gguf) |
| lbl_model | 显示模型文件路径 | - |

**注意**: 模型路径独立管理，不参与模板的 ParamTable 参数列表。拼接命令时自动添加 `-m {模型路径}`。

### ParamTable

| 列名 | 宽度 | 说明 | 可编辑 |
|------|------|------|--------|
| 参数名 | 100px | 如 -c, -ngl, --threads | 是 |
| 值 | 200px | 参数值 | 是 |
| 操作 | 60px | [删除] 按钮 | - |

**交互:**
- 双击 name/value 单元格 → 编辑模式
- 按 Enter → 更新 Parameter → 触发命令预览更新
- 双击操作列 → 删除行 → 触发命令预览更新
- [+ 添加参数] → 插入空行

### CmdPreviewRow

| 控件 | 说明 |
|------|------|
| lbl_cmd_preview | 显示拼接命令 |
| btn_copy_cmd | 复制到剪贴板 |

**交互:**
- 任何参数变化或模型路径变化 → 重新拼接命令 → 更新 lbl_cmd_preview
- 点击 btn_copy_cmd → 复制到剪贴板 → 短暂显示"已复制"

**回调接口:**

| 回调 | 签名 |
|------|------|
| on_file_selected | `Callable[[str], None]` |
| on_history_selected | `Callable[[str], None]` |
| on_model_selected | `Callable[[str], None]` |
| on_load_template | `Callable[[str], None]` |
| on_save_template | `Callable[[str], None]` |
| on_save_as_template | `Callable[[str], None]` |
| on_parameter_changed | `Callable[[list[Parameter]], None]` |

**核心方法:**

| 方法 | 说明 |
|------|------|
| get_launch_config() | 构建 LaunchConfig (含模型路径 + ParamTable 参数) |
| load_parameters(params) | 加载参数列表到 Treeview (过滤 -m) |
| update_command_preview() | 从当前参数 + 模型路径拼接并更新预览 |
| set_model_path(path) | 设置模型路径 |
| get_model_path() | 获取模型路径 |

## 5. SSHPanel

**职责**: 配置和管理 SSH 反向端口映射

**布局:**

```
┌─ SSH 端口映射 ───────────────────────────────┐
│ 本地端口: [8080        ]  远程端口: [8080    ]│
│ 远程IP:   [172.18.122.71]                    │
│ 用户名:   [root         ]                    │
│ 密码:     [********     ]                    │
│ 密钥:     [path         ] [浏览]             │
│ ┌──┐ 已连接                                 │
│ [连接] [断开]                                │
└──────────────────────────────────────────────┘
```

### SSHConfigGrid (2列 grid)

| 行 | 标签 | 输入控件 | 默认值 |
|----|------|---------|--------|
| 0 | 本地端口 | Entry (int) | 8080 |
| 1 | 远程端口 | Entry (int) | 8080 |
| 2 | 远程IP | Entry (str) | 172.18.122.71 |
| 3 | 用户名 | Entry (str) | root |
| 4 | 密钥 | Entry + 浏览按钮 | 空 |

**认证方式**: 仅密钥文件认证，密码已移除。

### SSHStatusRow

| 控件 | 说明 |
|------|------|
| status_indicator | 12×12 Canvas 圆形，颜色表示状态 |
| lbl_status | 状态文字 |

**状态颜色:**

| 状态 | 颜色 | 标签文字 |
|------|------|---------|
| disconnected | 灰色 (#888) | 未连接 |
| connecting | 黄色 (#FFA500) | 连接中... |
| connected | 绿色 (#00CC00) | 已连接 |

### SSHButtons

| 按钮 | 显示条件 |
|------|---------|
| 连接 | 未连接时可用 |
| 断开 | 已连接/连接中时可用 |

### SSHCmdPreviewRow (新增)

| 控件 | 说明 |
|------|------|
| lbl_cmd_label | "命令:" |
| lbl_cmd_preview | 显示 SSH 命令字符串 |
| btn_copy_cmd | 复制到剪贴板 |

**交互:**
- 字段变化 → 重新构建命令 → 更新预览
- 点击复制 → 复制到剪贴板

**回调接口:**

| 回调 | 签名 |
|------|------|
| on_connect_clicked | `Callable[[SSHConfig], None]` |
| on_disconnect_clicked | `Callable[[], None]` |

**核心方法:**

| 方法 | 说明 |
|------|------|
| get_config() | 从输入字段读取 SSHConfig (含 password, key_file) |
| update_status(state) | 根据 SSHState 更新状态显示 |

## 6. LogPanel

**职责**: 显示运行日志

**子组件:**

| 控件 | 说明 |
|------|------|
| lbl_log_title | "运行日志" |
| btn_toggle_log | 折叠/展开 |
| txt_log | ScrolledText, 只读, 带滚动条 |

**日志级别颜色:**

| 级别 | 颜色 | 标签 |
|------|------|------|
| INFO | 黑色 (#000000) | [INFO] |
| WARN | 橙色 (#CC6600) | [WARN] |
| ERROR | 红色 (#CC0000) | [ERROR] |
| SYSTEM | 蓝色 (#0066CC) | [SYS] |

**格式**: `[YYYY-MM-DD HH:MM:SS] [LEVEL] message`

**行为:**
- 每行追加时自动滚动到底部
- 折叠时隐藏 LogContent，LogHeader 仍可见
- 日志行数上限 10000 行（超出自动清理旧日志，保留最近 5000 行）
- 所有日志同步写入 `log/app.log` 文件

**日志文件:**
- 路径: `log/app.log`
- 格式: `[YYYY-MM-DD HH:MM:SS] [LEVEL] message`
- 来源: Python logging.FileHandler，服务层和 UI 层共用

**回调接口:**

| 回调 | 签名 |
|------|------|
| log | `Callable[[str, str], None]` (message, level) |
| toggle_visibility | `Callable[[], None]` |
| clear | `Callable[[], None]` |

## 7. 样式定义

使用 ttk.Style 定义进度条颜色样式:

| 样式名 | 颜色 | 用途 |
|--------|------|------|
| Danger.Horizontal.TProgressbar | 红色 | 内存 > 90% |
| Warning.Horizontal.TProgressbar | 橙色 | 内存 80%-90% |
| Normal.Horizontal.TProgressbar | 绿色 | 内存 < 80% |
