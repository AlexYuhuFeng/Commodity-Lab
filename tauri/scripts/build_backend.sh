#!/bin/bash
set -e
echo "Build backend into a single executable (PyInstaller)"
python -m pip install --upgrade pip
pip install -r tauri/backend/requirements.txt
pip install pyinstaller
OUTDIR="tauri/bundled/backend"
mkdir -p "$OUTDIR"
pyinstaller --onefile --name commodity_lab_backend --distpath "$OUTDIR" tauri/backend/main.py
echo "Built: $OUTDIR/commodity_lab_backend"
