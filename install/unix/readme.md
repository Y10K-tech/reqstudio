# Unix/macOS Installation

Scripts:

- `install_reqstudio.sh` — installs ReqStudio into a Python virtualenv and adds a launcher to `~/.local/bin/reqstudio`.
- `uninstall_reqstudio.sh` — removes the launcher and the created virtualenv.

Usage:

```
chmod +x install_reqstudio.sh uninstall_reqstudio.sh
./install_reqstudio.sh

# Options
./install_reqstudio.sh --bin-dir ~/.local/bin --venv-path /path/to/.venv

# Run
reqstudio

# Uninstall
./uninstall_reqstudio.sh
```

Notes:

- The installer checks for Python 3 and will attempt a headless install if missing, using your package manager (`apt`, `dnf/yum`, `pacman`, `zypper`) or Homebrew on macOS. If it cannot install automatically, it exits with guidance.
- Requires Git available in PATH.
- On Linux, set `CREATE_DESKTOP_ENTRY=1` to create a `.desktop` entry under `~/.local/share/applications`.
