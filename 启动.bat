@echo off
cd /d "%~dp0"
title Herba Atlas Launcher

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python and add it to PATH.
  pause
  exit /b 1
)

python -c "import fastapi,uvicorn" >nul 2>&1
if errorlevel 1 (
  echo [INFO] Installing dependencies...
  python -m pip install -r backend\requirements.txt
)

echo Starting backend in a new window...
echo Keep that window open. Closing it stops the site.
echo.

:: Start server in a SEPARATE window that stays alive
start "Herba-Backend-KEEP-OPEN" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo Waiting for database...
set /a n=0
:wait
set /a n+=1
if %n% GTR 40 goto :fail
timeout /t 1 /nobreak >nul
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/stats',timeout=1)" >nul 2>&1
if errorlevel 1 goto :wait

echo OK - opening browser
start "" http://127.0.0.1:8000/
echo.
echo Site: http://127.0.0.1:8000/
echo Do NOT close the window titled: Herba-Backend-KEEP-OPEN
echo.
pause
exit /b 0

:fail
echo [FAIL] Backend did not start. Check the Herba-Backend window for errors.
pause
exit /b 1
