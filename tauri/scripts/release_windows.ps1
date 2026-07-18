[CmdletBinding()]
param(
    [string]$Version = "",
    [switch]$DryRun,
    [switch]$AllowDirty,
    [switch]$SkipInstall,
    [Alias("SkipGithubRelease")]
    [switch]$SkipReleaseTag
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$FrontendDir = Join-Path $RepoRoot "tauri\tauri-frontend"
$TauriDir = Join-Path $RepoRoot "tauri"
$BackendExe = Join-Path $RepoRoot "tauri\bundled\backend\commodity_lab_backend.exe"
$BundleRoot = Join-Path $RepoRoot "tauri\src-tauri\target\release\bundle"

function Invoke-ReleaseStep {
    param(
        [string]$Title,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $RepoRoot
    )

    Write-Host "==> $Title"
    Write-Host ("    cd {0}" -f $WorkingDirectory)
    Write-Host ("    {0} {1}" -f $FilePath, ($Arguments -join " "))
    if ($DryRun) {
        return
    }

    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$Title failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

if (-not $Version) {
    $PackageJson = Get-Content -Raw (Join-Path $TauriDir "package.json") | ConvertFrom-Json
    $Version = [string]$PackageJson.version
}

Write-Host "Repository: $RepoRoot"
Write-Host "Release version: $Version"
$GuardrailSummary = "git status --porcelain | npm.cmd test -- --run | npm.cmd audit | package_tauri.ps1 | git push origin v$Version"
Write-Host "Guardrails: $GuardrailSummary"

if (-not $AllowDirty) {
    Push-Location $RepoRoot
    try {
        $Dirty = & git status --porcelain
        if ($Dirty) {
            throw "Working tree is not clean. Commit or stash changes, or pass -AllowDirty for a dry local package."
        }
    }
    finally {
        Pop-Location
    }
}

Invoke-ReleaseStep "Frontend unit tests" "npm.cmd" @("test", "--", "--run") $FrontendDir
Invoke-ReleaseStep "Python unit tests" "python" @("-m", "pytest", "-q") $RepoRoot
Invoke-ReleaseStep "Frontend build" "npm.cmd" @("run", "build") $FrontendDir
Invoke-ReleaseStep "Frontend audit" "npm.cmd" @("audit", "--audit-level=moderate") $FrontendDir
Invoke-ReleaseStep "Tauri audit" "npm.cmd" @("audit", "--audit-level=moderate") $TauriDir

$PackageArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $ScriptDir "package_tauri.ps1"), "-SkipPythonInstall")
Invoke-ReleaseStep "Build Windows client bundle" "powershell" $PackageArgs $RepoRoot

if (-not $DryRun) {
    if (-not (Test-Path $BackendExe)) {
        throw "Missing backend executable: $BackendExe"
    }
    $BackendBuiltAt = (Get-Item $BackendExe).LastWriteTimeUtc
    $BackendSources = @(
        Get-Item (Join-Path $RepoRoot "tauri\backend\main.py")
        Get-ChildItem (Join-Path $RepoRoot "core") -Filter "*.py" -Recurse
    )
    $NewestBackendSource = ($BackendSources | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc
    if ($BackendBuiltAt -lt $NewestBackendSource) {
        throw "Backend executable is older than backend source files. Re-run package_tauri.ps1."
    }
}

$NsisAsset = Get-ChildItem (Join-Path $BundleRoot "nsis") -Filter "*$Version*x64-setup.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
$MsiAsset = Get-ChildItem (Join-Path $BundleRoot "msi") -Filter "*$Version*x64*.msi" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $DryRun -and (-not $NsisAsset -or -not $MsiAsset)) {
    throw "Release assets for $Version were not found under $BundleRoot."
}

if (-not $SkipInstall -and -not $DryRun) {
    Invoke-ReleaseStep "Install NSIS package locally" $NsisAsset.FullName @("/S")
}

if (-not $SkipReleaseTag) {
    $TagName = "v$Version"
    if ($DryRun) {
        Write-Host "==> Trigger cross-platform release"
        Write-Host "    git tag -a $TagName -m 'Commodity Lab $TagName'"
        Write-Host "    git push origin $TagName"
    }
    else {
        Push-Location $RepoRoot
        try {
            $CurrentBranch = (& git branch --show-current).Trim()
            if ($CurrentBranch -ne "main") {
                throw "Formal cross-platform tags must be created from main; current branch is '$CurrentBranch'."
            }
            & git rev-parse --verify --quiet "refs/tags/$TagName" | Out-Null
            if ($LASTEXITCODE -eq 0) {
                throw "Tag $TagName already exists locally."
            }
        }
        finally {
            Pop-Location
        }
        Invoke-ReleaseStep "Create annotated release tag" "git" @("tag", "-a", $TagName, "-m", "Commodity Lab $TagName") $RepoRoot
        Invoke-ReleaseStep "Push tag for cross-platform CI" "git" @("push", "origin", $TagName) $RepoRoot
    }
}
