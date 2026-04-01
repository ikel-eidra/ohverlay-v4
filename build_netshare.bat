@echo off
:: ============================================================
:: NetShare Build Script
:: Developed by:  Futol Ethical Technology Ecosystems
:: For:           Sarah Attaqnia Contracting Company
::
:: Produces:  dist\NetShare\NetShare.exe
::   - No admin rights required
::   - No console window
::   - No network ports opened
::   - Runs silently in the system tray
::
:: Prerequisites (run once):
::   pip install pyinstaller PySide6 loguru
::
:: Usage:
::   Double-click this file   OR
::   From terminal:  build_netshare.bat
:: ============================================================

setlocal enabledelayedexpansion

echo.
echo  ============================================================
echo   NetShare Build
echo   Futol Ethical Technology Ecosystems
echo   Sarah Attaqnia Contracting Company
echo  ============================================================
echo.

:: --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo  Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do set PYVER=%%v
echo  [OK] %PYVER%

:: --- Check / Install dependencies ---
echo.
echo  Checking dependencies...

pip show PySide6 >nul 2>&1
if errorlevel 1 (
    echo  Installing PySide6...
    pip install PySide6
)

pip show loguru >nul 2>&1
if errorlevel 1 (
    echo  Installing loguru...
    pip install loguru
)

pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  Installing PyInstaller...
    pip install pyinstaller
)

echo  [OK] All dependencies present.

:: --- Clean previous build ---
echo.
echo  Cleaning previous build artefacts...
if exist build\NetShare  rmdir /s /q build\NetShare  2>nul
if exist dist\NetShare   rmdir /s /q dist\NetShare   2>nul

:: --- Build ---
echo.
echo  Running PyInstaller...
echo.
pyinstaller netshare.spec --noconfirm

if errorlevel 1 (
    echo.
    echo  [FAILED] Build failed. Review errors above.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   BUILD COMPLETE
echo   Output:  dist\NetShare\NetShare.exe
echo  ============================================================
echo.
echo  Distribution:
echo    Copy the entire  dist\NetShare\  folder to each PC.
echo    Run NetShare.exe (no installation wizard needed).
echo    Right-click the tray icon to configure.
echo.
echo  First-time setup on each PC:
echo    1. Right-click tray -> Configure My Shared Folder
echo    2. Enter your network folder path + username + peers
echo    3. Right-click -> Enable Notifications
echo.
pause
endlocal
