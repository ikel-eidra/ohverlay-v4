@echo off
REM ============================================
REM  ZenFish Overlay - Windows Build Script
REM  Creates a portable .exe (no admin needed)
REM ============================================
echo.
echo  ZenFish Overlay - Building portable Windows app...
echo  ==================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found!
    echo  Download portable Python from: https://www.python.org/downloads/
    echo  Or use the WinPython/Miniconda portable method in INSTALL.md
    pause
    exit /b 1
)

echo [1/3] Installing build dependencies...
pip install --user pyinstaller PySide6 numpy loguru requests pynput anthropic

echo.
echo [2/3] Building ZenFish.exe...
pyinstaller zenfish.spec --noconfirm --clean

echo.
echo [3/3] Done!
echo.
echo  Your portable ZenFish app is in: dist\ZenFish\
echo  Just copy that folder anywhere and run ZenFish.exe
echo  No admin privileges needed!
echo.
pause
