@echo off
setlocal enabledelayedexpansion
title DrishtiX Launcher
color 0A

:: ============================================================
::  DrishtiX — One-Click Master Launcher
::  Double-click this file to start the entire system.
:: ============================================================

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║           DrishtiX — Autonomous Launch Sequence         ║
echo  ║     Advanced Facial Recognition ^& Alert System v2.0    ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

set "PROJECT_ROOT=%~dp0"
set "APP_DIR=%PROJECT_ROOT%services\drishtix-app"
set "REID_DIR=%PROJECT_ROOT%services\reid-service"
set "DB_INIT=%PROJECT_ROOT%database\drishtix_init.js"
set "JAR_FILE=%APP_DIR%\target\drishtix-app-1.0.0.jar"
set "REID_VENV=%REID_DIR%\venv"
set "REID_PID_FILE=%PROJECT_ROOT%.reid_service.pid"
set "ERRORS=0"

:: ─────────────────────────────────────────────────────────────
:: STEP 1: Check MongoDB
:: ─────────────────────────────────────────────────────────────
echo  [1/5] Checking MongoDB...
sc query MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    sc query MongoDB | find "RUNNING" >nul 2>&1
    if !errorlevel! equ 0 (
        echo        ✓ MongoDB is running
    ) else (
        echo        ⚠ MongoDB service found but not running. Starting...
        net start MongoDB >nul 2>&1
        if !errorlevel! equ 0 (
            echo        ✓ MongoDB started successfully
        ) else (
            echo        ✗ Failed to start MongoDB. Try running as Administrator.
            set /a ERRORS+=1
        )
    )
) else (
    :: Check if mongod is running as a process (not a service)
    tasklist /FI "IMAGENAME eq mongod.exe" 2>nul | find /I "mongod.exe" >nul 2>&1
    if !errorlevel! equ 0 (
        echo        ✓ MongoDB is running ^(as process^)
    ) else (
        echo        ✗ MongoDB is not installed as a service and not running.
        echo          Please start MongoDB manually before launching DrishtiX.
        set /a ERRORS+=1
    )
)

:: ─────────────────────────────────────────────────────────────
:: STEP 2: Initialize Database (idempotent — safe to re-run)
:: ─────────────────────────────────────────────────────────────
echo  [2/5] Initializing database schema...
where mongosh >nul 2>&1
if %errorlevel% equ 0 (
    mongosh --quiet drishtix_db "%DB_INIT%" >nul 2>&1
    if !errorlevel! equ 0 (
        echo        ✓ Database schema verified
    ) else (
        echo        ⚠ Database init had warnings ^(may already be initialized^)
    )
) else (
    echo        ⚠ mongosh not found in PATH — skipping DB init
    echo          Run manually: mongosh drishtix_db database\drishtix_init.js
)

:: ─────────────────────────────────────────────────────────────
:: STEP 3: Start Python ReID Service (background)
:: ─────────────────────────────────────────────────────────────
echo  [3/5] Starting ReID microservice...

:: Check if already running
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8100/health' -TimeoutSec 2 -ErrorAction Stop; if($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo        ✓ ReID service is already running on port 8100
    goto :skip_reid
)

:: Check if venv exists
if exist "%REID_VENV%\Scripts\python.exe" (
    echo        Using existing virtual environment...
    start "DrishtiX ReID Service" /MIN cmd /c "cd /d "%REID_DIR%" && "%REID_VENV%\Scripts\python.exe" -m uvicorn main:app --port 8100 --host 0.0.0.0"
    echo        ✓ ReID service starting in background ^(port 8100^)
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        echo        ⚠ No virtual environment found. Starting with system Python...
        echo          ^(Run setup_first_time.bat to create a proper venv^)
        start "DrishtiX ReID Service" /MIN cmd /c "cd /d "%REID_DIR%" && python -m uvicorn main:app --port 8100 --host 0.0.0.0"
        echo        ✓ ReID service starting in background ^(port 8100^)
    ) else (
        echo        ⚠ Python not found — ReID service will be unavailable
        echo          DrishtiX will run in LBPH-only mode ^(graceful degradation^)
    )
)

:skip_reid

:: Wait a moment for ReID service to initialize
timeout /t 2 /nobreak >nul

:: ─────────────────────────────────────────────────────────────
:: STEP 4: Build Java Application (if JAR doesn't exist)
:: ─────────────────────────────────────────────────────────────
echo  [4/5] Preparing Java application...

if exist "%JAR_FILE%" (
    echo        ✓ JAR already built: drishtix-app-1.0.0.jar
) else (
    echo        Building fat JAR ^(first time may take a few minutes^)...
    cd /d "%APP_DIR%"
    call mvnw.cmd clean package -DskipTests -q 2>nul
    if !errorlevel! equ 0 (
        echo        ✓ Build successful
    ) else (
        echo        ✗ Build failed! Check Maven output for errors.
        echo          Try running manually: cd services\drishtix-app ^&^& mvnw clean package -DskipTests
        set /a ERRORS+=1
    )
    cd /d "%PROJECT_ROOT%"
)

:: ─────────────────────────────────────────────────────────────
:: STEP 5: Launch DrishtiX
:: ─────────────────────────────────────────────────────────────
if %ERRORS% gtr 0 (
    echo.
    echo  ╔══════════════════════════════════════════════════════════╗
    echo  ║  ⚠ There were %ERRORS% error^(s^). DrishtiX may not work properly.  ║
    echo  ╚══════════════════════════════════════════════════════════╝
    echo.
    echo  Press any key to launch anyway, or close this window to abort.
    pause >nul
)

if not exist "%JAR_FILE%" (
    echo.
    echo  ✗ FATAL: JAR file not found at %JAR_FILE%
    echo    Cannot launch DrishtiX. Please fix the build errors first.
    echo.
    pause
    exit /b 1
)

echo  [5/5] Launching DrishtiX...
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║          ✓ All systems GO — DrishtiX launching!         ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  TIP: To stop everything later, run stop_drishtix.bat
echo.

cd /d "%APP_DIR%"
java --add-opens javafx.graphics/com.sun.javafx.scene=ALL-UNNAMED --add-opens javafx.graphics/com.sun.javafx.scene.traversal=ALL-UNNAMED --add-opens javafx.graphics/com.sun.javafx.css=ALL-UNNAMED --add-opens javafx.controls/com.sun.javafx.scene.control.behavior=ALL-UNNAMED --add-opens javafx.controls/javafx.scene.control.skin=ALL-UNNAMED --add-opens javafx.base/com.sun.javafx.runtime=ALL-UNNAMED -cp "target\drishtix-app-1.0.0.jar" com.drishtix.DrishtiXLauncher

echo.
echo  DrishtiX has exited. Press any key to close this window.
pause >nul
