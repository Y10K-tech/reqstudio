#!/usr/bin/env bash
set -euo pipefail

# Uninstall ReqStudio venv and launcher created by install_reqstudio.sh

usage(){ cat <<EOF
Usage: $(basename "$0") [--bin-dir PATH] [--venv-path PATH]
Defaults match install script: bin-dir=~/.local/bin, venv-path=<repo>/.venv
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

LAUNCHER="$BIN_DIR/reqstudio"

if [ -f "$LAUNCHER" ]; then
  rm -f "$LAUNCHER"
  echo "[reqstudio] Removed launcher: $LAUNCHER"
fi

if [ -d "$VENV_PATH" ]; then
  rm -rf "$VENV_PATH"
  echo "[reqstudio] Removed virtualenv: $VENV_PATH"
fi

# Remove desktop entry on Linux
APPS_FILE="${HOME}/.local/share/applications/reqstudio.desktop"
if [ -f "$APPS_FILE" ]; then
  rm -f "$APPS_FILE"
  echo "[reqstudio] Removed desktop entry: $APPS_FILE"
fi

echo "[reqstudio] Uninstall complete."
