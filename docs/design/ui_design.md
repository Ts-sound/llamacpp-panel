# UI 设计文档

## 1. 总体布局

### 1.1 窗口结构

```
┌──────────────────────────────────────────────────────────────┐
│  [Toolbar]  ─ 内存仪表 + GPU仪表 + 操作按钮 + 自动重启开关    │
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
| Toolbar | pack(fill=X, side=TOP) | 固定在顶部 |
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
├── Toolbar (tk.Frame)
│   ├── MemoryBar (tk.Frame)
│   │   ├── memory_label (tk.Label)      # "内存: 45%"
│   │   └── memory_progress (ttk.Progressbar)
│   ├── GPUBbar (tk.Frame)
│   │   ├── gpu_label (tk.Label)         # "GPU: 62%"
│   │   └── gpu_progress (ttk.Progressbar)
│   ├── ControlButtons (tk.Frame)
│   │   ├── btn_start (tk.Button)        # "▶ 启动"
│   │   ├── btn_stop (tk.Button)         # "⏹ 停止"
│   │   └── btn_restart (tk.Button)      # "🔄 重启"
│   └── AutoRestartToggle (tk.Frame)
│       ├── lbl_auto_restart (tk.Label)  # "自动重启:"
│       └── chk_auto_restart (tk.Checkbutton)
├── Notebook (ttk.Notebook)
│   ├── ParamPanelTab (tk.Frame)
│   │   └── ParamPanel (tk.Frame)
│   │       ├── FileSelectRow (tk.Frame)
│   │       │   ├── btn_select_file (tk.Button)    # "选择文件"
│   │       │   ├── lbl_server_path (tk.Label)     # 当前路径
│   │       │   └── cmb_history (tk.ttk.Combobox)  # 历史记录下拉
│   │       ├── TemplateRow (tk.Frame)
│   │       │   ├── lbl_template (tk.Label)         # "模板:"
│   │       │   ├── cmb_template (ttk.Combobox)     # 模板选择
│   │       │   ├── btn_load_template (tk.Button)   # "加载"
│   │       │   ├── btn_save_template (tk.Button)   # "保存"
│   │       │   └── btn_save_as_template (tk.Button) # "另存为"
│   │       ├── ParamTable (tk.Frame)
│   │       │   └── tree_params (ttk.Treeview)      # 参数表格
│   │       │       列: 参数名 | 值 | 分类 | 必填 | 操作
│   │       └── CmdPreviewRow (tk.Frame)
│   │           ├── lbl_cmd_preview (tk.Label)       # "预览: ..."
│   │           └── btn_copy_cmd (tk.Button)         # "复制"
│   └── SSHPanelTab (tk.Frame)
│       └── SSHPanel (tk.Frame)
│           ├── SSHConfigGrid (tk.Frame)
│           │   ├── lbl_local_port (tk.Label)        # "本地端口:"
│           │   ├── ent_local_port (tk.Entry)
│           │   ├── lbl_remote_port (tk.Label)       # "远程端口:"
│           │   ├── ent_remote_port (tk.Entry)
│           │   ├── lbl_remote_host (tk.Label)       # "远程IP:"
│           │   ├── ent_remote_host (tk.Entry)
│           │   ├── lbl_username (tk.Label)          # "用户名:"
│           │   └── ent_username (tk.Entry)
│           ├── SSHStatusRow (tk.Frame)
│           │   ├── status_indicator (tk.Canvas)     # 颜色圆点
│           │   └── lbl_status (tk.Label)            # 状态文字
│           └── SSHButtons (tk.Frame)
│               ├── btn_connect (tk.Button)           # "连接"
│               └── btn_disconnect (tk.Button)       # "断开"
└── LogPanel (tk.Frame)
    ├── LogHeader (tk.Frame)
    │   ├── lbl_log_title (tk.Label)     # "运行日志"
    │   └── btn_toggle_log (tk.Button)   # "折叠/展开"
    └── LogContent (tk.Frame)
        └── txt_log (tk.scrolledtext.ScrolledText)
```

## 3. 各组件详细设计

### 3.1 Toolbar

**职责**: 显示系统资源状态，提供快捷操作按钮

**子组件:**

| 子组件 | 类型 | 宽度 | 说明 |
|--------|------|------|------|
| MemoryBar | tk.Frame | ~150px | 内存进度条 + 标签 |
| GPUBbar | tk.Frame | ~150px | GPU 进度条 + 标签（无 GPU 时隐藏） |
| ControlButtons | tk.Frame | ~180px | 启动/停止/重启按钮 |
| AutoRestartToggle | tk.Frame | ~120px | 自动重启开关 |

**布局**: `grid(row=0, columns=0-3, sticky=W, padx=10, pady=5)`

**状态与行为:**

| 状态 | 启动按钮 | 停止按钮 | 重启按钮 |
|------|---------|---------|---------|
| 已停止 | 可用(绿色) | 禁用(灰色) | 禁用(灰色) |
| 运行中 | 禁用(灰色) | 可用(红色) | 可用(蓝色) |
| 启动中 | 禁用 | 可用 | 禁用 |
| 崩溃 | 可用 | 禁用 | 可用 |

**颜色规则:**
- 内存 < 80%: 绿色
- 内存 80%-90%: 黄色
- 内存 > 90%: 红色（闪烁告警）

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
| btn_select_file | 打开文件对话框选择 server 可执行文件 |
| lbl_server_path | 显示当前选中路径，过长时省略 |
| cmb_history | 下拉选择历史路径，支持快速切换 |

**交互:**
- 点击 btn_select_file → 调用 `file_utils.select_server_file()` → 更新 lbl_server_path → 触发 `on_path_changed`
- 切换 cmb_history → 更新 lbl_server_path → 触发 `on_path_changed`

#### TemplateRow
| 控件 | 说明 |
|------|------|
| cmb_template | 下拉选择预设模板（最小配置/GPU加速/全功能） |
| btn_load_template | 将选中模板的参数加载到表格 |
| btn_save_template | 保存当前配置覆盖选中模板 |
| btn_save_as_template | 弹出对话框输入模板名，保存为新模板 |

**交互:**
- 点击 btn_load_template → 调用 `param_service.get_template()` → 填充 ParamTable
- 点击 btn_save_template → 从 ParamTable 读取 → 调用 `param_service.save_template()`

#### ParamTable (ttk.Treeview)
| 列名 | 宽度 | 说明 | 可编辑 |
|------|------|------|--------|
| 参数名 | 100px | 如 -m, -c, --threads | 是 |
| 值 | 200px | 参数值 | 是 |
| 分类 | 80px | model/context/gpu/network/other | 下拉选择 |
| 必填 | 50px | ✓ / 空 | 复选框 |
| 操作 | 80px | [删除] 按钮 | - |

**交互:**
- 双击单元格 → 进入编辑模式
- 编辑完成后按 Enter → 更新对应 Parameter 对象 → 触发命令预览更新
- 点击 [删除] → 删除对应行 → 触发命令预览更新
- 底部 "+ 添加参数" 按钮 → 插入空行

#### CmdPreviewRow
| 控件 | 说明 |
|------|------|
| lbl_cmd_preview | 显示拼接后的完整命令，如 `server -m model.gguf -c 4096` |
| btn_copy_cmd | 将命令复制到剪贴板 |

**交互:**
- 任何参数变化 → 调用 `param_service.build_command()` → 更新 lbl_cmd_preview
- 点击 btn_copy_cmd → `app.clipboard_append()` → 短暂显示"已复制"

**回调接口:**
```
on_file_selected(path: str)
on_history_selected(path: str)
on_load_template(name: str)
on_save_template(name: str)
on_save_as_template()
on_parameter_changed(params: list[Parameter])
on_command_copy()
```

### 3.3 SSHPanel

**职责**: 配置和管理 SSH 反向端口映射

**子组件:**

#### SSHConfigGrid (2列 grid 布局)
| 行 | 标签 | 输入控件 | 默认值 |
|----|------|---------|--------|
| 0 | 本地端口 | tk.Entry (int) | 8080 |
| 1 | 远程端口 | tk.Entry (int) | 8080 |
| 2 | 远程IP | tk.Entry (str) | 172.18.122.71 |
| 3 | 用户名 | tk.Entry (str) | root |

#### SSHStatusRow
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

#### SSHButtons
| 按钮 | 显示条件 |
|------|---------|
| 连接 | 未连接时可用 |
| 断开 | 已连接/连接中时可用 |

**回调接口:**
```
on_connect_clicked(cfg: SSHConfig)
on_disconnect_clicked()
update_status(state: SSHState)
```

### 3.4 LogPanel

**职责**: 显示运行日志

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
    → 从 ParamPanel 获取 LaunchConfig
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
    → param_service.build_command(current_params)
    → cmd_preview_label 更新为拼接命令
```

### 4.3 内存监控流程

```
monitor_service 后台线程 (每 3s)
    → psutil.virtual_memory()
    → 构建 MemoryStats
    → callback(memory_stats)
    → App.on_memory_update(memory_stats)
    → toolbar.update_memory_display(memory_stats)
        → memory_label 更新百分比
        → memory_progress 更新进度条
        → 超阈值 → 颜色变红
```

### 4.4 SSH 连接流程

```
用户点击"连接"
    → SSHPanel.btn_connect clicked
    → 读取 SSHConfig (从 Entry 控件)
    → App.on_connect_clicked(cfg)
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
| 文件对话框 | tk.filedialog (一致) | tk.filedialog (一致) |
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
