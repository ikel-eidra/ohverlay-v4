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
echo.
echo   =============================================
echo    OHVERLAY v4.0 - Windows Installer Builder
echo    Futol Ethical Technology Ecosystems
echo   =============================================
echo.

REM Step 1: Build the portable app first
if not exist "dist\Ohverlay\Ohverlay.exe" (
    echo  [Step 1] Building portable app first...
    echo.
    call build_windows.bat
    if errorlevel 1 (
        echo  [ERROR] Portable build failed. Cannot create installer.
        pause
        exit /b 1
    )
) else (
    echo  [Step 1] Portable build already exists, skipping...
    echo           (Delete dist\Ohverlay\ to force rebuild)
)

echo.
echo  [Step 2] Looking for Inno Setup compiler...

REM Try common Inno Setup install locations
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    echo.
    echo  [INFO] Inno Setup not found.
    echo         Download it free from: https://jrsoftware.org/isdl.php
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
echo   Installer: installer_output\Ohverlay-v4.0-Setup.exe
echo.
echo   This installer:
echo     - Works without admin (installs to user folder)
echo     - Creates Start Menu shortcut
echo     - Optional desktop shortcut
echo     - Optional Windows startup entry
echo     - Clean uninstaller included
echo.
pause
