# UI 设计文档

## 1. 总体布局

### 1.1 窗口结构

```
┌──────────────────────────────────────────────────────────────┐
│  [Toolbar]  ─ MEM/GPU 仪表(垂直排列) + 操作按钮 + 自动重启    │
├──────────────────────────────────────────────────────────────┤
│  [Notebook]  ─ Tab页签容器                                    │
│  ┌─ Tab 1: 参数配置 ─────────────────────────────────────┐  │
│  │ [ParamPanel]                                          │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌─ Tab 2: SSH 映射 ────────────────────────────────────┐  │
│  │ [SSHPanel]                                           │  │
│  └───────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  [LogPanel]  ─ 运行日志 (底部, 高度 200px, 可折叠)          │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 布局参数

| 组件 | 布局方式 | 说明 |
|------|---------|------|
| Toolbar | pack(fill=X, side=TOP) | 固定在顶部, 子组件垂直排列 |
| Notebook | pack(fill=BOTH, expand=True) | 占据中间区域 |
| LogPanel | pack(fill=X, side=BOTTOM) | 固定在底部，带折叠按钮 |

### 1.3 窗口属性

| 属性 | 值 |
|------|---|
| 标题 | "llamacpp-panel" |
| 最小尺寸 | 800×600 |
| 初始尺寸 | 1000×700 |
| 可调整大小 | True |

## 2. 组件层级

```
App (tk.Tk)
├── Toolbar (tk.Frame, height=80)
│   ├── Row 1: StatusRow (grid, 4 columns + 1 fixed)
│   │   ├── MemoryIndicator (col=0)      # "MEM: 50% / 16G" + 圆点 + 进度条
│   │   ├── GPUIndicator (col=1)         # "GPU: 30% / 8G" + 圆点 + 进度条
│   │   ├── ServerIndicator (col=2)      # "SERVER: 运行中" + 状态圆点
│   │   ├── SSHIndicator (col=3)         # "SSH: 已连接" + 状态圆点
│   │   └── AutoStartSSH (col=4)         # ☑ "同时启动SSH"
│   └── Row 2: ControlRow (grid)
│   │   ├── ControlButtons (col=0-1)     # [启动][停止][重启]
│   │   └── AutoRestartConfig (col=2-4)  # ☑ 自动重启 | 次数:3 | 间隔:5秒 | 内存:90%
├── Notebook (ttk.Notebook)
│   ├── ParamPanelTab (tk.Frame)
│   │   └── ParamPanel (tk.Frame)
│   │       ├── FileSelectRow (tk.Frame)
│   │       │   ├── btn_select_file (tk.Button)    # "选择启动文件"
│   │       │   └── lbl_server_path (tk.Label)     # 当前路径
│   │       ├── TemplateRow (tk.Frame)
│   │       │   ├── cmb_template (ttk.Combobox)     # 模板选择
│   │       │   ├── btn_load_template (tk.Button)   # "加载"
│   │       │   ├── btn_save_template (tk.Button)   # "保存"
│   │       │   └── btn_save_as_template (tk.Button) # "另存为"
│   │       ├── ModelSelectRow (tk.Frame)
│   │       │   ├── btn_browse (tk.Button)          # "浏览"
│   │       │   └ lbl_model (tk.Label)             # 模型文件路径
│   │       ├── ParamTable (tk.Frame)
│   │       │   └── tree_params (ttk.Treeview)      # 参数表格 (3列)
│   │       └── CmdPreviewRow (tk.Frame)
│   │           ├── lbl_cmd_preview (tk.Label)      # 完整命令预览 (wraplength)
│   │           └── btn_copy_cmd (tk.Button)        # "复制"
│   └── SSHPanelTab (tk.Frame)
│       └── SSHPanel (tk.Frame)
│           ├── ConfigGrid (tk.Frame)
│           │   ├── Row 0: 本地端口 + 远程IP
│           │   ├── Row 1: 远程端口 + 用户名
│           │   ├── Row 2: (空)     + SSH端口
│           │   ├── Row 3: (空)     + 密钥[浏览]
│           │   ├── StatusIndicator (Row 4)         # 状态圆点 (无文字)
│           │   ├── Buttons (Row 5)                 # [连接][断开]
│           │   └── CmdPreview (Row 6)              # SSH 命令预览
└── LogPanel (tk.Frame)
    ├── LogHeader (tk.Frame)
    │   ├── lbl_log_title (tk.Label)     # "运行日志"
    │   └── btn_toggle_log (tk.Button)   # "折叠/展开"
    └── LogContent (tk.Frame)
        └── txt_log (tk.scrolledtext.ScrolledText)
```

## 3. 各组件详细设计

### 3.1 Toolbar

**职责**: 显示系统资源状态、服务器状态、SSH状态，提供快捷操作按钮和配置

**布局**: grid 布局，4列等间隔 (weight=1)，第5列固定

**子组件:**

| 子组件 | 位置 | 说明 |
|--------|------|------|
| MemoryIndicator | Row 0, Col 0 | 内存进度条 + 状态圆点 + 标签 |
| GPUIndicator | Row 0, Col 1 | GPU进度条 + 状态圆点 + 标签 (无GPU显示N/A) |
| ServerIndicator | Row 0, Col 2 | SERVER状态: 已停止/运行中/启动中/已崩溃 |
| SSHIndicator | Row 0, Col 3 | SSH状态: 未连接/连接中/已连接 |
| AutoStartSSH | Row 0, Col 4 | ☑ "同时启动SSH" checkbox |
| ControlButtons | Row 1, Col 0-1 | [启动][停止][重启] 按钮 |
| AutoRestartConfig | Row 1, Col 2-4 | ☑自动重启 + 次数输入 + 间隔输入 + 阈值输入 |

**状态颜色:**

| 组件 | 颜色 |
|------|------|
| MEM/GPU 正常 | 绿色 (#4CAF50) |
| MEM/GPU 告警 (80%) | 黄色 (#FF9800) |
| MEM/GPU 危险 (90%) | 红色 (#F44336) |
| SERVER 已停止 | 灰色 (#888888) |
| SERVER 运行中 | 绿色 (#00CC00) |
| SERVER 启动中 | 黄色 (#FFA500) |
| SERVER 已崩溃 | 红色 (#CC0000) |
| SSH 未连接 | 灰色 (#888888) |
| SSH 连接中 | 黄色 (#FFA500) |
| SSH 已连接 | 绿色 (#00CC00) |

**按钮状态:**

| 状态 | 启动按钮 | 停止按钮 | 重启按钮 |
|------|---------|---------|---------|
| 已停止 | 可用 | 禁用 | 禁用 |
| 运行中 | 禁用 | 可用 | 可用 |
| 启动中 | 禁用 | 可用 | 禁用 |
| 已崩溃 | 可用 | 禁用 | 可用 |

**AutoRestartConfig 参数:**

| 参数 | 默认值 | 输入控件 |
|------|--------|----------|
| max_restarts | 3 | Entry (width=4) |
| restart_interval | 5.0 | Entry (width=4) 秒 |
| memory_threshold | 90.0 | Entry (width=4) % |

**AutoStartSSH 行为:**
- 勾选后，服务器启动成功并端口就绪时自动启动 SSH tunnel
- 使用 socket 连接测试端口可用性 (最多检查10次，每次间隔1秒)

**颜色规则:**
- 内存 < 80%: 绿色
- 内存 80%-90%: 黄色
- 内存 > 90%: 红色

**回调接口:**
```
on_start_clicked()
on_stop_clicked()
on_restart_clicked()
on_auto_restart_toggled(enabled: bool)
update_memory_display(stats: MemoryStats)
update_gpu_display(stats: GPUStats | None)
set_button_state(state: ButtonState)
```

### 3.2 ParamPanel

**职责**: 可视化配置 llama.cpp 启动参数

**子组件:**

#### FileSelectRow
| 控件 | 说明 |
|------|------|
| btn_select_file | 打开文件对话框选择启动文件，标签 "选择启动文件" |
| lbl_server_path | 显示当前选中路径，过长时省略 |

**交互:**
- 点击 btn_select_file → 调用 `file_utils.select_server_file()` → Windows 过滤 `*.exe`, Linux 显示所有文件 → 更新 lbl_server_path → 触发 `on_path_changed`

#### TemplateRow
| 控件 | 说明 |
|------|------|
| cmb_template | 下拉选择模板（从 config/templates/*.json 动态加载） |
| btn_load_template | 将选中模板的参数加载到表格 |
| btn_save_template | 保存当前配置覆盖选中模板 |
| btn_save_as_template | 弹出对话框输入模板名，保存为新模板 |

**交互:**
- 点击 btn_load_template → 调用 `param_service.get_template()` → 填充 ParamTable（不含 -m 参数）
- 点击 btn_save_template → 从 ParamTable 读取参数 + 模型路径 → 调用 `param_service.save_template()`
- 模板文件存储: `config/templates/<模板名>.json`

#### ModelSelectRow (新增)
| 控件 | 说明 |
|------|------|
| lbl_model_label | "模型:" |
| btn_browse | "浏览" — 打开 gguf 文件选择对话框 |
| lbl_model | 显示模型文件路径 |

**交互:**
- 点击 btn_browse → filedialog 过滤 `*.gguf` → 设置模型路径 → 更新命令预览
- 模型路径独立于参数表，不在 ParamTable 中显示
- 拼接命令时自动追加 `-m {模型路径}`

#### ParamTable (ttk.Treeview)
| 列名 | 宽度 | 说明 | 可编辑 |
|------|------|------|--------|
| 参数名 | 100px | 如 -c, -ngl, --threads | 是 |
| 值 | 200px | 参数值 | 是 |
| 操作 | 60px | [删除] 按钮 | - |

**注意**: 不含 `-m` 参数（由 ModelSelectRow 独立管理）。不含"分类"和"必填"列。

**交互:**
- 双击 name/value 单元格 → 进入编辑模式
- 编辑完成后按 Enter → 更新 Parameter → 触发命令预览更新
- 双击操作单元格 → 删除对应行 → 触发命令预览更新
- 底部 "+ 添加参数" 按钮 → 插入空行

#### CmdPreviewRow
| 控件 | 说明 |
|------|------|
| lbl_cmd_preview | 显示拼接后的完整命令，如 `server -m model.gguf -c 4096` |
| btn_copy_cmd | 将命令复制到剪贴板 |

**交互:**
- 任何参数变化或模型路径变化 → 调用 `param_service.build_command()` → 更新 lbl_cmd_preview
- 点击 btn_copy_cmd → `app.clipboard_append()` → 短暂显示"已复制"

**回调接口:**
```
on_file_selected(path: str)
on_history_selected(path: str)
on_model_selected(path: str)
on_load_template(name: str)
on_save_template(name: str)
on_save_as_template(name: str)
on_parameter_changed(params: list[Parameter])
on_command_copy()
```

### 3.3 SSHPanel

**职责**: 配置和管理 SSH 反向端口映射

**子组件:**

#### SSHConfigGrid (左右 2 列布局)
| 行 | 左列 (col=0) | 右列 (col=2) |
|----|-------------|-------------|
| 0 | 本地端口: [entry] | 远程IP: [entry] |
| 1 | 远程端口: [entry] | 用户名: [entry] |
| 2 | (空) | SSH端口: [entry] (默认 22) |
| 3 | (空) | 密钥: [entry][浏览] |

**注意**: SSH端口字段用于 `-p` 参数，支持非默认端口 (如 2202)

#### SSHStatusIndicator
| 控件 | 说明 |
|------|------|
| status_indicator | 12×12 Canvas 圆形，颜色表示状态 (无文字标签) |

**状态颜色:**

| 状态 | 颜色 |
|------|------|
| disconnected | 灰色 (#888) |
| connecting | 黄色 (#FFA500) |
| connected | 绿色 (#00CC00) |

#### SSHButtons
| 按钮 | 显示条件 |
|------|---------|
| 连接 | 未连接时可用 |
| 断开 | 已连接/连接中时可用 |

#### SSHCmdPreviewRow
| 控件 | 说明 |
|------|------|
| lbl_cmd_label | "命令:" |
| lbl_cmd_preview | 显示完整 SSH 命令 (wraplength, 不截断) |
| btn_copy_cmd | 复制到剪贴板 |

**SSH 命令格式:**
```bash
ssh -R 0.0.0.0:8080:127.0.0.1:8080 -o StrictHostKeyChecking=no -N -p 2202 -i /path/key root@172.18.12.xxx
```

**模板保存:** SSH 配置随模板一起保存到 `config/templates/*.json`

**回调接口:**
```
on_connect_clicked(cfg: SSHConfig)
on_disconnect_clicked()
update_status(state: SSHState)
get_config() -> SSHConfig
```

### 3.4 LogPanel

**职责**: 显示运行日志 + 持久化到日志文件

**子组件:**

| 控件 | 说明 |
|------|------|
| lbl_log_title | "运行日志" |
| btn_toggle_log | 折叠/展开日志区域 |
| txt_log | ScrolledText，只读，带垂直滚动条 |

**日志级别颜色:**

| 级别 | 颜色 | 标签 |
|------|------|------|
| INFO | 黑色 (#000000) | [INFO] |
| WARN | 橙色 (#CC6600) | [WARN] |
| ERROR | 红色 (#CC0000) | [ERROR] |
| SYSTEM | 蓝色 (#0066CC) | [SYS] |

**格式**: `[2026-04-24 10:00:01] [INFO] Starting server...`

**行为:**
- 每行追加时自动滚动到底部
- 折叠时隐藏 LogContent，LogHeader 仍可见
- 日志行数上限 10000 行（超出自动清理旧日志）

**日志文件:**
- 文件名格式: `log/YYYY-MM-DD.txt` (每日一个文件)
- 格式: `[YYYY-MM-DD HH:MM:SS] [LEVEL] module: message`
- 同时输出到终端控制台 (便于调试)

**两层日志系统:**

| 系统 | 目标 | 内容 |
|------|------|------|
| LogPanel (UI) | 用户 | 简洁中文状态日志 |
| log/*.txt | 开发者 | 详细技术日志 (含参数值、PID 等) |
- 路径: `log/app.log`
- 格式: `[YYYY-MM-DD HH:MM:SS] [LEVEL] message`
- 来源: Python logging 模块，服务层和 UI 层共用

**回调接口:**
```
log(message: str, level: str = "INFO")
toggle_visibility()
clear()
```

## 4. 事件流

### 4.1 启动流程

```
用户点击"启动"
    → Toolbar.btn_start clicked
    → App.on_start_clicked()
    → 从 ParamPanel 获取 LaunchConfig (含模型路径)
    → param_service.validate(config)
        → 校验失败 → messagebox.showerror → 中止
        → 校验成功 →
    → process_manager.start(config)
    → log_panel.log("Server started", "INFO")
    → toolbar.set_button_state("running")
```

### 4.2 参数变更流程

```
用户编辑 ParamTable 单元格
    → ParamPanel.on_cell_edited()
    → tree_params 数据更新
    → param_service.build_command(current_params + model_path)
    → cmd_preview_label 更新为拼接命令
```

### 4.3 内存/GPU 监控流程

```
monitor_service 后台线程 (每 3s)
    → psutil.virtual_memory() → MemoryStats
    → nvidia-smi → GPUStats | None
    → callback(memory_stats, gpu_stats)
    → App._on_monitor_update(memory_stats, gpu_stats)
    → toolbar.update_memory_display(memory_stats)
        → memory_label 更新: "MEM: 60% / 16G"
        → memory_progress 更新进度条
        → 超阈值 → 颜色变红
    → toolbar.update_gpu_display(gpu_stats)
        → gpu_label 更新: "GPU: 45% / 8G"
        → gpu_progress 更新进度条
```

### 4.4 SSH 连接流程

```
用户点击"连接"
    → SSHPanel.btn_connect clicked
    → 读取 SSHConfig (含密码/密钥字段)
    → App.on_connect_clicked(cfg)
    → ssh_service.build_command(cfg)
        → 若有密码: "sshpass -p xxx ssh ..."
        → 若有密钥: "ssh ... -i {key_file}"
    → ssh_service.connect(cfg)
    → status 更新为 connecting
    → SSH 进程建立成功
    → status 更新为 connected
    → 异常 → status 更新为 disconnected + messagebox
```

### 4.5 自动重启流程

```
process_manager 监控线程
    → process.poll()
    → 返回 exit_code (非 None)
    → 判断: auto_restart == True && restart_count < max_restarts
        → restart_count++
        → log_panel.log(f"Auto-restart #{restart_count}", "WARN")
        → process_manager.start(config)
        → log_panel.log("Server restarted", "INFO")
    → 否则: log_panel.log("Max restarts reached", "ERROR")
```

## 5. 跨平台兼容

| 差异点 | Windows | Linux |
|--------|---------|-------|
| 可执行文件名 | server.exe | server |
| 文件对话框 | tk.filedialog (*.exe 过滤) | tk.filedialog (所有文件) |
| 进程终止 | os.kill + CTRL_BREAK_EVENT | SIGTERM |
| 字体 | "Microsoft YaHei" | "Noto Sans CJK SC" |

## 6. 快捷键 (未来扩展)

| 快捷键 | 功能 |
|--------|------|
| Ctrl+Enter | 启动服务 |
| Ctrl+. | 停止服务 |
| Ctrl+R | 重启服务 |
| Ctrl+Shift+L | 折叠/展开日志 |

## 7. 无障碍

- 所有按钮有 focusable=True
- 标签有 accelerator 提示（未来）
- 颜色对比度符合 WCAG AA 标准
