@echo off
REM ============================================================
REM  OHVERLAY v4.0 - Portable ZIP Builder
REM  By Futol Ethical Technology Ecosystems
REM  Creates a single ZIP file you can share with anyone
REM ============================================================

REM Auto-navigate to the folder where this script lives
cd /d "%~dp0"

echo.
echo   =============================================
echo    OHVERLAY v4.0 - Portable ZIP Builder
echo   =============================================
echo.

REM Always rebuild first so the ZIP matches the current source tree
echo  Rebuilding portable app first...
set "OHVERLAY_NO_PAUSE=1"
call build_windows.bat
set "OHVERLAY_NO_PAUSE="
if errorlevel 1 (
    echo  [ERROR] Build failed.
    pause
    exit /b 1
)

echo  Creating portable ZIP...

REM Create output directory
if not exist "installer_output" mkdir installer_output

REM Use PowerShell to create ZIP (available on Windows 10+)
powershell -Command "Compress-Archive -Path 'dist\Ohverlay\*' -DestinationPath 'installer_output\Ohverlay-Portable.zip' -Force"

if errorlevel 1 (
    echo  [ERROR] ZIP creation failed.
    pause
    exit /b 1
)

echo.
echo  =============================================
echo   Portable ZIP Ready!
echo  =============================================
echo.
echo   File: installer_output\Ohverlay-Portable.zip
echo.
echo   To use:
echo     1. Extract the ZIP anywhere
echo     2. Run Ohverlay.exe
echo     3. That's it! No install needed.
echo.
pause
