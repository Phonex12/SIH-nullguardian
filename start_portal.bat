@echo off
title NCRP Sentinel - Public Citizen Portal (Port 8000)
color 0b

echo =====================================================================
echo    NCRP SENTINEL // PUBLIC CITIZEN PORTAL & AWARENESS HUB
echo =====================================================================
echo.
echo Launching Citizen Service on http://127.0.0.1:8000/ ...
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

start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000/"

%PY_CMD% ncrp_sentinel\backend\run_citizen.py

pause
