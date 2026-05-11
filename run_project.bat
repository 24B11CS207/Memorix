@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found: .venv\Scripts\python.exe
  echo Create/install dependencies first, then run this file again.
  pause
  exit /b 1
)

echo Starting Memorix / DQMS...
echo.
echo App URL:
echo   http://127.0.0.1:8000/
echo.
echo Keep this window open while using the app.
echo Press CTRL+C here to stop the server.
echo.

".venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 (
  echo.
  echo Migration failed. Check the error above.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload

echo.
echo Server stopped.
pause
