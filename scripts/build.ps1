# build.ps1
# Windows: Package as standalone executable
# Usage: .\scripts\build.ps1

$ErrorActionPreference = "Stop"

if (Test-Path ".venv") {
    & .\.venv\Scripts\Activate.ps1
}

pip install pyinstaller
pyinstaller --name "llamacpp-panel" --onefile --windowed main.py --clean

Write-Host "Done: dist\llamacpp-panel.exe" -ForegroundColor Cyan
