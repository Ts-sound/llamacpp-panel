# llamacpp-panel

Lightweight GUI management tool for llama.cpp, built with Python Tkinter, zero third-party GUI dependencies.

**Language**: [English](README.md) | [中文](README.zh.md)

## Features

- **Visual Executable Selection** — File dialog with history for selecting llama.cpp server binary
- **Parameter Configuration** — Visual parameter editor with preset templates (Minimum/GPU/Full), command preview, and save/load
- **Real-time Memory Monitoring** — System RAM and optional GPU monitoring with configurable threshold alerts
- **Automatic Restart** — Auto-restart on process crash or memory threshold, with configurable max restart count
- **SSH Port Mapping** — One-click reverse SSH tunnel management with status indicator
- **One-click Start/Stop** — Simple start/stop/restart controls with real-time log output
- **Persistent Configuration** — Auto-save/load settings across sessions

## Installation

### Option 1: Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Global Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

## Building

```bash
pip install build
python -m build
```

## Architecture

```
src/
├── models/        # Data models (@dataclass)
├── services/      # Business logic
├── ui/            # Tkinter interface
└── utils/         # Utilities
```

See [docs/design/](docs/design/) for detailed design documents.

## License

MIT License - See [LICENSE](LICENSE)
