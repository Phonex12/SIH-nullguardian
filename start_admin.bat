@echo off
title NCRP Sentinel - LEA Tactical Command Terminal (Port 9000)
color 0a

echo =====================================================================
echo    NCRP SENTINEL // LEA TACTICAL COMMAND TERMINAL (PORT 9000)
echo =====================================================================
echo.
echo Launching Secured Law Enforcement Command Terminal on http://127.0.0.1:9000/ ...
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

start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:9000/"

%PY_CMD% ncrp_sentinel\backend\run_lea.py

pause
