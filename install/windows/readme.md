# Windows Installation

Scripts:

- `install_reqstudio.ps1` — sets up a virtualenv, installs the project, and creates Start Menu and Desktop shortcuts.
- `uninstall_reqstudio.ps1` — removes shortcuts and optionally deletes the virtualenv.

Usage:

```
powershell -ExecutionPolicy Bypass -File install_reqstudio.ps1

# Options
powershell -ExecutionPolicy Bypass -File install_reqstudio.ps1 -VenvPath C:\\path\\to\\venv -CreateDesktop

# Uninstall (keep venv)
powershell -ExecutionPolicy Bypass -File uninstall_reqstudio.ps1 -KeepVenv
```

Notes:

- If Python is not found, the installer attempts a headless install using (in order): `winget`, `choco`, then the official python.org silent installer (3.11.x). After installation, it sets up a venv and installs ReqStudio via `pyproject.toml`.
- Requires Git in PATH.
- Shortcuts launch `pythonw.exe` with `app.py` as the entry point.
