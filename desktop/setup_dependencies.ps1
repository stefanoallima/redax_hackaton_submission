# ====================================
# CodiceCivile.ai - Dependency Setup (PowerShell)
# ====================================

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "CodiceCivile.ai - Setup Script" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will install:" -ForegroundColor Yellow
Write-Host "- Python packages"
Write-Host "- spaCy Italian model"
Write-Host "- Cerbero-7B LLM model (4.1GB)"
Write-Host "- Tesseract OCR (optional)"
Write-Host ""
Write-Host "Estimated download: ~5GB" -ForegroundColor Yellow
Write-Host "Estimated time: 10-20 minutes" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "Continue? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Setup cancelled." -ForegroundColor Red
    exit
}

# Check Python
Write-Host ""
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Install Python packages
Write-Host ""
Write-Host "[2/6] Installing Python packages..." -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

Set-Location src\python

Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "Installing core packages..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Installing LLM support..." -ForegroundColor Cyan
pip install llama-cpp-python

Write-Host "Installing OCR support..." -ForegroundColor Cyan
pip install pytesseract pillow

# Download spaCy model
Write-Host ""
Write-Host "[3/6] Downloading spaCy Italian model..." -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
python -m spacy download it_core_news_lg

# Create models directory
Write-Host ""
Write-Host "[4/6] Creating models directory..." -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

Set-Location ..\..
if (-not (Test-Path "models")) {
    New-Item -ItemType Directory -Path "models" | Out-Null
    Write-Host "Created: models\" -ForegroundColor Green
}

# Download Cerbero-7B
Write-Host ""
Write-Host "[5/6] Downloading Cerbero-7B model..." -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: This is a 4.1GB download!" -ForegroundColor Yellow
Write-Host ""

$modelPath = "models\cerbero-7b.gguf"
$modelUrl = "https://huggingface.co/mradermacher/Cerbero-7B-GGUF/resolve/main/Cerbero-7B.Q4_K_M.gguf"

if (Test-Path $modelPath) {
    Write-Host "Model already exists: $modelPath" -ForegroundColor Yellow
    $overwrite = Read-Host "Re-download? (y/n)"
    if ($overwrite -ne 'y') {
        Write-Host "Skipping download." -ForegroundColor Cyan
    } else {
        Write-Host "Downloading Cerbero-7B (this may take 10-20 minutes)..." -ForegroundColor Cyan
        try {
            Invoke-WebRequest -Uri $modelUrl -OutFile $modelPath -UseBasicParsing
            Write-Host "Download complete!" -ForegroundColor Green
        } catch {
            Write-Host "Download failed: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "Please download manually:" -ForegroundColor Yellow
            Write-Host "1. Visit: https://huggingface.co/mradermacher/Cerbero-7B-GGUF"
            Write-Host "2. Download: Cerbero-7B.Q4_K_M.gguf (4.1GB)"
            Write-Host "3. Place in: $PWD\models\cerbero-7b.gguf"
        }
    }
} else {
    Write-Host "Downloading Cerbero-7B (this may take 10-20 minutes)..." -ForegroundColor Cyan
    Write-Host "URL: $modelUrl" -ForegroundColor Gray
    
    try {
        # Show progress
        $ProgressPreference = 'Continue'
        Invoke-WebRequest -Uri $modelUrl -OutFile $modelPath -UseBasicParsing
        Write-Host "Download complete!" -ForegroundColor Green
    } catch {
        Write-Host "Download failed: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download manually:" -ForegroundColor Yellow
        Write-Host "1. Visit: https://huggingface.co/mradermacher/Cerbero-7B-GGUF"
        Write-Host "2. Download: Cerbero-7B.Q4_K_M.gguf (4.1GB)"
        Write-Host "3. Place in: $PWD\models\cerbero-7b.gguf"
    }
}

# Tesseract OCR
Write-Host ""
Write-Host "[6/6] Optional: Tesseract OCR" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "For scanned document support, install Tesseract OCR:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Download: https://github.com/UB-Mannheim/tesseract/wiki"
Write-Host "2. Install: tesseract-ocr-w64-setup-5.3.3.20231005.exe"
Write-Host "3. During install, select 'Italian' language data"
Write-Host "4. Add to PATH: C:\Program Files\Tesseract-OCR"
Write-Host ""

$installTesseract = Read-Host "Open Tesseract download page? (y/n)"
if ($installTesseract -eq 'y') {
    Start-Process "https://github.com/UB-Mannheim/tesseract/wiki"
}

# Summary
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Verify installations
Write-Host "Verification:" -ForegroundColor Yellow
Write-Host ""

# Check spaCy model
try {
    python -c "import spacy; nlp = spacy.load('it_core_news_lg'); print('✅ spaCy Italian model: OK')"
} catch {
    Write-Host "❌ spaCy Italian model: FAILED" -ForegroundColor Red
}

# Check Cerbero model
if (Test-Path $modelPath) {
    $fileSize = (Get-Item $modelPath).Length / 1GB
    Write-Host "✅ Cerbero-7B model: OK ($([math]::Round($fileSize, 2)) GB)" -ForegroundColor Green
} else {
    Write-Host "❌ Cerbero-7B model: NOT FOUND" -ForegroundColor Red
}

# Check packages
try {
    python -c "import presidio_analyzer, presidio_anonymizer, fitz, docx; print('✅ Python packages: OK')"
} catch {
    Write-Host "❌ Python packages: FAILED" -ForegroundColor Red
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run tests: cd src\python; python test_basic.py"
Write-Host "2. Start app: .\START_APP.bat"
Write-Host ""

Read-Host "Press Enter to exit"
