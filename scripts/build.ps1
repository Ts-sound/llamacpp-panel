# llamacpp-panel build script
# Package Windows EXE with icon (no console window)

pip install pyinstaller
pyinstaller -F -w -n llamacpp-panel --icon=llamacpp-panel.ico main.py

Write-Host "Done: dist\llamacpp-panel.exe"
