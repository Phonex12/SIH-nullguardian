@echo off
title NCRP Sentinel - Citizen Support Portal
cls
echo =====================================================================
echo           NCRP SENTINEL -- CITIZEN CYBER SUPPORT PORTAL
echo =====================================================================
echo [INFO] Initializing standalone Citizen Portal on Port 8000...
echo.

cd /d "%~dp0.."
python -m citizen_app.server

pause
