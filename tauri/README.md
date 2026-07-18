# Commodity Lab Tauri Client

This directory contains the Commodity Lab Windows and Linux desktop client.

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

## Desktop Packages

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1
```

The generated Windows bundle is under `tauri\src-tauri\target\release\bundle\`. Linux x86_64 and ARM64 `.deb` and `.AppImage` packages are built natively by `.github/workflows/tauri-build.yml`.

For a formal public release, use the guarded script from a clean `main` checkout:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\release_windows.ps1 -Version 1.5.1
```

It runs tests, npm audit, backend rebuild freshness checks, Windows packaging, and local install, then pushes a `v*.*.*` tag. The tag starts the cross-platform workflow, which publishes Windows x86_64, Linux x86_64, and Linux ARM64 assets to one GitHub release. Pass `-SkipReleaseTag` to stop after local Windows qualification.
