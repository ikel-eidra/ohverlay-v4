@echo off
REM ============================================================
REM  OHVERLAY v4.0 - Windows Installer Builder
REM  By Futol Ethical Technology Ecosystems
REM  Creates a proper setup wizard (.exe installer)
REM
REM  This script:
REM    1. Builds the portable app with PyInstaller
REM    2. Packages it into a setup wizard with Inno Setup
REM ============================================================

REM Auto-navigate to the folder where this script lives
cd /d "%~dp0"

echo.
echo   =============================================
echo    OHVERLAY v4.0 - Windows Installer Builder
echo    Futol Ethical Technology Ecosystems
echo   =============================================
echo.

echo  [Step 1] Rebuilding portable app...
echo.
set "OHVERLAY_NO_PAUSE=1"
call build_windows.bat
set "OHVERLAY_NO_PAUSE="
if errorlevel 1 (
    echo  [ERROR] Portable build failed. Cannot create installer.
    pause
    exit /b 1
)

echo.
echo  [Step 2] Looking for Inno Setup compiler...

REM Try common Inno Setup install locations
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)
if "%ISCC%"=="" if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)
if "%ISCC%"=="" if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    winget --version >nul 2>&1
    if not errorlevel 1 (
        echo.
        echo  [INFO] Inno Setup not found. Attempting user-scope install with winget...
        winget install --id JRSoftware.InnoSetup --scope user --accept-source-agreements --accept-package-agreements

        if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
            set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
        )
        if "%ISCC%"=="" if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
            set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
        )
        if "%ISCC%"=="" if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
            set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
        )
    )
)

if "%ISCC%"=="" (
    echo.
    echo  [INFO] Inno Setup not found.
    echo         Download it free from: https://jrsoftware.org/isdl.php
    echo         Or run: winget install --id JRSoftware.InnoSetup --scope user
    echo         Then run this script again.
    echo.
    echo  [ALTERNATIVE] You can also just ZIP the dist\Ohverlay\ folder
    echo               and share it as a portable app (no install needed).
    echo.
    pause
    exit /b 1
)

echo  Found: %ISCC%
echo.
echo  [Step 3] Building installer...
echo.

"%ISCC%" installer.iss

if errorlevel 1 (
    echo.
    echo  [ERROR] Installer build failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo  =============================================
echo   Windows Installer Ready!
echo  =============================================
echo.
echo   Installer: installer_output\Ohverlay-Setup.exe
echo.
echo   This installer:
echo     - Works without admin (installs to user folder)
echo     - Creates Start Menu shortcut
echo     - Optional desktop shortcut
echo     - Optional Windows startup entry
echo     - Clean uninstaller included
echo.
if /I "%OHVERLAY_NO_PAUSE%"=="1" exit /b 0
pause
