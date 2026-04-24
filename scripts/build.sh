#!/bin/bash
set -e
echo "=== Building llamacpp-panel ==="
if [ -d "venv" ]; then
    source venv/bin/activate
fi
echo "Building..."
if [ -f "pyproject.toml" ]; then
    python -m build
    echo "Build complete! Check dist/"
else
    echo "No pyproject.toml found."
    exit 1
fi
echo "=== Build complete! ==="
