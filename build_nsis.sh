#!/bin/bash
set -e

if ! command -v makensis >/dev/null 2>&1; then
    echo "NSIS is required to build the installer. Install makensis and retry."
    exit 1
fi

echo "✔ Building the exe package..."
bash build.sh --clean

if [ ! -f dist/Commodity-Lab.exe ]; then
    echo "Could not find dist/Commodity-Lab.exe. Ensure the build created the Windows executable."
    exit 1
fi

echo "✔ Building NSIS installer..."
makensis installer.nsi

echo "✔ Installer created: dist/HedgeLabInstaller.exe"
