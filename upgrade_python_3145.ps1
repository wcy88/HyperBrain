# HyperBrain Python 3.14.5 升级脚本
# 自动下载并安装最新稳定版Python 3.14.5 (64位)

$ErrorActionPreference = "Stop"
$PythonUrl = "https://www.python.org/ftp/python/3.14.5/python-3.14.5-amd64.exe"
$InstallerPath = "$PSScriptRoot\python-3.14.5-amd64.exe"
$InstallDir = "E:\software\python314"
$ProjectDir = "$PSScriptRoot"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HyperBrain Python 3.14.5 升级工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 下载Python 3.14.5
Write-Host "[1/6] 正在下载 Python 3.14.5 (64位)..." -ForegroundColor Yellow
if (Test-Path $InstallerPath) {
    Write-Host "      安装程序已存在，跳过下载" -ForegroundColor Green
} else {
    try {
        Invoke-WebRequest -Uri $PythonUrl -OutFile $InstallerPath -UseBasicParsing -TimeoutSec 120
        Write-Host "      下载完成!" -ForegroundColor Green
    } catch {
        Write-Host "      下载失败: $_" -ForegroundColor Red
        Write-Host "      请手动下载: $PythonUrl" -ForegroundColor Yellow
        exit 1
    }
}

# 2. 卸载旧版Python 3.11.9
Write-Host "[2/6] 正在卸载旧版 Python 3.11.9..." -ForegroundColor Yellow
$OldPythonDir = "E:\software\python311"
if (Test-Path $OldPythonDir) {
    Remove-Item -Recurse -Force $OldPythonDir -ErrorAction SilentlyContinue
    Write-Host "      旧版已卸载" -ForegroundColor Green
} else {
    Write-Host "      旧版不存在，跳过" -ForegroundColor Green
}

# 3. 安装Python 3.14.5
Write-Host "[3/6] 正在安装 Python 3.14.5..." -ForegroundColor Yellow
$InstallArgs = @(
    "/quiet",
    "InstallAllUsers=0",
    "PrependPath=1",
    "Include_test=0",
    "TargetDir=$InstallDir"
)
Start-Process -FilePath $InstallerPath -ArgumentList $InstallArgs -Wait
Write-Host "      安装完成!" -ForegroundColor Green

# 4. 验证安装
Write-Host "[4/6] 验证安装..." -ForegroundColor Yellow
$PythonExe = "$InstallDir\python.exe"
& $PythonExe --version
& $PythonExe -c "import struct; print(f'Architecture: {struct.calcsize(\"P\") * 8}-bit')"
Write-Host "      验证通过!" -ForegroundColor Green

# 5. 重新创建虚拟环境
Write-Host "[5/6] 重新创建虚拟环境..." -ForegroundColor Yellow
$VenvDir = "$ProjectDir\venv"
if (Test-Path $VenvDir) {
    Remove-Item -Recurse -Force $VenvDir
}
& $PythonExe -m venv $VenvDir
Write-Host "      虚拟环境创建完成!" -ForegroundColor Green

# 6. 安装依赖
Write-Host "[6/6] 安装项目依赖..." -ForegroundColor Yellow
$VenvPython = "$VenvDir\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip

# 安装核心依赖
$Dependencies = @(
    "PyQt6", "PyQt6-Qt6",
    "numpy", "pandas",
    "requests", "aiohttp",
    "openai", "anthropic", "google-generativeai",
    "faiss-cpu",
    "python-dotenv", "loguru",
    "pydantic", "pydantic-settings",
    "pytest", "pytest-asyncio",
    "markdown", "pygments", "pyyaml",
    "pyqtgraph", "pyinstaller"
)

foreach ($Dep in $Dependencies) {
    Write-Host "      安装 $Dep..." -ForegroundColor Gray
    & $VenvPython -m pip install $Dep --only-binary :all: -q
}

Write-Host "      依赖安装完成!" -ForegroundColor Green

# 清理安装文件
Remove-Item $InstallerPath -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "升级完成! Python 3.14.5 已就绪" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "使用方法:" -ForegroundColor White
Write-Host "  & '$VenvPython' -m hyperbrain.main --process \"你好\"" -ForegroundColor Yellow
Write-Host ""
