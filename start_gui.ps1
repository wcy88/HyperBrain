# HyperBrain System Launcher - GUI Mode
$PROJECT = "E:\超脑\超脑002"
$PYTHON = Join-Path $PROJECT "venv\Scripts\python.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   HyperBrain System - GUI Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Checking environment..."
Write-Host "   Python path: $PYTHON"

if (-not (Test-Path $PYTHON)) {
    Write-Host "   [Error] Python not found at: $PYTHON" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "   [OK] Python found" -ForegroundColor Green

Write-Host ""
Write-Host "[2/3] Starting GUI..."
Write-Host "   Close window to exit"
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

Set-Location $PROJECT
& $PYTHON -m hyperbrain.main --mode gui

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   GUI stopped" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
