# Build and Release Guide

Commodity Lab releases Windows desktop clients only.

## GitHub Workflow

The release workflow is `.github/workflows/tauri-build.yml`.

It runs:

1. Python tests with `pytest -q`.
2. Windows backend bundling with PyInstaller.
3. Frontend build with Vite.
4. Tauri Windows bundle generation.
5. GitHub Release upload for tag builds.

## Release

```powershell
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

## Local Windows Build

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1
```

The bundle is written under:

```text
tauri\src-tauri\target\release\bundle\
```

## Development Run

```powershell
python tauri/backend/main.py
```

In another terminal:

```powershell
cd tauri\tauri-frontend
npm ci
npm run dev
```

Or run the Tauri dev shell:

```powershell
cd tauri
npm ci
npm run tauri:dev
```

