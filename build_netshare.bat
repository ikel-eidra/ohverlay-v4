@echo off
:: ============================================================
:: NetShare Standalone Build Script
:: Produces a single .exe at dist\NetShare\NetShare.exe
:: No admin rights required. Runs on Windows 10/11.
::
:: Prerequisites (install once):
::   pip install pyinstaller PySide6 loguru
::
:: Usage:
::   Double-click build_netshare.bat
::   OR from terminal:  build_netshare.bat
:: ============================================================

echo.
echo ===========================
echo  Building NetShare.exe
echo ===========================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: Check PyInstaller is available
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Clean previous build artifacts
if exist build\NetShare rmdir /s /q build\NetShare
if exist dist\NetShare  rmdir /s /q dist\NetShare

:: Run PyInstaller
echo Running PyInstaller...
pyinstaller netshare.spec --noconfirm

if errorlevel 1 (
    echo.
    echo BUILD FAILED. Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo ===========================
echo  Build complete!
echo  Executable: dist\NetShare\NetShare.exe
echo ===========================
echo.
echo To distribute: copy the entire dist\NetShare\ folder to each PC.
echo Each user runs NetShare.exe once, right-clicks the tray icon,
echo and chooses "Configure My Shared Folder..." to set up their path.
echo.
pause
