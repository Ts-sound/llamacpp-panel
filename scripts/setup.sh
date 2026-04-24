# setup.sh
# Unix: Create virtual environment and install dependencies
# Usage: ./scripts/setup.sh

set -e

echo "=== Setting up llamacpp-panel ==="

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

python3 -m pip install --upgrade pip
pip install -r requirements.txt

echo "Done. Activate: source .venv/bin/activate"
