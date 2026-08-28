@echo off
setlocal
title DrishtiX v4.0 Test Suite Runner
set "APP_DIR=%~dp0..\services\drishtix-py"
set "PYTHON=%APP_DIR%\venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    set "PYTHON=python"
)

echo Running DrishtiX v4.0 Automated Test Suite...
cd /d "%APP_DIR%"
"%PYTHON%" -m pytest tests/ -v

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo [PASS] All automated test cases passed successfully!
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo [FAIL] Test suite encountered errors. Check output above.
    echo ============================================================
)
