# Quick Release

Commodity Lab now publishes Windows desktop artifacts only.

## Official Release

```powershell
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

## Manual Workflow Run

Open GitHub Actions and run `Tauri Windows Build`.

Manual runs produce downloadable workflow artifacts. Tag pushes also publish a GitHub Release.

## Expected Assets

After the workflow succeeds, the GitHub Release should contain Windows Tauri bundle artifacts from:

```text
tauri\src-tauri\target\release\bundle\
```

Verify before publishing:

- Release tag and app package version match.
- Windows Publisher displays `Commodity Lab`.
- Installer/app signing status is documented. Public commercial builds should be signed with a trusted certificate.
