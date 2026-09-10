@echo off
title NCRP Sentinel - Dual Service Manager
color 0e

echo =====================================================================
echo    NCRP SENTINEL // DUAL AIR-GAPPED ISOLATED SERVICES
echo =====================================================================
echo.
echo Launching both isolated services concurrently:
echo  1. Public Citizen Portal (Port 8000)
echo  2. LEA Tactical Command Terminal (Port 9000)
echo.

where python >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
) else (
    if exist "C:\Program Files\Python313\python.exe" (
        set PY_CMD="C:\Program Files\Python313\python.exe"
    ) else (
        set PY_CMD=py
    )
)

start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000/ && start http://127.0.0.1:9000/"

%PY_CMD% ncrp_sentinel\backend\run_all.py

pause
