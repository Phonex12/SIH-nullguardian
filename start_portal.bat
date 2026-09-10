@echo off
title NCRP Sentinel - Citizen Portal Launcher
cls
echo =====================================================================
echo           NCRP SENTINEL -- CITIZEN CYBER SUPPORT PORTAL
echo =====================================================================
echo Starting Citizen Portal on Port 8000...
echo.
cd /d "%~dp0"
python -m citizen_app.server
pause
