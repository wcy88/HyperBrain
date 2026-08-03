@echo off
chcp 65001 >nul
echo ========================================
echo   HyperBrain System - CLI Mode
echo ========================================
echo.

echo [1/3] Checking environment...
E:\software\python314\python.exe --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found at E:\software\python314\python.exe
    pause
    exit /b 1
)
echo   [OK] Python ready

echo.
echo [2/3] Starting system...
echo   Mode: CLI
echo   Press Ctrl+C to exit
echo.
echo ========================================

cd /d "E:\超脑\超脑002"
E:\software\python314\python.exe -m hyperbrain.main %*

echo.
echo ========================================
echo   System stopped
echo ========================================
pause
