# Build and Release Guide

## CI/CD workflow

Workflow file: `.github/workflows/build-and-release.yml`

### What it does
1. Runs tests (`pytest -q`) on Ubuntu.
2. Builds with PyInstaller on:
   - Windows → `Commodity-Lab.exe`
   - macOS → `Commodity-Lab` binary
3. Packages release artifacts:
   - Windows: `.exe` + `.zip`
   - macOS: `.dmg`
4. Publishes to GitHub Releases:
   - tag `v*.*.*` → versioned release
   - push to `main` → rolling prerelease `nightly-latest`

## Release steps

### Stable release
```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

### Nightly release
```bash
git push origin main
```

## Local build (optional)

### Windows
```powershell
.\build.ps1 -Clean
```

### macOS/Linux
```bash
./build.sh --clean
```

## Expected release assets
- `Commodity-Lab.exe`
- `Commodity-Lab-windows-x64.zip`
- `Commodity-Lab-macos.dmg`
