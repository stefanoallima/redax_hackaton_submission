"""
Test script to verify PII detection setup
"""
import spacy
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

print("=" * 60)
print("Testing CodiceCivile.ai PII Detection Setup")
print("=" * 60)

# Test 1: SpaCy Italian Model
print("\n1. Testing spaCy Italian model...")
try:
    nlp = spacy.load('it_core_news_lg')
    print(f"   SUCCESS: Loaded {nlp.meta['name']} v{nlp.meta['version']}")
    print(f"   Pipeline: {nlp.pipe_names}")

    # Test with Italian text
    doc = nlp("Mario Rossi lavora a Milano dal 2020.")
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    print(f"   Test entities found: {entities}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: Presidio Analyzer
print("\n2. Testing Presidio Analyzer...")
try:
    # Configure with Italian model
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [
            {"lang_code": "it", "model_name": "it_core_news_lg"},
            {"lang_code": "en", "model_name": "en_core_web_lg"}
        ]
    }

    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()

    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["it", "en"])
    print("   SUCCESS: Presidio analyzer initialized")

    # Test with Italian PII
    test_text = """
    Mario Rossi abita a Via Roma 123, 20100 Milano.
    Email: mario.rossi@example.it
    Telefono: +39 02 1234567
    """

    results = analyzer.analyze(text=test_text, language='it')
    print(f"   Detected {len(results)} PII entities:")

    for result in results:
        detected_text = test_text[result.start:result.end]
        print(f"     - {result.entity_type}: '{detected_text}' (score: {result.score:.2f})")

except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Italian-specific PII patterns
print("\n3. Testing Italian-specific patterns...")
try:
    # Test Codice Fiscale detection (custom recognizer would go here)
    test_cf = "RSSMRA80A01H501X"  # Sample Codice Fiscale
    print(f"   Sample Codice Fiscale: {test_cf}")
    print("   NOTE: Custom Italian recognizers need to be added in pii_detector.py")

except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 60)
print("Setup verification complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Implement custom Italian recognizers in pii_detector.py")
print("2. Add Codice Fiscale pattern matching")
print("3. Test with real Italian legal documents")
print("=" * 60)
