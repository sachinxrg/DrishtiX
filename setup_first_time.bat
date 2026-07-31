@echo off
setlocal enabledelayedexpansion
title DrishtiX — First Time Setup
color 0B

:: ============================================================
::  DrishtiX — First Time Setup
::  Run this ONCE to set up everything. After this, use
::  start_drishtix.bat for daily launches.
:: ============================================================

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║        DrishtiX — First Time Setup Wizard               ║
echo  ║  This sets up everything you need. Run only ONCE.       ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

set "PROJECT_ROOT=%~dp0"
set "APP_DIR=%PROJECT_ROOT%services\drishtix-app"
set "REID_DIR=%PROJECT_ROOT%services\reid-service"
set "DB_INIT=%PROJECT_ROOT%database\drishtix_init.js"

:: ─────────────────────────────────────────────────────────────
:: Pre-flight: Check required tools
:: ─────────────────────────────────────────────────────────────
echo  ── Pre-flight checks ──────────────────────────────────
echo.

set "MISSING=0"

where java >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('java -version 2^>^&1 ^| find "version"') do echo   ✓ Java: %%v
) else (
    echo   ✗ Java NOT FOUND — Install JDK 17+
    set /a MISSING+=1
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   ✓ %%v
) else (
    echo   ✗ Python NOT FOUND — Install Python 3.10+
    set /a MISSING+=1
)

where mongosh >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ mongosh found
) else (
    echo   ⚠ mongosh not found — DB init will be skipped
)

sc query MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ MongoDB service found
) else (
    echo   ⚠ MongoDB not installed as service
)

echo.
if %MISSING% gtr 0 (
    echo  ✗ %MISSING% required tool^(s^) missing. Please install them first.
    pause
    exit /b 1
)

:: ─────────────────────────────────────────────────────────────
:: Step 1: Initialize MongoDB
:: ─────────────────────────────────────────────────────────────
echo  ── Step 1: MongoDB Setup ──────────────────────────────
echo.

sc query MongoDB | find "RUNNING" >nul 2>&1
if %errorlevel% neq 0 (
    echo   Starting MongoDB service...
    net start MongoDB >nul 2>&1
)

where mongosh >nul 2>&1
if %errorlevel% equ 0 (
    echo   Running database initialization script...
    mongosh --quiet drishtix_db "%DB_INIT%"
    echo.
    echo   ✓ Database initialized
) else (
    echo   ⚠ Skipped — install mongosh and run manually:
    echo     mongosh drishtix_db database\drishtix_init.js
)
echo.

:: ─────────────────────────────────────────────────────────────
:: Step 2: Set up Python Virtual Environment for ReID Service
:: ─────────────────────────────────────────────────────────────
echo  ── Step 2: ReID Service Setup ─────────────────────────
echo.

if exist "%REID_DIR%\venv\Scripts\python.exe" (
    echo   ✓ Virtual environment already exists
) else (
    echo   Creating Python virtual environment...
    cd /d "%REID_DIR%"
    python -m venv venv
    if !errorlevel! equ 0 (
        echo   ✓ Virtual environment created
    ) else (
        echo   ✗ Failed to create venv
        cd /d "%PROJECT_ROOT%"
        goto :step3
    )
    cd /d "%PROJECT_ROOT%"
)

echo   Installing Python dependencies ^(this may take a while^)...
cd /d "%REID_DIR%"
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo   ✓ Python dependencies installed
call deactivate 2>nul
cd /d "%PROJECT_ROOT%"
echo.

:: ─────────────────────────────────────────────────────────────
:: Step 3: Build Java Application
:: ─────────────────────────────────────────────────────────────
:step3
echo  ── Step 3: Java Build ─────────────────────────────────
echo.

echo   Building DrishtiX fat JAR ^(this takes 1-3 minutes^)...
cd /d "%APP_DIR%"
call mvnw.cmd clean package -DskipTests
if %errorlevel% equ 0 (
    echo.
    echo   ✓ Build successful: target\drishtix-app-2.0.0-SNAPSHOT.jar
) else (
    echo.
    echo   ✗ Build failed! Check errors above.
)
cd /d "%PROJECT_ROOT%"
echo.

:: ─────────────────────────────────────────────────────────────
:: Step 4: Create config.properties if missing
:: ─────────────────────────────────────────────────────────────
echo  ── Step 4: Configuration ──────────────────────────────
echo.

if not exist "%APP_DIR%\config.properties" (
    echo   Creating config.properties from example...
    copy "%APP_DIR%\config.properties.example" "%APP_DIR%\config.properties" >nul
    echo   ✓ config.properties created — edit if needed
) else (
    echo   ✓ config.properties already exists
)
echo.

:: ─────────────────────────────────────────────────────────────
:: Done!
:: ─────────────────────────────────────────────────────────────
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║          ✓ First-time setup complete!                   ║
echo  ║                                                         ║
echo  ║   From now on, just double-click:                       ║
echo  ║     start_drishtix.bat   — to launch everything         ║
echo  ║     stop_drishtix.bat    — to shut down                 ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  Press any key to close...
pause >nul
