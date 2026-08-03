@echo off
echo ========================================
echo   HyperBrain System
echo ========================================
echo.

set PYTHON=E:\software\python314\python.exe
set PROJECT=E:\超脑\超脑002

echo [1/3] Check environment...
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found
    pause
    exit /b 1
)
echo   [OK] Python ready

echo.
echo [2/3] Start system...
echo   Mode: CLI
echo   Press Ctrl+C to exit
echo.
echo ========================================

cd /d "%PROJECT%"
"%PYTHON%" -m hyperbrain.main %*

echo.
echo ========================================
echo   System stopped
echo ========================================
pause
