# build.ps1 - 本地构建脚本 (Windows)
# 使用方式: .\build.ps1

param(
    [switch]$Clean = $false,
    [switch]$Windowed = $true,
    [switch]$OneFile = $true,
    [string]$OutputDir = "dist"
)

$ErrorActionPreference = "Stop"

Write-Host "🔨 Commodity Lab 构建脚本" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "🐍 检查Python环境..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ 未找到Python！请确保Python已安装并添加到PATH"
    exit 1
}
Write-Host "✅ $pythonVersion" -ForegroundColor Green
Write-Host ""

# 检查虚拟环境
Write-Host "📦 检查虚拟环境..." -ForegroundColor Yellow
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "⚠️  虚拟环境不存在，正在创建..." -ForegroundColor Yellow
    python -m venv venv
}
& ".\venv\Scripts\Activate.ps1"
Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
Write-Host ""

# 安装依赖
Write-Host "📚 安装依赖..." -ForegroundColor Yellow
pip install --upgrade pip setuptools wheel | Out-Null
pip install -r requirements.txt | Out-Null
pip install pyinstaller | Out-Null
Write-Host "✅ 依赖安装完成" -ForegroundColor Green
Write-Host ""

# 清理旧的构建
if ($Clean -or (Test-Path "build") -or (Test-Path $OutputDir)) {
    Write-Host "🧹 清理旧的构建文件..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path $OutputDir) { Remove-Item -Recurse -Force $OutputDir }
    if (Test-Path "*.spec") { Remove-Item -Force "*.spec" 2>$NULL }
    Write-Host "✅ 清理完成" -ForegroundColor Green
    Write-Host ""
}

# 构建参数
$buildArgs = @(
    "--distpath", $OutputDir,
    "--workpath", "build",
    "--specpath", ".",
    "-y"  # 覆盖已存在的文件
)

if ($OneFile) {
    $buildArgs += "--onefile"
}

if ($Windowed) {
    $buildArgs += "--windowed"
}

# 添加数据文件
$buildArgs += "--add-data", "app:app"
$buildArgs += "--add-data", "core:core"
$buildArgs += "--add-data", "data:data"

# 添加隐藏导入
$hiddenImports = @(
    "streamlit",
    "streamlit.web",
    "duckdb",
    "pandas",
    "plotly",
    "yfinance",
)

foreach ($module in $hiddenImports) {
    $buildArgs += "--hidden-import=$module"
}

# 设置图标（如果存在）
if (Test-Path "app\assets\icon.ico") {
    $buildArgs += "--icon", "app\assets\icon.ico"
}

# 执行构建
Write-Host "🏗️ 开始构建..." -ForegroundColor Cyan
Write-Host "命令: pyinstaller $($buildArgs -join ' ') app\main.py" -ForegroundColor Gray
Write-Host ""

try {
    & python -m PyInstaller @buildArgs "app\main.py"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Green
        Write-Host "✅ 构建成功！" -ForegroundColor Green
        Write-Host "=" * 60 -ForegroundColor Green
        Write-Host ""
        
        # 列出输出文件
        $exePath = Join-Path $OutputDir "Commodity-Lab.exe"
        if (Test-Path $exePath) {
            $fileInfo = Get-Item $exePath
            Write-Host "📦 可执行文件:" -ForegroundColor Cyan
            Write-Host "   路径: $exePath" -ForegroundColor Yellow
            Write-Host "   大小: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "🚀 运行应用:" -ForegroundColor Cyan
            Write-Host "   & '.\$exePath'" -ForegroundColor Yellow
            Write-Host ""
        }
        
        # 显示文件列表
        Write-Host "📂 输出目录内容:" -ForegroundColor Cyan
        Get-ChildItem $OutputDir -Recurse | 
            Where-Object { $_.PSIsContainer -eq $false } |
            Select-Object @{N="文件";E={$_.Name}}, @{N="大小(MB)";E={[math]::Round($_.Length / 1MB, 2)}} |
            Format-Table -AutoSize
        
    } else {
        Write-Error "❌ 构建失败！请检查错误信息"
        exit 1
    }
} catch {
    Write-Error "❌ 执行错误: $_"
    exit 1
}

Write-Host ""
Write-Host "构建完成！" -ForegroundColor Green
