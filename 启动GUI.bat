@echo off
echo ========================================
echo   HyperBrain System
echo   GUI Mode
echo ========================================
echo.

echo [1/3] Checking environment...
py --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python or add it to PATH.
    pause
    exit /b 1
)
echo   [OK] Python ready

echo.
echo [2/3] Starting GUI...
echo   Close window to exit
echo.
echo ========================================

cd /d "E:\超脑\超脑002"
py -m hyperbrain.app --mode gui

echo.
echo ========================================
echo   GUI stopped
echo ========================================
pause
