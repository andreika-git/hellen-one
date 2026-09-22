@echo off
rem Downloads xPack OpenOCD for Windows and extracts it next to this script.
rem Uses curl and powershell, both included with Windows 10 and newer.

setlocal

set OPENOCD_VERSION=0.12.0-7
set OPENOCD_DIR=xpack-openocd-%OPENOCD_VERSION%
set OPENOCD_ZIP=%OPENOCD_DIR%-win32-x64.zip
set OPENOCD_URL=https://github.com/xpack-dev-tools/openocd-xpack/releases/download/v%OPENOCD_VERSION%/%OPENOCD_ZIP%

cd /d "%~dp0"

if exist "%OPENOCD_DIR%\bin\openocd.exe" (
    echo OpenOCD %OPENOCD_VERSION% is already present in %~dp0%OPENOCD_DIR%
    goto :EOF
)

echo Downloading %OPENOCD_URL%
curl --location --fail --output "%OPENOCD_ZIP%" "%OPENOCD_URL%"
if errorlevel 1 (
    echo ERROR: failed to download %OPENOCD_URL%
    exit /b 1
)

echo Extracting %OPENOCD_ZIP%
rem not using tar: it chokes on the non-ASCII file names inside the xPack zip
powershell -NoProfile -Command "Expand-Archive -LiteralPath '%OPENOCD_ZIP%' -DestinationPath '.' -Force"
if errorlevel 1 (
    echo ERROR: failed to extract %OPENOCD_ZIP%
    exit /b 1
)

del "%OPENOCD_ZIP%"

echo Done: %~dp0%OPENOCD_DIR%\bin\openocd.exe
