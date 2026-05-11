$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Host "Virtual environment not found: .venv\Scripts\python.exe" -ForegroundColor Red
  Write-Host "Create/install dependencies first, then run this script again."
  Read-Host "Press Enter to exit"
  exit 1
}

Write-Host "Starting Memorix / DQMS..." -ForegroundColor Cyan
Write-Host ""
Write-Host "App URL:"
Write-Host "  http://127.0.0.1:8000/"
Write-Host ""
Write-Host "Keep this window open while using the app."
Write-Host "Press CTRL+C here to stop the server."
Write-Host ""

.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
