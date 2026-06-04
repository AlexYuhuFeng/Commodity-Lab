# Commodity Lab Tauri Client

This directory contains the Commodity Lab Windows desktop client.

## Dev Run

Requirements: Rust toolchain, Node.js 20+, Python 3.12+.

1. Start the Python backend from the repository root:

```powershell
pip install -r requirements.txt -r tauri/backend/requirements.txt
python tauri/backend/main.py
```

2. Run Tauri from this directory:

```powershell
npm ci
npm run tauri:dev
```

## Windows Package

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1
```

The generated bundle is under `tauri\src-tauri\target\release\bundle\`.
