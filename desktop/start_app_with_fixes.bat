@echo off
echo ========================================
echo Starting CodiceCivile Redact Desktop App
echo With NEW PII Detector (includes all fixes)
echo ========================================
echo.

REM Set environment variable for new detector
set USE_NEW_PII_DETECTOR=true
echo [OK] Enabled NEW PII detector with fixes

REM Start the Electron app (includes both frontend and backend)
echo [Starting] Launching Electron app...
npm run electron:dev

pause