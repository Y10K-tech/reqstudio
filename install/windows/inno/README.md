# Windows Installer (Inno Setup)

This script builds a basic Windows installer that:

- Copies the ReqStudio repository into `%APPDATA%\ReqStudio`.
- Runs the PowerShell installer to create a virtualenv and install the project (`pip install .`).
- Creates Start Menu and Desktop shortcuts with the official icon.

Requirements:

- Inno Setup 6.x installed (https://jrsoftware.org/isinfo.php)
- Build from within the repository (paths assume this script is located under `install/windows/inno`).

Build steps:

1. Open `install/windows/inno/setup.iss` in Inno Setup.
2. Compile. The installer `reqstudio-setup.exe` is produced next to the script.

Notes:

- This installer expects Python 3.10+ on the user’s machine. The post-install script will create a `.venv` inside the installation directory and install dependencies.
- For a fully bundled installer (embedding Python), consider using PyInstaller to generate binaries and then package those artifacts with Inno Setup.
