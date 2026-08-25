@echo off
setlocal enabledelayedexpansion
title DrishtiX v4.0 — Tactical Edge Surveillance Launcher
color 0B

echo.
echo  ============================================================
echo          DrishtiX v4.0 Tactical Edge Surveillance Node
echo          Python 3.11+ / PySide6 / YuNet / SFace
echo  ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "APP_DIR=%SCRIPT_DIR%services\drishtix-py"
set "VENV_PYTHON=%APP_DIR%\venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    echo   Using dedicated virtual environment...
    cd /d "%APP_DIR%"
    "%VENV_PYTHON%" main.py
) else (
    echo   Venv not found, using global python...
    cd /d "%APP_DIR%"
    python main.py
)

if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] DrishtiX terminated with exit code %errorlevel%
    pause
)
