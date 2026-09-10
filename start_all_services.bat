@echo off
title NCRP Sentinel - Dual System Launcher
cls
echo =====================================================================
echo               NCRP SENTINEL -- DUAL PLATFORM LAUNCHER
echo =====================================================================
echo Launching Citizen Portal (Port 8000) and LEA Admin (Port 9000)...
echo.

start "NCRP Sentinel - Citizen Portal (Port 8000)" cmd /k "cd /d %~dp0 && python -m citizen_app.server"
timeout /t 2 /nobreak >nul
start "NCRP Sentinel - LEA Admin Command (Port 9000)" cmd /k "cd /d %~dp0 && python -m admin_app.server"

echo Both services launched in independent processes.
echo - Citizen Portal: http://localhost:8000
echo - LEA Admin Panel: http://localhost:9000
echo.
