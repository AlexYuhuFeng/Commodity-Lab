# Commodity Lab Packaging Guide

Commodity Lab packaging is Windows-only for V1.

## Recommended Path

Use the GitHub Actions workflow:

```text
.github/workflows/tauri-build.yml
```

The workflow builds and uploads Windows Tauri bundle artifacts when a version tag is pushed or the workflow is run manually.

## Local Windows Build

Requirements:

- Python 3.12+
- Node.js 20+
- Rust stable
- Windows build dependencies required by Tauri

Run from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1
```

Useful dry run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1 -DryRun
```

## Output

Tauri writes generated Windows bundles under:

```text
tauri\src-tauri\target\release\bundle\
```

## Notes

- Do not commit 海能, Platts, or Yahoo Finance credentials.
- The UI labels data sources as `Platts`, `Yahoo Finance`, or `Simulated`.
- The app name is Commodity Lab.
