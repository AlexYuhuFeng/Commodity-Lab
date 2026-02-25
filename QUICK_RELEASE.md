# Quick Release (EXE + DMG)

## One-click automatic release

`build-and-release.yml` now automatically builds and publishes:
- Windows: `Commodity-Lab.exe` and `Commodity-Lab-windows-x64.zip`
- macOS: `Commodity-Lab-macos.dmg`

## Trigger methods

### 1) Official version release (recommended)
```bash
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

### 2) Nightly pre-release
Push to `main`, workflow updates `nightly-latest`.

### 3) Manual run
GitHub → **Actions** → **Build and Release** → **Run workflow**.

## Verify output
After workflow success, check GitHub Releases assets include:
- `Commodity-Lab.exe`
- `Commodity-Lab-windows-x64.zip`
- `Commodity-Lab-macos.dmg`
