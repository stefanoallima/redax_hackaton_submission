@echo off
REM DigitalOcean Deployment Preparation Script
REM Prepares the React app for web deployment with interactive text selection

echo =========================================
echo DigitalOcean Deployment Preparation
echo =========================================
echo.

REM Step 1: Check prerequisites
echo Step 1: Checking prerequisites...
echo.

where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found. Please install Node.js first.
    pause
    exit /b 1
)

where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git not found. Please install Git first.
    pause
    exit /b 1
)

echo [OK] Node.js found
echo [OK] Git found
echo.

REM Step 2: Install dependencies
echo Step 2: Installing dependencies...
cd desktop
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm install failed
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Step 3: Build production version
echo Step 3: Building production version...
call npm run build:renderer
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)
echo [OK] Build complete
echo.

REM Step 4: Verify build output
echo Step 4: Verifying build output...
if not exist "dist\renderer\index.html" (
    echo [ERROR] Build output not found
    pause
    exit /b 1
)
echo [OK] Build output verified
echo.

REM Step 5: Check backend files
echo Step 5: Checking backend files...
cd ..
if not exist "desktop\src\python\web_api.py" (
    echo [ERROR] Backend API file not found
    pause
    exit /b 1
)
if not exist "desktop\src\python\requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)
echo [OK] Backend files present
echo.

REM Step 6: Show deployment summary
echo =========================================
echo Deployment Ready!
echo =========================================
echo.
echo Frontend build: desktop\dist\renderer\
echo Backend files: desktop\src\python\
echo Shared backend: shared_backend\
echo.
echo Next steps:
echo.
echo 1. Push code to GitHub:
echo    git add .
echo    git commit -m "Prepare for DigitalOcean deployment"
echo    git push origin main
echo.
echo 2. Go to: https://cloud.digitalocean.com/apps
echo.
echo 3. Create new app from GitHub repo
echo.
echo 4. Configure services (see DIGITALOCEAN_DEPLOYMENT_GUIDE.md)
echo.
echo 5. Deploy and test!
echo.
echo See DIGITALOCEAN_DEPLOYMENT_GUIDE.md for detailed instructions
echo.
pause
