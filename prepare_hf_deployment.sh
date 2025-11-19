#!/bin/bash
# HuggingFace Spaces Deployment Preparation Script
# Run this script to create deployment package

set -e  # Exit on error

echo "========================================="
echo "HuggingFace Spaces Deployment Preparation"
echo "========================================="
echo ""

# 1. Create deployment directory
echo "Step 1: Creating deployment directory..."
rm -rf huggingface-deploy 2>/dev/null || true
mkdir -p huggingface-deploy
cd huggingface-deploy

# 2. Copy web application files
echo "Step 2: Copying web application files..."
cp ../web/app.py .
cp ../web/requirements.txt .
cp ../web/README.md .

# 3. Copy shared_backend directory
echo "Step 3: Copying shared_backend directory..."
cp -r ../shared_backend .

# 4. Verify structure
echo ""
echo "Step 4: Verifying deployment structure..."
echo ""
echo "Files in deployment directory:"
ls -lh

echo ""
echo "Shared backend structure:"
ls -lh shared_backend/

echo ""
echo "Core modules:"
ls -lh shared_backend/core/ 2>/dev/null || echo "Warning: core/ directory not found"

echo ""
echo "Detectors:"
ls -lh shared_backend/detectors/ 2>/dev/null || echo "Warning: detectors/ directory not found"

echo ""
echo "Config:"
ls -lh shared_backend/config/ 2>/dev/null || echo "Warning: config/ directory not found"

echo ""
echo "Utils:"
ls -lh shared_backend/utils/ 2>/dev/null || echo "Warning: utils/ directory not found"

# 5. Verify critical files exist
echo ""
echo "Step 5: Checking critical files..."
MISSING_FILES=0

check_file() {
    if [ ! -f "$1" ]; then
        echo "❌ Missing: $1"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "✅ Found: $1"
    fi
}

check_file "app.py"
check_file "requirements.txt"
check_file "README.md"
check_file "shared_backend/__init__.py"
check_file "shared_backend/core/gemini_client.py"
check_file "shared_backend/core/pii_detector_integrated.py"
check_file "shared_backend/core/learned_entities_db.py"
check_file "shared_backend/core/document_processor.py"
check_file "shared_backend/core/redaction_exporter.py"

echo ""
if [ $MISSING_FILES -eq 0 ]; then
    echo "✅ All critical files present!"
else
    echo "❌ Warning: $MISSING_FILES critical files missing"
    echo "   Review the structure and ensure all shared_backend files are included"
fi

# 6. Create .gitignore for deployment
echo ""
echo "Step 6: Creating .gitignore for deployment..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.pyc
.pytest_cache/

# Environment
.env
.env.local

# Logs
*.log

# Temporary
*.tmp
tmp/
EOF

echo "✅ .gitignore created"

# 7. Initialize git if needed
echo ""
echo "Step 7: Initializing git repository..."
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# 8. Display next steps
echo ""
echo "========================================="
echo "✅ Deployment package ready!"
echo "========================================="
echo ""
echo "Location: $(pwd)"
echo ""
echo "Next steps:"
echo ""
echo "1. Add HuggingFace remote:"
echo "   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/redactor-ai"
echo ""
echo "2. Stage all files:"
echo "   git add ."
echo ""
echo "3. Commit:"
echo "   git commit -m \"Initial deployment: Redactor AI web app\""
echo ""
echo "4. Push to HuggingFace:"
echo "   git push hf main"
echo ""
echo "5. Configure HF Spaces:"
echo "   - Enable Persistent Storage"
echo "   - Add Secret: GEMINI_API_KEY"
echo "   - Set Hardware: CPU Upgrade (8 vCPU, 32GB RAM)"
echo ""
echo "See HUGGINGFACE_DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
