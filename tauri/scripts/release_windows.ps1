[CmdletBinding()]
param(
    [string]$Version = "",
    [switch]$DryRun,
    [switch]$AllowDirty,
    [switch]$SkipInstall,
    [switch]$SkipGithubRelease
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
$GuardrailSummary = "git status --porcelain | npm.cmd test -- --run | npm.cmd audit | gh release create"
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

$NotesPath = Join-Path $RepoRoot "build\release-notes-v$Version.md"
$Notes = @"
# Commodity Lab v$Version

## 中文
- 强化 AI 对训练工作台的可见控制：AI 修改图表、题目或策略后会留下动作日志。
- 新增策略腿与风险覆盖映射，帮助学员看清实货、纸货、基差、汇率和运力风险是否匹配。
- 增加 Windows 发布护栏：测试、审计、后端打包 freshness、安装包和 GitHub release notes 检查。

## English
- Adds a visible AI control log when the assistant changes charts, cases, or strategy legs.
- Adds a strategy-leg-to-risk coverage map for physical, paper, basis, FX, and capacity matching.
- Adds Windows release guardrails for tests, audits, backend freshness, installers, and GitHub release notes.
"@

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $NotesPath) | Out-Null
    $Notes | Out-File -Encoding utf8 -FilePath $NotesPath
}

if (-not $SkipInstall -and -not $DryRun) {
    Invoke-ReleaseStep "Install NSIS package locally" $NsisAsset.FullName @("/S")
}

if (-not $SkipGithubRelease) {
    $TagName = "v$Version"
    if ($DryRun) {
        Write-Host "==> GitHub release"
        Write-Host ("    gh release create {0} <assets> --title ""Commodity Lab v{1}"" --notes-file {2} --latest" -f $TagName, $Version, $NotesPath)
    }
    else {
        Invoke-ReleaseStep "Create GitHub release" "gh" @(
            "release", "create", $TagName,
            $NsisAsset.FullName,
            $MsiAsset.FullName,
            "--title", "Commodity Lab v$Version",
            "--notes-file", $NotesPath,
            "--latest"
        ) $RepoRoot
    }
}
