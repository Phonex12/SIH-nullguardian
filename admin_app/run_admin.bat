@echo off
title NCRP Sentinel - LEA Tactical Command Center
cls
echo =====================================================================
echo          NCRP SENTINEL -- LEA TACTICAL COMMAND CENTER
echo =====================================================================
echo [INFO] Initializing standalone LEA Admin Dashboard on Port 9000...
echo.

cd /d "%~dp0.."
python -m admin_app.server

pause
