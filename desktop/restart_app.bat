@echo off
echo Cleaning up processes...
powershell -ExecutionPolicy Bypass -File ./scripts/cleanup-ports.ps1

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak

echo.
echo Starting Electron app...
npm run electron:dev
