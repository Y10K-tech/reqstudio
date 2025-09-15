#!/usr/bin/env bash
set -euo pipefail

# Create a minimal macOS .app bundle that launches ReqStudio via the repo's .venv pythonw
# Requires: macOS, python installed via install/unix/install_reqstudio.sh

APP_NAME="ReqStudio"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUT_DIR="${SCRIPT_DIR}/out"
APP_DIR="${OUT_DIR}/${APP_NAME}.app"

mkdir -p "${APP_DIR}/Contents/MacOS" "${APP_DIR}/Contents/Resources"

# Info.plist
cat > "${APP_DIR}/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>${APP_NAME}</string>
  <key>CFBundleDisplayName</key><string>${APP_NAME}</string>
  <key>CFBundleIdentifier</key><string>com.y10k.reqstudio</string>
  <key>CFBundleVersion</key><string>0.1.0</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>CFBundleExecutable</key><string>${APP_NAME}</string>
  <key>LSMinimumSystemVersion</key><string>12.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST

# Launcher
cat > "${APP_DIR}/Contents/MacOS/${APP_NAME}" <<'LAUNCH'
#!/bin/bash
set -euo pipefail
ROOT="__REQSTUDIO_ROOT__"
VENV="$ROOT/.venv"
if [ ! -x "$VENV/bin/pythonw" ]; then
  echo "pythonw not found in $VENV. Run install/unix/install_reqstudio.sh first." >&2
  exit 1
fi
exec "$VENV/bin/pythonw" "$ROOT/app.py" "$@"
LAUNCH
chmod +x "${APP_DIR}/Contents/MacOS/${APP_NAME}"
sed -i.bak "s#__REQSTUDIO_ROOT__#${REPO_ROOT//\//\/}#g" "${APP_DIR}/Contents/MacOS/${APP_NAME}" && rm -f "${APP_DIR}/Contents/MacOS/${APP_NAME}.bak"

# Icon (optional): convert PNG to icns if tools available
PNG="${REPO_ROOT}/media/reqstudio_logo.png"
ICONSET_DIR="${OUT_DIR}/icon.iconset"
ICNS_OUT="${APP_DIR}/Contents/Resources/AppIcon.icns"
if [ -f "$PNG" ] && command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
  mkdir -p "$ICONSET_DIR"
  for sz in 16 32 64 128 256 512; do
    sips -z $sz $sz "$PNG" --out "$ICONSET_DIR/icon_${sz}x${sz}.png" >/dev/null
  done
  iconutil -c icns -o "$ICNS_OUT" "$ICONSET_DIR" || true
  rm -rf "$ICONSET_DIR"
  echo "[reqstudio] Set app icon at: $ICNS_OUT"
else
  echo "[reqstudio] Icon conversion skipped (missing tools or PNG)."
fi

echo "[reqstudio] Created app bundle: $APP_DIR"
