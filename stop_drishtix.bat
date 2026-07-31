@echo off
setlocal
title DrishtiX Shutdown
color 0C

:: ============================================================
::  DrishtiX — Clean Shutdown
::  Stops the ReID service and cleans up background processes.
::  MongoDB is left running (it's a system service).
:: ============================================================

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║            DrishtiX — Shutdown Sequence                 ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: Kill the ReID Python service (uvicorn)
echo  [1/2] Stopping ReID microservice...
tasklist /FI "WINDOWTITLE eq DrishtiX ReID Service*" 2>nul | find /I "cmd.exe" >nul 2>&1
if %errorlevel% equ 0 (
    taskkill /FI "WINDOWTITLE eq DrishtiX ReID Service*" /T /F >nul 2>&1
    echo        ✓ ReID service stopped
) else (
    :: Also try killing uvicorn directly
    tasklist /FI "IMAGENAME eq uvicorn.exe" 2>nul | find /I "uvicorn" >nul 2>&1
    if !errorlevel! equ 0 (
        taskkill /IM uvicorn.exe /F >nul 2>&1
        echo        ✓ Uvicorn process killed
    ) else (
        echo        ✓ ReID service was not running
    )
)

:: Kill any lingering DrishtiX Java process
echo  [2/2] Checking for DrishtiX Java process...
powershell -Command "Get-Process java -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*DrishtiX*' -or $_.CommandLine -like '*drishtix*' } | Stop-Process -Force -ErrorAction SilentlyContinue" 2>nul
echo        ✓ Java processes cleaned up

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║       ✓ DrishtiX shutdown complete                      ║
echo  ║       MongoDB left running (system service)             ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  Press any key to close...
pause >nul
