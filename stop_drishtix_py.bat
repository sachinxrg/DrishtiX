@echo off
setlocal
title DrishtiX — Stop Tactical Surveillance Node
color 0C

echo.
echo  ============================================================
echo          Stopping DrishtiX Tactical Surveillance Node...
echo  ============================================================
echo.

:: Terminate running Python processes launched from drishtix-py
taskkill /F /FI "WINDOWTITLE eq DrishtiX*" /T >nul 2>&1
wmic process where "commandline like '%%drishtix-py%%'" delete >nul 2>&1

echo.
echo  [OK] DrishtiX processes stopped successfully.
echo.
timeout /t 2 >nul
