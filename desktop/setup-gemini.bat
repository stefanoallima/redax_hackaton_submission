@echo off
REM Gemini Integration Setup Script for Windows
REM This script installs the required dependencies and helps configure the API key

echo ========================================
echo Gemini Integration Setup
echo ========================================
echo.

REM Step 1: Install Python dependency
echo [1/3] Installing google-generativeai library...
cd src\python
pip install google-generativeai==0.8.3
if %errorlevel% neq 0 (
    echo ERROR: Failed to install google-generativeai
    echo Please run manually: pip install google-generativeai==0.8.3
    pause
    exit /b 1
)
echo ✓ Library installed successfully
echo.

REM Step 2: Check for .env file
cd ..\..
echo [2/3] Checking for .env file...
if exist .env (
    echo ✓ .env file already exists
) else (
    echo Creating .env file from template...
    copy .env.example .env
    echo ✓ .env file created
    echo.
    echo ⚠ IMPORTANT: You need to add your Gemini API key to .env
    echo.
    echo Steps:
    echo 1. Go to https://aistudio.google.com/app/apikey
    echo 2. Click "Create API Key"
    echo 3. Copy the key (starts with AIza...)
    echo 4. Edit desktop\.env and replace 'your_gemini_api_key_here' with your actual key
    echo.
    notepad .env
)
echo.

REM Step 3: Verify setup
echo [3/3] Verifying setup...
python -c "import google.generativeai; print('✓ Python library ready')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠ Warning: Could not verify Python library
)

findstr /C:"GEMINI_API_KEY=AIza" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ API key configured in .env
) else (
    echo ⚠ Warning: API key not configured in .env
    echo   Please edit .env and add your Gemini API key
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure your API key is in desktop\.env
echo 2. Run: npm run electron:dev
echo 3. Select "Gemini Scan" mode in the app
echo 4. Upload a PDF and click "Analizza con Gemini AI"
echo.
echo For detailed instructions, see: GEMINI_SETUP_GUIDE.md
echo.

pause
