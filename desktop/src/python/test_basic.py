"""
Basic Test - Check Python Environment and Imports
"""
import sys
from pathlib import Path

print("=" * 80)
print("CodiceCivile.ai - Basic Environment Test")
print("=" * 80)

# Test 1: Python Version
print("\n[TEST 1] Python Version")
print("-" * 80)
print(f"Python: {sys.version}")
print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Test 2: Check Packages
print("\n[TEST 2] Checking Required Packages")
print("-" * 80)

packages = {
    'spacy': 'spaCy NLP library',
    'presidio_analyzer': 'Microsoft Presidio Analyzer',
    'presidio_anonymizer': 'Microsoft Presidio Anonymizer',
    'fitz': 'PyMuPDF (PDF processing)',
    'docx': 'python-docx (DOCX processing)'
}

missing = []
for package, description in packages.items():
    try:
        __import__(package)
        print(f"✅ {package:25} - {description}")
    except ImportError:
        print(f"❌ {package:25} - {description} (NOT INSTALLED)")
        missing.append(package)

if missing:
    print("\n" + "=" * 80)
    print("⚠️  MISSING PACKAGES")
    print("=" * 80)
    print("\nTo install missing packages, run:")
    print(f"pip install {' '.join(missing)}")
    print("\nFor PyMuPDF, use: pip install PyMuPDF")
    print("For python-docx, use: pip install python-docx")
    sys.exit(1)

# Test 3: Check spaCy Italian Model
print("\n[TEST 3] Checking spaCy Italian Model")
print("-" * 80)
try:
    import spacy
    nlp = spacy.load('it_core_news_lg')
    print(f"✅ Model loaded: {nlp.meta['name']}")
    print(f"   Version: {nlp.meta['version']}")
    print(f"   Language: {nlp.meta['lang']}")
except OSError:
    print("❌ Italian model 'it_core_news_lg' not found")
    print("\nTo install, run:")
    print("python -m spacy download it_core_news_lg")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error loading model: {e}")
    sys.exit(1)

# Test 4: Quick NER Test
print("\n[TEST 4] Quick NER Test")
print("-" * 80)
test_text = "Mario Rossi lavora a Milano."
doc = nlp(test_text)
entities = [(ent.text, ent.label_) for ent in doc.ents]
print(f"Text: '{test_text}'")
print(f"Entities found: {entities}")
if len(entities) > 0:
    print("✅ NER is working")
else:
    print("⚠️  No entities detected (this might be normal for simple text)")

# Test 5: Check Project Files
print("\n[TEST 5] Checking Project Files")
print("-" * 80)
project_files = [
    'pii_detector.py',
    'document_analyzer.py',
    'detection_config.py',
    'llm_validator.py',
    'visual_pii_detector.py'
]

for file in project_files:
    file_path = Path(__file__).parent / file
    if file_path.exists():
        print(f"✅ {file}")
    else:
        print(f"❌ {file} (NOT FOUND)")

print("\n" + "=" * 80)
print("✅ BASIC SETUP COMPLETE!")
print("=" * 80)
print("\nNext steps:")
print("1. Run: python test_complete.py")
print("2. Test with real documents")
print("3. Start the desktop app")
print("=" * 80)
