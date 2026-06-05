# Commodity Lab build and runtime guide

This guide records the operational path for local validation, Windows packaging, and GitHub Actions artifact delivery.

## Local validation

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r tauri/backend/requirements.txt
pytest -q
```

Frontend validation:

```powershell
cd tauri\tauri-frontend
npm ci
npm run test
npm run build
```

Rust/Tauri validation:

```powershell
cd tauri\src-tauri
cargo check
```

## Backend runtime configuration

The desktop shell starts the bundled Python backend automatically. These environment variables can override the default local backend endpoint when needed:

| Variable | Default | Purpose |
| --- | --- | --- |
| `COMMODITY_LAB_BACKEND_HOST` | `127.0.0.1` | Backend bind host. Keep loopback-only for desktop use. |
| `COMMODITY_LAB_BACKEND_PORT` | `8000` | Backend port. Change this if another local service already uses 8000. |

Health check endpoint:

```text
GET /api/health
```

Expected response:

```json
{"ok": true, "service": "commodity-lab-backend"}
```

## Local Windows packaging

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1
```

Dry run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1 -DryRun
```

Generated Windows bundles are written under:

```text
tauri\src-tauri\target\release\bundle\
```

## GitHub Actions artifact build

The workflow is:

```text
.github/workflows/tauri-build.yml
```

Manual build path:

```text
GitHub repo → Actions → Tauri Windows Build → Run workflow → main
```

The downloadable artifact is named:

```text
tauri-windows
```

Tag release path:

```powershell
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

Tag pushes build the Windows bundle and publish the resulting files into a GitHub Release.

## Current hardening decisions

- The backend exposes `/api/health` for Tauri startup readiness checks.
- The backend port is configurable to reduce local port conflicts.
- Tauri now waits briefly for backend readiness instead of immediately sending UI requests to a possibly unready service.
- The GitHub Actions workflow fails if no Windows bundle files are generated.
- The workflow caches pip, npm, and Cargo dependencies to reduce repeated build time.
- The workflow runs Python tests plus frontend tests/build before packaging.

## Recommended release gate

Before creating a tag, run or verify the following:

```powershell
pytest -q
cd tauri\tauri-frontend
npm ci
npm run test
npm run build
cd ..\src-tauri
cargo check
cd ..\..
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1 -DryRun
```

If all checks pass, create and push a semantic version tag.
