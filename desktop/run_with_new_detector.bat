@echo off
echo Starting Desktop App with NEW PII Detector (with fixes)...
set USE_NEW_PII_DETECTOR=true
cd src\python
python main.py
pause