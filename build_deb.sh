#!/bin/bash
set -e

APP_NAME="Commodity-Lab"
PACKAGE_NAME="commodity-lab"
OUTPUT_DIR="dist"
BUILD_DIR="build_deb"
PKG_ROOT="pkgroot"
VERSION="${VERSION:-0.9.0-preview}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required."
  exit 1
fi

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb is required to build the Debian package."
  exit 1
fi

if [ "$1" == "--clean" ]; then
  rm -rf "$OUTPUT_DIR" "$BUILD_DIR" "$PKG_ROOT" *.spec
fi

mkdir -p "$OUTPUT_DIR"

python3 -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --onefile --name "$APP_NAME" \
  --distpath "$OUTPUT_DIR" \
  --workpath "$BUILD_DIR" \
  --specpath "." \
  -y app/desktop_launcher.py

BIN_PATH="$OUTPUT_DIR/$APP_NAME"
if [ ! -f "$BIN_PATH" ]; then
  echo "Build failed: $BIN_PATH not found."
  exit 1
fi

rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/usr/local/bin"
mkdir -p "$PKG_ROOT/DEBIAN"
cp "$BIN_PATH" "$PKG_ROOT/usr/local/bin/$PACKAGE_NAME"
chmod 755 "$PKG_ROOT/usr/local/bin/$PACKAGE_NAME"

cat > "$PKG_ROOT/DEBIAN/control" <<EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Depends: libc6 (>= 2.34)
Maintainer: Commodity Lab <internal@commodity-lab.local>
Description: Hedge Lab Terminal — internal commodity hedge learning workspace.
EOF

fakeroot dpkg-deb --build "$PKG_ROOT" "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_amd64.deb"

echo "Built Linux package: $OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_amd64.deb"
