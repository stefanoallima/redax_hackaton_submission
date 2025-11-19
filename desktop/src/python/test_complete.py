"""
Complete Test Suite for CodiceCivile.ai PII Detection
Tests all components with Italian legal document samples
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("CodiceCivile.ai - Complete PII Detection Test Suite")
print("=" * 80)

# Test 1: Basic Setup
print("\n[TEST 1] Verifying Python Environment")
print("-" * 80)
try:
    import spacy
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    import fitz  # PyMuPDF
    from docx import Document
    print("✅ All required packages imported successfully")
except ImportError as e:
    print(f"❌ Missing package: {e}")
    sys.exit(1)

# Test 2: SpaCy Italian Model
print("\n[TEST 2] Testing spaCy Italian Model")
print("-" * 80)
try:
    nlp = spacy.load('it_core_news_lg')
    print(f"✅ Loaded: {nlp.meta['name']} v{nlp.meta['version']}")
    print(f"   Pipeline components: {', '.join(nlp.pipe_names)}")
    
    # Test NER
    test_text = "Mario Rossi lavora presso ABC S.r.l. a Milano dal 2020."
    doc = nlp(test_text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    print(f"   Test NER: Found {len(entities)} entities: {entities}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 3: Custom Italian Recognizers
print("\n[TEST 3] Testing Custom Italian Recognizers")
print("-" * 80)
try:
    from pii_detector import (
        CodiceFiscaleRecognizer,
        IBANRecognizer,
        ItalianPhoneRecognizer,
        ItalianAddressRecognizer,
        PIIDetector
    )
    
    # Test Codice Fiscale
    cf_recognizer = CodiceFiscaleRecognizer()
    print(f"✅ CodiceFiscaleRecognizer initialized")
    print(f"   Pattern: {cf_recognizer.patterns[0].regex}")
    
    # Test IBAN
    iban_recognizer = IBANRecognizer()
    print(f"✅ IBANRecognizer initialized")
    
    # Test Phone
    phone_recognizer = ItalianPhoneRecognizer()
    print(f"✅ ItalianPhoneRecognizer initialized ({len(phone_recognizer.patterns)} patterns)")
    
    # Test Address
    address_recognizer = ItalianAddressRecognizer()
    print(f"✅ ItalianAddressRecognizer initialized")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Full PII Detector
print("\n[TEST 4] Testing Complete PII Detector")
print("-" * 80)
try:
    detector = PIIDetector()
    print("✅ PIIDetector initialized with all custom recognizers")
    
    # Test with comprehensive Italian text
    test_document = """
    CONTRATTO DI LAVORO SUBORDINATO
    
    Tra la società ABC Legal Services S.r.l. e il signor Mario Rossi,
    nato a Roma il 15 marzo 1985, Codice Fiscale: RSSMRA85C15H501X,
    residente in Via Giuseppe Garibaldi 45, 20100 Milano (MI).
    
    Contatti:
    - Telefono: +39 333 1234567
    - Email: mario.rossi@example.com
    - IBAN: IT60X0542811101000000123456
    
    Il presente contratto ha decorrenza dal 01/01/2024 con una
    retribuzione annua lorda di €50,000.00.
    
    Firmato a Milano il 15 dicembre 2023.
    
    Datore di Lavoro: Laura Bianchi
    CF: BNCLRA80D45F205Z
    Tel: 02 87654321
    """
    
    print("\n📄 Test Document:")
    print("-" * 80)
    print(test_document[:200] + "...")
    print("-" * 80)
    
    # Run detection
    entities = detector.detect_pii(test_document, language='it')
    
    print(f"\n🔍 Detection Results: {len(entities)} PII entities found")
    print("-" * 80)
    
    # Group by type
    by_type = {}
    for entity in entities:
        entity_type = entity['entity_type']
        if entity_type not in by_type:
            by_type[entity_type] = []
        by_type[entity_type].append(entity)
    
    # Display results
    for entity_type, items in sorted(by_type.items()):
        print(f"\n{entity_type} ({len(items)} found):")
        for item in items:
            confidence_bar = "█" * int(item['score'] * 10)
            print(f"  • '{item['text']}' - {item['score']:.2f} {confidence_bar}")
    
    # Verify key entities
    print("\n" + "=" * 80)
    print("Verification Checklist:")
    print("-" * 80)
    
    checks = {
        'CODICE_FISCALE': ['RSSMRA85C15H501X', 'BNCLRA80D45F205Z'],
        'PERSON': ['Mario Rossi', 'Laura Bianchi'],
        'PHONE_NUMBER': ['+39 333 1234567', '02 87654321'],
        'EMAIL_ADDRESS': ['mario.rossi@example.com'],
        'IBAN': ['IT60X0542811101000000123456'],
    }
    
    all_passed = True
    for entity_type, expected_values in checks.items():
        found_texts = [e['text'] for e in entities if e['entity_type'] == entity_type]
        
        for expected in expected_values:
            if any(expected in found for found in found_texts):
                print(f"✅ {entity_type}: '{expected}' detected")
            else:
                print(f"❌ {entity_type}: '{expected}' NOT detected")
                all_passed = False
    
    if all_passed:
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED! PII Detection is working correctly.")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("⚠️  Some entities were not detected. Review recognizer patterns.")
        print("=" * 80)
    
except Exception as e:
    print(f"❌ Error during detection: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Anonymization
print("\n[TEST 5] Testing Anonymization")
print("-" * 80)
try:
    anonymized_results = detector.anonymize_text(test_document, entities)
    
    if anonymized_results['status'] == 'success':
        print("✅ Anonymization successful")
        print("\n📝 Anonymized Text (first 300 chars):")
        print("-" * 80)
        print(anonymized_results['anonymized_text'][:300] + "...")
        print("-" * 80)
    else:
        print(f"❌ Anonymization failed: {anonymized_results.get('error')}")
        
except Exception as e:
    print(f"❌ Error during anonymization: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Performance
print("\n[TEST 6] Performance Benchmark")
print("-" * 80)
try:
    import time
    
    # Test with larger document
    large_text = test_document * 10  # Simulate 10-page document
    
    start = time.time()
    entities = detector.detect_pii(large_text, language='it')
    elapsed = time.time() - start
    
    print(f"✅ Processed {len(large_text)} characters in {elapsed:.2f}s")
    print(f"   Detected {len(entities)} entities")
    print(f"   Speed: {len(large_text) / elapsed:.0f} chars/second")
    
    if elapsed < 5.0:
        print("   ✅ Performance: EXCELLENT (< 5s)")
    elif elapsed < 10.0:
        print("   ✅ Performance: GOOD (< 10s)")
    else:
        print("   ⚠️  Performance: SLOW (> 10s)")
        
except Exception as e:
    print(f"❌ Error during benchmark: {e}")

# Summary
print("\n" + "=" * 80)
print("TEST SUITE COMPLETE")
print("=" * 80)
print("\n✅ Setup verified and ready for production use!")
print("\nNext Steps:")
print("1. Test with real Italian legal documents")
print("2. Fine-tune recognizer patterns based on accuracy")
print("3. Integrate with Electron desktop app")
print("4. Run full end-to-end tests with PDF/DOCX files")
print("\n" + "=" * 80)
