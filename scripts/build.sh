# build.sh
# Unix: Package as standalone executable
# Usage: ./scripts/build.sh

set -e

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

pip install pyinstaller
pyinstaller --name "llamacpp-panel" --onefile --windowed main.py --clean

echo "Done: dist/llamacpp-panel"
