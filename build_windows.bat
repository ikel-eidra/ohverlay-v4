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

set "PY_CMD=py -3.11"
%PY_CMD% --version >nul 2>&1
if errorlevel 1 (
    set "PY_CMD=py -3"
    %PY_CMD% --version >nul 2>&1
)
if errorlevel 1 (
    set "PY_CMD=python"
    %PY_CMD% --version >nul 2>&1
)
if errorlevel 1 (
    echo  [ERROR] Python 3.11+ not found in PATH or via the Python launcher.
    echo  Install Python 3.11 from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

set "BUILD_PY=.venv-build\Scripts\python.exe"
if not exist "%BUILD_PY%" (
    echo  [1/6] Creating isolated build environment...
    %PY_CMD% -m venv .venv-build
    if errorlevel 1 (
        echo.
        echo  [ERROR] Failed to create .venv-build
        pause
        exit /b 1
    )
) else (
    echo  [1/6] Reusing isolated build environment...
)

echo.
echo  [2/6] Upgrading build tools...
"%BUILD_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo.
    echo  [ERROR] Failed to upgrade pip tooling.
    pause
    exit /b 1
)

echo.
echo  [3/6] Installing PyInstaller...
"%BUILD_PY%" -m pip install pyinstaller
if errorlevel 1 (
    echo.
    echo  [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

echo.
echo  [4/6] Installing application dependencies...
"%BUILD_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  [ERROR] Failed to install application dependencies.
    pause
    exit /b 1
)

echo.
echo  [5/6] Clearing previous build output...
if exist "build" rmdir /s /q "build"
if exist "dist\Ohverlay" rmdir /s /q "dist\Ohverlay"

echo.
echo  [6/6] Building Ohverlay.exe with PyInstaller...
echo         (This may take 2-5 minutes)
echo.
"%BUILD_PY%" -m PyInstaller ohverlay.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed! Check the errors above.
    pause
    exit /b 1
)

echo.
echo  [6/6] Build complete!
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
if /I "%OHVERLAY_NO_PAUSE%"=="1" exit /b 0
pause
