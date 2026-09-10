@echo off
echo Starting Fluxline...

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker is not running.
  pause
  exit /b 1
)

if not exist .env (
  copy .env.example .env
  echo Please edit .env before continuing.
  notepad .env
  pause
)

if not exist data mkdir data
if not exist uploads mkdir uploads

docker-compose up --build -d

echo.
echo Fluxline started!
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo.
pause
