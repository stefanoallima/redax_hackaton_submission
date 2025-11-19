@echo off
echo ====================================
echo CodiceCivile Redact - Desktop App
echo ====================================
echo.
echo Starting Vite dev server and Electron...
echo.
echo This will open TWO windows:
echo 1. Vite dev server (port 5173)
echo 2. Electron desktop app
echo.
echo Keep this terminal open!
echo Press Ctrl+C to stop both.
echo.
echo ====================================
echo.

cd /d "%~dp0"
npm run electron:dev
