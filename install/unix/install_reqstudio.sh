#!/usr/bin/env bash
set -euo pipefail

# ReqStudio installer for Linux/macOS
# - Creates a virtualenv in the repo (.venv) and installs the project via pyproject.toml
# - Creates a launcher at ~/.local/bin/reqstudio (or custom via --bin-dir)
# - Optionally creates a .desktop entry on Linux (toggle via env CREATE_DESKTOP_ENTRY=1)

usage() {
  cat <<EOF
ReqStudio installer (Linux/macOS)

Usage:
  $(basename "$0") [--bin-dir PATH] [--venv-path PATH]

Options:
  --bin-dir PATH     Directory to place launcher (default: ~/.local/bin)
  --venv-path PATH   Virtualenv path (default: <repo>/.venv)

Environment:
  CREATE_DESKTOP_ENTRY=1  Create a desktop entry on Linux (default: off)
EOF
}

BIN_DIR="${HOME}/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_PATH="${REPO_ROOT}/.venv"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bin-dir) BIN_DIR="$2"; shift 2 ;;
    --venv-path) VENV_PATH="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

echo "[reqstudio] Repo root: ${REPO_ROOT}"
echo "[reqstudio] Using venv: ${VENV_PATH}"
echo "[reqstudio] Launcher dir: ${BIN_DIR}"

ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    return 0
  fi
  echo "[reqstudio] Python 3 not found. Attempting headless installation..."
  # Detect OS / package manager
  if [ "$(uname)" = "Darwin" ]; then
    if ! command -v brew >/dev/null 2>&1; then
      echo "[reqstudio] Homebrew not found. Installing Homebrew headlessly..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      # Add brew to path for Apple Silicon/Intel
      if [ -d "/opt/homebrew/bin" ]; then export PATH="/opt/homebrew/bin:$PATH"; fi
      if [ -d "/usr/local/bin" ]; then export PATH="/usr/local/bin:$PATH"; fi
    fi
    brew update
    brew install python
  else
    if [ -r /etc/os-release ]; then
      . /etc/os-release
    fi
    # Try apt, dnf, yum, pacman, zypper in order
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update -y
      sudo apt-get install -y python3 python3-venv python3-pip curl
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y python3 python3-pip
    elif command -v yum >/dev/null 2>&1; then
      sudo yum install -y python3 python3-pip
    elif command -v pacman >/dev/null 2>&1; then
      sudo pacman -Sy --noconfirm python
    elif command -v zypper >/dev/null 2>&1; then
      sudo zypper --non-interactive install python3 python3-pip || sudo zypper --non-interactive install python311
    else
      echo "[reqstudio] Unsupported package manager. Please install Python 3.10+ manually and re-run." >&2
      exit 1
    fi
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "[reqstudio] Failed to install Python automatically." >&2
    exit 1
  fi
}

ensure_python

ensure_git() {
  if command -v git >/dev/null 2>&1; then
    return 0
  fi
  echo "[reqstudio] Git not found. Attempting headless installation..."
  if [ "$(uname)" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
      brew install git
    else
      echo "[reqstudio] Homebrew not found; installing..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      if [ -d "/opt/homebrew/bin" ]; then export PATH="/opt/homebrew/bin:$PATH"; fi
      if [ -d "/usr/local/bin" ]; then export PATH="/usr/local/bin:$PATH"; fi
      brew install git
    fi
  else
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update -y && sudo apt-get install -y git
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y git
    elif command -v yum >/dev/null 2>&1; then
      sudo yum install -y git
    elif command -v pacman >/dev/null 2>&1; then
      sudo pacman -Sy --noconfirm git
    elif command -v zypper >/dev/null 2>&1; then
      sudo zypper --non-interactive install git
    else
      echo "[reqstudio] Unsupported package manager. Please install Git and re-run." >&2
      exit 1
    fi
  fi
}

ensure_git

# Check Python version >= 3.10
pyver=$(python3 -c 'import sys; print("%d.%d"%sys.version_info[:2])')
req_major=3; req_minor=10
cur_major=$(echo "$pyver" | cut -d. -f1)
cur_minor=$(echo "$pyver" | cut -d. -f2)
if [ "$cur_major" -lt "$req_major" ] || { [ "$cur_major" -eq "$req_major" ] && [ "$cur_minor" -lt "$req_minor" ]; }; then
  echo "[reqstudio] Python $pyver found; attempting to install a newer Python (>=3.10)..."
  if [ "$(uname)" = "Darwin" ]; then
    brew update && brew upgrade python || true
  else
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update -y
      sudo apt-get install -y python3 python3-venv python3-pip
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf upgrade -y python3 || true
    elif command -v yum >/dev/null 2>&1; then
      sudo yum update -y python3 || true
    elif command -v pacman >/dev/null 2>&1; then
      sudo pacman -Syu --noconfirm python || true
    elif command -v zypper >/dev/null 2>&1; then
      sudo zypper --non-interactive install python311 || true
    fi
  fi
  pyver=$(python3 -c 'import sys; print("%d.%d"%sys.version_info[:2])')
  cur_major=$(echo "$pyver" | cut -d. -f1)
  cur_minor=$(echo "$pyver" | cut -d. -f2)
  if [ "$cur_major" -lt "$req_major" ] || { [ "$cur_major" -eq "$req_major" ] && [ "$cur_minor" -lt "$req_minor" ]; }; then
    echo "[reqstudio] Still on Python $pyver. Please install Python >= 3.10 and re-run." >&2
    exit 1
  fi
fi

# Create venv if missing
if [ ! -d "$VENV_PATH" ]; then
  echo "[reqstudio] Creating virtualenv..."
  python3 -m venv "$VENV_PATH"
fi

"$VENV_PATH/bin/python" -m pip install --upgrade pip
echo "[reqstudio] Installing project via pyproject.toml..."
"$VENV_PATH/bin/python" -m pip install "$REPO_ROOT"

# Create launcher
mkdir -p "$BIN_DIR"
LAUNCHER="$BIN_DIR/reqstudio"
cat > "$LAUNCHER" <<'LAUNCH'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_HINT="__REQSTUDIO_ROOT__"
VENV_PATH="$ROOT_HINT/.venv"
exec "$VENV_PATH/bin/python" "$ROOT_HINT/app.py" "$@"
LAUNCH

# Replace placeholder with actual repo root path
sed -i.bak "s#__REQSTUDIO_ROOT__#${REPO_ROOT//\//\/}#g" "$LAUNCHER" && rm -f "$LAUNCHER.bak"
chmod +x "$LAUNCHER"
echo "[reqstudio] Installed launcher: $LAUNCHER"

# Optional: desktop entry (Linux/XDG)
if [ "${CREATE_DESKTOP_ENTRY:-0}" = "1" ] && command -v xdg-mime >/dev/null 2>&1; then
  APPS_DIR="${HOME}/.local/share/applications"
  mkdir -p "$APPS_DIR"
  DESKTOP_FILE="$APPS_DIR/reqstudio.desktop"
  cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=ReqStudio
Comment=Git-driven requirements/SRS editor
Exec=${LAUNCHER}
Terminal=false
Type=Application
Categories=Development;Utility;
Icon=${REPO_ROOT}/media/reqstudio_logo.ico
EOF
  echo "[reqstudio] Desktop entry created: $DESKTOP_FILE"
fi

echo "[reqstudio] Done. Run: reqstudio"
