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

Before tagging, keep these versions aligned:

- `tauri/src-tauri/tauri.conf.json` package version
- `tauri/src-tauri/Cargo.toml` package version
- `tauri/package.json`
- `tauri/tauri-frontend/package.json`

Windows release metadata must identify the publisher as `Commodity Lab`.

## Local Windows Build

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1
```

The bundle is written under:

```text
tauri\src-tauri\target\release\bundle\
```

## Windows Signing

Current local builds are unsigned unless a valid Windows code-signing certificate is supplied to the build environment. Do not use a self-signed certificate for public distribution. For commercial distribution, sign both the app binary and installers with a trusted certificate and timestamp server.

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

