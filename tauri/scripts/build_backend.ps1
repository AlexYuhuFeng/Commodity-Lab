[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$OutDir = Join-Path $RepoRoot "tauri\bundled\backend"
$WorkPath = Join-Path $RepoRoot "build\pyinstaller"
$MainPath = Join-Path $RepoRoot "tauri\backend\main.py"

function Invoke-Step {
    param(
        [string]$Title,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $RepoRoot
    )

    Write-Host "==> $Title"
    if ($DryRun) {
        Write-Host ("    {0} {1}" -f $FilePath, ($Arguments -join " "))
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
Write-Host "Backend output: $OutDir"

if (-not $DryRun) {
    if (Test-Path $OutDir) {
        Remove-Item -LiteralPath $OutDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $OutDir, $WorkPath | Out-Null
}

if (-not $SkipInstall) {
    Invoke-Step "Upgrade pip" "python" @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-Step "Install Python build dependencies" "python" @(
        "-m", "pip", "install",
        "-r", (Join-Path $RepoRoot "requirements.txt"),
        "-r", (Join-Path $RepoRoot "tauri\backend\requirements.txt"),
        "pyinstaller"
    )
}

$HiddenImports = @(
    "core.db",
    "core.energy_models",
    "core.gas_scenarios",
    "core.haineng_client",
    "core.hedge",
    "core.learner_profile",
    "core.learning_journey",
    "core.learning_session",
    "core.market_learning",
    "core.platts_market",
    "core.scenario_registry",
    "core.training_templates"
)

$PyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--noconsole",
    "--name", "commodity_lab_backend",
    "--paths", $RepoRoot
)

foreach ($ModuleName in $HiddenImports) {
    $PyInstallerArgs += @("--hidden-import", $ModuleName)
}

$PyInstallerArgs += @(
    "--distpath", $OutDir,
    "--workpath", $WorkPath,
    "--specpath", $WorkPath,
    $MainPath
)

$OriginalPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = ""
    Invoke-Step "Build backend executable" "python" $PyInstallerArgs
}
finally {
    $env:PYTHONPATH = $OriginalPythonPath
}

$ExecutablePath = Join-Path $OutDir "commodity_lab_backend.exe"
if ((-not $DryRun) -and (-not (Test-Path $ExecutablePath))) {
    throw "Backend executable was not created at $ExecutablePath"
}
