@echo off
setlocal
title DrishtiX — Rebuild ^& Run
color 0E

:: ============================================================
::  DrishtiX — Rebuild & Run
::  Use this after making code changes. Rebuilds the JAR
::  and immediately launches the app.
:: ============================================================

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║           DrishtiX — Rebuild ^& Run                      ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

set "PROJECT_ROOT=%~dp0"
set "APP_DIR=%PROJECT_ROOT%services\drishtix-app"

echo  [1/2] Rebuilding JAR...
cd /d "%APP_DIR%"
call mvnw.cmd clean package -DskipTests -q
if %errorlevel% neq 0 (
    echo.
    echo  ✗ Build FAILED. Fix the errors and try again.
    pause
    exit /b 1
)
echo        ✓ Build successful
cd /d "%PROJECT_ROOT%"

echo  [2/2] Launching...
echo.
call "%PROJECT_ROOT%start_drishtix.bat"
