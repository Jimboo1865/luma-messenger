#!/bin/bash
# Build Luma Messenger.app and zip it for a GitHub release (Homebrew cask).
# Run on the Mac from this folder:  bash build-app.sh
# Output: dist/"Luma Messenger.app" and Luma-Messenger-<version>-macOS.zip
set -euo pipefail
cd "$(dirname "$0")"

VERSION="${1:-0.1.0}"
APP_NAME="Luma Messenger"
ZIP_NAME="Luma-Messenger-${VERSION}-macOS.zip"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt pyinstaller

.venv/bin/pyinstaller \
  --windowed \
  --name "$APP_NAME" \
  --osx-bundle-identifier com.jamesnovak.lumamessenger \
  --noconfirm --clean \
  main.py

rm -f "$ZIP_NAME"
ditto -c -k --keepParent "dist/$APP_NAME.app" "$ZIP_NAME"

echo "Built: dist/$APP_NAME.app"
echo "Zipped: $ZIP_NAME"
shasum -a 256 "$ZIP_NAME"
