[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$SkipTauriBuild,
    [switch]$SkipPythonInstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

function Invoke-Step {
    param(
        [string]$Title,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $RepoRoot
    )

    Write-Host "==> $Title"
    if ($DryRun) {
        Write-Host ("    (cd {0}; {1} {2})" -f $WorkingDirectory, $FilePath, ($Arguments -join " "))
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

Write-Host "Repository: $RepoRoot"

if (-not $SkipBackend) {
    $BackendArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $ScriptDir "build_backend.ps1"))
    if ($DryRun) {
        $BackendArgs += "-DryRun"
    }
    if ($SkipPythonInstall) {
        $BackendArgs += "-SkipInstall"
    }
    Invoke-Step "Build Python backend" "powershell" $BackendArgs
}

if (-not $SkipFrontend) {
    Invoke-Step "Install frontend dependencies" "npm" @("ci") (Join-Path $RepoRoot "tauri\tauri-frontend")
    Invoke-Step "Build frontend assets" "npm" @("run", "build") (Join-Path $RepoRoot "tauri\tauri-frontend")
}

if (-not $SkipTauriBuild) {
    Invoke-Step "Install Tauri dependencies" "npm" @("ci") (Join-Path $RepoRoot "tauri")
    Invoke-Step "Build desktop bundle" "npm" @("run", "tauri:build") (Join-Path $RepoRoot "tauri")
}
