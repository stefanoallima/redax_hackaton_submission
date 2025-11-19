@echo off
REM Desktop App - Port Cleanup and Restart (Batch Wrapper)

echo Starting port cleanup and restart...
powershell -ExecutionPolicy Bypass -File "%~dp0fix_and_restart.ps1"

pause
