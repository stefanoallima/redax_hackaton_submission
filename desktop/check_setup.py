"""
Quick Setup Checker
Checks what's installed and what's missing
"""
import sys
import subprocess

print("=" * 80)
print("CodiceCivile.ai - Setup Status Check")
print("=" * 80)
print()

# Check Python version
print("[1] Python Version")
print("-" * 80)
print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
print()

# Check packages
print("[2] Required Packages")
print("-" * 80)

packages = {
    'spacy': 'spaCy NLP library',
    'presidio_analyzer': 'Microsoft Presidio Analyzer',
    'presidio_anonymizer': 'Microsoft Presidio Anonymizer',
    'fitz': 'PyMuPDF (PDF processing)',
    'docx': 'python-docx (DOCX processing)',
    'llama_cpp': 'llama-cpp-python (LLM support)'
}

missing_packages = []
for package, description in packages.items():
    try:
        __import__(package)
        print(f"✅ {package:25} - {description}")
    except ImportError:
        print(f"❌ {package:25} - {description} (NOT INSTALLED)")
        missing_packages.append(package)

print()

# Check spaCy model
print("[3] spaCy Italian Model")
print("-" * 80)
try:
    import spacy
    nlp = spacy.load('it_core_news_lg')
    print(f"✅ Model loaded: {nlp.meta['name']} (version {nlp.meta['version']})")
except:
    print("❌ Italian model 'it_core_news_lg' not found")
    missing_packages.append('spacy-model')

print()

# Check Cerbero model
print("[4] Cerbero-7B Model")
print("-" * 80)
from pathlib import Path
model_path = Path(__file__).parent.parent / 'models' / 'cerbero-7b.gguf'
if model_path.exists():
    size_gb = model_path.stat().st_size / (1024**3)
    print(f"✅ Model found: {model_path} ({size_gb:.2f} GB)")
else:
    print(f"❌ Model not found: {model_path}")
    missing_packages.append('cerbero-model')

print()

# Summary
print("=" * 80)
if missing_packages:
    print("⚠️  SETUP INCOMPLETE")
    print("=" * 80)
    print()
    print("Missing components:")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    print()
    print("To install missing components, run:")
    print()
    if 'spacy' in missing_packages or 'presidio_analyzer' in missing_packages:
        print("  pip install -r requirements.txt")
    if 'llama_cpp' in missing_packages:
        print("  pip install llama-cpp-python")
    if 'spacy-model' in missing_packages:
        print("  python -m spacy download it_core_news_lg")
    if 'cerbero-model' in missing_packages:
        print("  # Download Cerbero-7B manually from:")
        print("  # https://huggingface.co/mradermacher/Cerbero-7B-GGUF")
        print("  # File: Cerbero-7B.Q4_K_M.gguf")
    print()
    sys.exit(1)
else:
    print("✅ ALL COMPONENTS INSTALLED!")
    print("=" * 80)
    print()
    print("Ready to run:")
    print("  python test_basic.py")
    print("  cd ..\.. && START_APP.bat")
    print()
    sys.exit(0)
