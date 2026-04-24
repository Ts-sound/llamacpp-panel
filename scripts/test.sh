#!/bin/bash
set -e
echo "=== Running tests ==="
if [ -d "venv" ]; then
    source venv/bin/activate
fi
echo "Running pytest..."
pytest tests/ -v --cov=src --cov-report=term-missing
echo "Generating coverage report..."
coverage html
echo "Coverage report: htmlcov/index.html"
echo "=== Tests complete! ==="
