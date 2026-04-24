# setup-venv.ps1
# Windows: Create virtual environment and install dependencies
# Usage: .\scripts\setup-venv.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Setting up llamacpp-panel ===" -ForegroundColor Green

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Done. Activate: .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
