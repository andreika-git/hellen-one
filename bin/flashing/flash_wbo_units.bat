@echo off
rem Hands-free production flashing of WBO STM32F042 units via ST-Link:
rem waits for a unit, unlocks/flashes/verifies/resets it, waits for it to be
rem unplugged, then waits for the next unit. No keypresses needed, Ctrl+C to stop.

setlocal

rem keep in sync with download_openocd.bat
set OPENOCD_VERSION=0.12.0-7
set OPENOCD=%~dp0xpack-openocd-%OPENOCD_VERSION%\bin\openocd.exe
set CFG=-f interface/stlink.cfg -f target/stm32f0x.cfg
set IMAGE=wideband_image_with_bl.bin

if not exist "%OPENOCD%" call "%~dp0download_openocd.bat"
if not exist "%OPENOCD%" (
    echo ERROR: OpenOCD not found at %OPENOCD%
    exit /b 1
)

rem openocd 'program' takes the image relative to cwd
pushd "%~dp0..\..\modules\wbo\fw-releases\Wideband f0_module 2023-dec" || exit /b 1

set /a COUNT=0
echo Flashing %CD%\%IMAGE%
echo Connect the first unit. Press Ctrl+C to stop.

:wait_connect
"%OPENOCD%" %CFG% -c "init; exit" >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto wait_connect
)

echo Unit detected, flashing...
"%OPENOCD%" %CFG% -c "init; halt; stm32f1x unlock 0; program %IMAGE% verify reset exit 0x08000000"
if errorlevel 1 (
    echo *** FLASHING FAILED - check the connection, retrying... ***
    timeout /t 2 /nobreak >nul
    goto wait_connect
)

set /a COUNT+=1
echo.
echo ===== Unit #%COUNT% flashed OK. Disconnect it and connect the next one. =====
echo.

:wait_removal
timeout /t 2 /nobreak >nul
"%OPENOCD%" %CFG% -c "init; exit" >nul 2>&1
if not errorlevel 1 goto wait_removal
goto wait_connect
