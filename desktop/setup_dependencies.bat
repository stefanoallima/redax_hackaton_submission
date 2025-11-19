@echo off
REM ====================================
REM CodiceCivile.ai - Dependency Setup
REM ====================================
REM This script downloads and installs all required dependencies

echo ====================================
echo CodiceCivile.ai - Setup Script
echo ====================================
echo.
echo This will install:
echo - Python packages
echo - spaCy Italian model
echo - Cerbero-7B LLM model
echo - Tesseract OCR (optional)
echo.
echo Estimated download: ~5GB
echo Estimated time: 10-20 minutes
echo.
pause

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

echo.
echo [1/5] Installing Python packages...
echo ====================================
cd src\python

REM Install core packages
pip install --upgrade pip
pip install -r requirements.txt

REM Install LLM package
pip install llama-cpp-python

REM Install OCR packages (optional)
pip install pytesseract pillow

echo.
echo [2/5] Downloading spaCy Italian model...
echo ====================================
python -m spacy download it_core_news_lg

echo.
echo [3/5] Creating models directory...
echo ====================================
cd ..\..
if not exist "models" mkdir models

echo.
echo [4/5] Downloading Cerbero-7B model...
echo ====================================
echo.
echo IMPORTANT: This is a 4.1GB download!
echo.
echo Please download manually:
echo 1. Visit: https://huggingface.co/mradermacher/Cerbero-7B-GGUF
echo 2. Download: Cerbero-7B.Q4_K_M.gguf (4.1GB)
echo 3. Place in: %CD%\models\cerbero-7b.gguf
echo.
echo Alternative (if you have git-lfs):
echo   git lfs install
echo   git clone https://huggingface.co/mradermacher/Cerbero-7B-GGUF
echo   copy Cerbero-7B-GGUF\Cerbero-7B.Q4_K_M.gguf models\cerbero-7b.gguf
echo.

REM Try to download with curl if available
where curl >nul 2>&1
if not errorlevel 1 (
    echo Attempting download with curl...
    curl -L -o models\cerbero-7b.gguf "https://huggingface.co/mradermacher/Cerbero-7B-GGUF/resolve/main/Cerbero-7B.Q4_K_M.gguf"
    if errorlevel 1 (
        echo Download failed. Please download manually.
    ) else (
        echo Download complete!
    )
) else (
    echo curl not found. Please download manually.
)

echo.
echo [5/5] Optional: Tesseract OCR
echo ====================================
echo.
echo For scanned document support, install Tesseract OCR:
echo.
echo 1. Download: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Install: tesseract-ocr-w64-setup-5.3.3.20231005.exe
echo 3. During install, select "Italian" language data
echo 4. Add to PATH: C:\Program Files\Tesseract-OCR
echo.

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Verify Cerbero-7B model is in: models\cerbero-7b.gguf
echo 2. Run tests: cd src\python ^&^& python test_basic.py
echo 3. Start app: START_APP.bat
echo.
pause
