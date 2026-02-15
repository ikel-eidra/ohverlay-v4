@echo off
REM ============================================================
REM  OHVERLAY v4.0 - Windows Build Script
REM  By Futol Ethical Technology Ecosystems
REM  Creates a portable .exe folder (no admin/install needed)
REM ============================================================

REM Auto-navigate to the folder where this script lives
cd /d "%~dp0"

echo.
echo   =============================================
echo    OHVERLAY v4.0 - Portable Windows Builder
echo    Futol Ethical Technology Ecosystems
echo   =============================================
echo.
echo   Working directory: %cd%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found in PATH!
    echo  Download Python 3.10+ from: https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo  [1/4] Installing build tools...
pip install --user pyinstaller

echo.
echo  [2/4] Installing application dependencies...
pip install --user -r requirements.txt

echo.
echo  [3/4] Building Ohverlay.exe with PyInstaller...
echo         (This may take 2-5 minutes)
echo.
pyinstaller ohverlay.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed! Check the errors above.
    pause
    exit /b 1
)

echo.
echo  [4/4] Build complete!
echo.
echo  =============================================
echo   Your portable OHVERLAY is ready!
echo  =============================================
echo.
echo   Location: dist\Ohverlay\
echo   Run:      dist\Ohverlay\Ohverlay.exe
echo.
echo   To distribute:
echo     1. Copy the entire dist\Ohverlay\ folder
echo     2. Share it as a ZIP file
echo     3. Or run build_installer.bat to create a setup wizard
echo.
echo   No admin privileges or Python needed to run!
echo.
pause
