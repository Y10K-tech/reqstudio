# Windows — Self-contained Build (PyInstaller)

This produces a standalone `ReqStudio.exe` that bundles Python and dependencies.

Requirements:

- Windows 10/11
- Python 3.10+ (build-time)

Build steps (from repo root):

```
python -m venv .venv
. .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install .
python -m pip install pyinstaller

# Build
powershell -ExecutionPolicy Bypass -File install\windows\pyinstaller\build_pyinstaller.ps1

# Output
dist\ReqStudio\ReqStudio.exe
```

Notes:

- The spec includes PyQt6; adjust hidden imports if needed.
- If assets are missing at runtime, add them in the `--add-data` list.
