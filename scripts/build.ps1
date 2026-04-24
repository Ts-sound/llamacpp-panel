# build.ps1
# Windows: Package as standalone executable
# Usage: .\scripts\build.ps1

$ErrorActionPreference = "Stop"

if (Test-Path ".venv") {
    & .\.venv\Scripts\Activate.ps1
}

# Install dependencies
pip install pyinstaller pillow -q

# Convert PNG to ICO if not exists
if (-not (Test-Path "llamacpp-panel.ico")) {
    Write-Host "Creating icon from PNG..." -ForegroundColor Yellow
    python -c "from PIL import Image; img = Image.open('llamacpp-panel.png'); sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]; icons = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]; icons[0].save('llamacpp-panel.ico', format='ICO', append_images=icons[1:])"
}

# Build using spec file
pyinstaller llamacpp-panel.spec --clean

Write-Host "Done: dist\llamacpp-panel.exe" -ForegroundColor Cyan
