# llamacpp-panel

基于 Python 内置 Tkinter 开发的 llama.cpp 轻量可视化管理工具，无第三方 GUI 依赖、开箱即用。一站式实现 llama.cpp 启动文件选择、启动参数可视化配置、系统内存实时监控、服务异常自动重启、SSH 远程端口映射一键管理，大幅降低 llama.cpp 本地 / 远程部署、运行的操作门槛.

**语言切换**: [English](README.md) | [中文](README.zh.md)

## 功能特性

- **可视化选择可执行文件** — 文件对话框 + 历史记录
- **启动参数可视化配置** — 预设模板（最小配置/GPU加速/全功能）、命令预览完整显示、保存/加载
- **实时资源监控** — MEM/GPU/SERVER/SSH 4列等间隔布局，颜色状态指示器
- **服务异常自动重启** — 可配置重启次数、间隔时间、内存阈值
- **SSH 端口映射管理** — 反向 SSH 隧道、连接状态指示、服务器就绪后自动启动
- **模板含 SSH 配置** — 保存/加载模板时同步保存 SSH 连接参数
- **一键启动/停止** — 简单操作 + 实时日志输出
- **终端调试日志** — 详细日志同时写入文件 (log/YYYY-MM-DD.txt) 和控制台
- **配置持久化** — 自动保存/加载设置

## 安装

### 方式一：虚拟环境（推荐）

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 方式二：全局安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
python main.py
```

日志保存到 `log/YYYY-MM-DD.txt`，同时打印到终端。

## 测试

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

## 打包

```bash
pip install build
python -m build
```

## 架构

```
src/
├── models/        # 数据模型 (@dataclass)
├── services/      # 业务逻辑
├── ui/            # Tkinter 界面
└── utils/         # 工具函数
config/
├── app_config.json    # 保存的配置
└── templates/*.json   # 用户模板（含 SSH 配置）
log/
└── YYYY-MM-DD.txt     # 每日日志文件
```

详见 [docs/design/](docs/design/) 设计文档。

## 许可证

MIT License - 查看 [LICENSE](LICENSE)
