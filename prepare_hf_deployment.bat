@echo off
REM HuggingFace Spaces Deployment Preparation Script (Windows)
REM Run this script to create deployment package

echo =========================================
echo HuggingFace Spaces Deployment Preparation
echo =========================================
echo.

REM 1. Create deployment directory
echo Step 1: Creating deployment directory...
if exist huggingface-deploy rmdir /s /q huggingface-deploy
mkdir huggingface-deploy
cd huggingface-deploy

REM 2. Copy web application files
echo Step 2: Copying web application files...
copy ..\web\app.py . >nul
copy ..\web\requirements.txt . >nul
copy ..\web\README.md . >nul

REM 3. Copy shared_backend directory
echo Step 3: Copying shared_backend directory...
xcopy /E /I /Q ..\shared_backend shared_backend >nul

REM 4. Verify structure
echo.
echo Step 4: Verifying deployment structure...
echo.
echo Files in deployment directory:
dir /B

echo.
echo Shared backend structure:
dir /B shared_backend

echo.
echo Core modules:
dir /B shared_backend\core 2>nul || echo Warning: core\ directory not found

echo.
echo Detectors:
dir /B shared_backend\detectors 2>nul || echo Warning: detectors\ directory not found

echo.
echo Config:
dir /B shared_backend\config 2>nul || echo Warning: config\ directory not found

echo.
echo Utils:
dir /B shared_backend\utils 2>nul || echo Warning: utils\ directory not found

REM 5. Verify critical files exist
echo.
echo Step 5: Checking critical files...

set MISSING_FILES=0

if exist app.py (echo [OK] app.py) else (echo [MISSING] app.py & set /a MISSING_FILES+=1)
if exist requirements.txt (echo [OK] requirements.txt) else (echo [MISSING] requirements.txt & set /a MISSING_FILES+=1)
if exist README.md (echo [OK] README.md) else (echo [MISSING] README.md & set /a MISSING_FILES+=1)
if exist shared_backend\__init__.py (echo [OK] shared_backend\__init__.py) else (echo [MISSING] shared_backend\__init__.py & set /a MISSING_FILES+=1)
if exist shared_backend\core\gemini_client.py (echo [OK] shared_backend\core\gemini_client.py) else (echo [MISSING] shared_backend\core\gemini_client.py & set /a MISSING_FILES+=1)
if exist shared_backend\core\pii_detector_integrated.py (echo [OK] shared_backend\core\pii_detector_integrated.py) else (echo [MISSING] shared_backend\core\pii_detector_integrated.py & set /a MISSING_FILES+=1)
if exist shared_backend\core\learned_entities_db.py (echo [OK] shared_backend\core\learned_entities_db.py) else (echo [MISSING] shared_backend\core\learned_entities_db.py & set /a MISSING_FILES+=1)
if exist shared_backend\core\document_processor.py (echo [OK] shared_backend\core\document_processor.py) else (echo [MISSING] shared_backend\core\document_processor.py & set /a MISSING_FILES+=1)
if exist shared_backend\core\redaction_exporter.py (echo [OK] shared_backend\core\redaction_exporter.py) else (echo [MISSING] shared_backend\core\redaction_exporter.py & set /a MISSING_FILES+=1)

echo.
if %MISSING_FILES%==0 (
    echo [OK] All critical files present!
) else (
    echo [WARNING] %MISSING_FILES% critical files missing
    echo    Review the structure and ensure all shared_backend files are included
)

REM 6. Create .gitignore for deployment
echo.
echo Step 6: Creating .gitignore for deployment...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *.pyc
echo .pytest_cache/
echo.
echo # Environment
echo .env
echo .env.local
echo.
echo # Logs
echo *.log
echo.
echo # Temporary
echo *.tmp
echo tmp/
) > .gitignore

echo [OK] .gitignore created

REM 7. Initialize git if needed
echo.
echo Step 7: Initializing git repository...
if not exist .git (
    git init
    echo [OK] Git initialized
) else (
    echo [OK] Git already initialized
)

REM 8. Display next steps
echo.
echo =========================================
echo [OK] Deployment package ready!
echo =========================================
echo.
echo Location: %cd%
echo.
echo Next steps:
echo.
echo 1. Add HuggingFace remote:
echo    git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/redactor-ai
echo.
echo 2. Stage all files:
echo    git add .
echo.
echo 3. Commit:
echo    git commit -m "Initial deployment: Redactor AI web app"
echo.
echo 4. Push to HuggingFace:
echo    git push hf main
echo.
echo 5. Configure HF Spaces:
echo    - Enable Persistent Storage
echo    - Add Secret: GEMINI_API_KEY
echo    - Set Hardware: CPU Upgrade (8 vCPU, 32GB RAM^)
echo.
echo See HUGGINGFACE_DEPLOYMENT_GUIDE.md for detailed instructions
echo.
pause
