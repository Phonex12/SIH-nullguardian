@echo off
title NCRP Sentinel - LEA Admin Launcher
cls
echo =====================================================================
echo          NCRP SENTINEL -- LEA TACTICAL COMMAND CENTER
echo =====================================================================
echo Starting LEA Admin Dashboard on Port 9000...
echo.
cd /d "%~dp0"
python -m admin_app.server
pause
