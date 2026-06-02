# Build and Release Guide

## CI/CD workflow (Tauri)

The project has migrated from a PyInstaller-based desktop to a Tauri-based native desktop with a bundled Python backend. The new CI workflow is `.github/workflows/tauri-build.yml`.

### What it does
1. Runs tests (`pytest -q`).
2. Builds the Python backend executable with PyInstaller (packaged into the Tauri bundle).
3. Builds the frontend (Vite) and runs `tauri build` for platform bundles (Linux/Windows).
4. Publishes artifacts to GitHub Releases when a tag is pushed.

### Release steps
```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

### Local build (dev)
Start backend and frontend separately for development:

```bash
# Start Python backend
python tauri/backend/main.py

# Start frontend dev server (in another terminal)
cd tauri/tauri-frontend
npm install
npm run dev

# Or run Tauri dev from `tauri/` (requires Node + Rust):
cd tauri
npm install
npm run tauri:dev
```

### Expected release artifacts
- Tauri platform bundles (installer, AppImage, MSI, etc.) under `src-tauri/target/release/bundle/`

