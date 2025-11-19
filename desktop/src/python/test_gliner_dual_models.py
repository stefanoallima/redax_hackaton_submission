"""
Test script for dual-model GLiNER strategy
Tests both Italian-specific and multilingual PII models
"""

print("=" * 70)
print("GLiNER Dual-Model Test Script")
print("=" * 70)

# Test text: Italian legal document with various PII types
TEST_TEXT = """
CONTRATTO DI LAVORO SUBORDINATO

Tra le parti:

DATORE DI LAVORO:
TechItalia S.p.A., con sede legale in Via Mazzini 45, 20123 Milano (MI)
Partita IVA: 12345678901
Rappresentata da: Dott. Giovanni Bianchi, in qualità di Amministratore Delegato

E

LAVORATORE:
Mario Rossi, nato a Roma il 15 marzo 1985
Residente in Via Mura Anteo Zamboni 22, 40126 Bologna (BO)
Codice Fiscale: RSSMRA85C15H501X
Carta d'Identità n. CA1234567, rilasciata dal Comune di Bologna il 01/01/2020

CONTATTI LAVORATORE:
Telefono: +39 333 1234567
Email: mario.rossi@example.com
PEC: mario.rossi@pec.example.it

DATI BANCARI:
IBAN: IT60 X054 2811 1010 0000 0123 456
Intestato a: Mario Rossi

CONDIZIONI ECONOMICHE:
Retribuzione mensile lorda: € 2.500,00
Data di assunzione: 01/06/2023
"""

print("\nTest Text:")
print("-" * 70)
print(TEST_TEXT[:200] + "...")
print("-" * 70)

# Step 1: Test GLiNER import
print("\n[Step 1] Testing GLiNER import...")
try:
    from gliner import GLiNER
    print("[OK] GLiNER imported successfully")
except ImportError as e:
    print(f"[FAIL] GLiNER import failed: {e}")
    print("\nTo install GLiNER, run:")
    print("  pip install gliner psutil onnxruntime")
    exit(1)

# Step 2: Load Italian-specific model
print("\n[Step 2] Loading Italian-specific model (DeepMount00/universal_ner_ita)...")
try:
    model_italian = GLiNER.from_pretrained("DeepMount00/universal_ner_ita")
    print("✓ Italian model loaded successfully")
except Exception as e:
    print(f"✗ Italian model loading failed: {e}")
    model_italian = None

# Step 3: Load multilingual PII model
print("\n[Step 3] Loading multilingual PII model (urchade/gliner_multi_pii-v1)...")
try:
    model_multilingual = GLiNER.from_pretrained("urchade/gliner_multi_pii-v1")
    print("✓ Multilingual PII model loaded successfully")
except Exception as e:
    print(f"✗ Multilingual PII model loading failed: {e}")
    model_multilingual = None

# Exit if both models failed
if model_italian is None and model_multilingual is None:
    print("\n✗ Both models failed to load. Cannot proceed with testing.")
    exit(1)

# Step 4: Test Italian model
if model_italian:
    print("\n" + "=" * 70)
    print("[Step 4] Testing Italian Model")
    print("=" * 70)

    italian_labels = [
        "persona", "nome", "cognome",
        "codice fiscale", "partita iva",
        "email", "telefono", "indirizzo",
        "iban", "data", "luogo", "azienda"
    ]

    print(f"\nLabels: {', '.join(italian_labels)}")
    print("\nDetecting entities (threshold=0.5)...")

    try:
        entities_italian = model_italian.predict_entities(
            TEST_TEXT,
            italian_labels,
            threshold=0.5
        )

        print(f"\n✓ Detected {len(entities_italian)} entities:\n")

        for i, entity in enumerate(entities_italian, 1):
            print(f"  {i:2d}. [{entity['label']:20s}] {entity['text'][:50]:50s} (score: {entity['score']:.2f})")

    except Exception as e:
        print(f"✗ Detection failed: {e}")

# Step 5: Test multilingual PII model
if model_multilingual:
    print("\n" + "=" * 70)
    print("[Step 5] Testing Multilingual PII Model")
    print("=" * 70)

    multilingual_labels = [
        "person", "email", "phone number", "address",
        "date", "organization", "location",
        "fiscal code", "vat number", "iban",
        "passport number", "identity card"
    ]

    print(f"\nLabels: {', '.join(multilingual_labels)}")
    print("\nDetecting entities (threshold=0.5)...")

    try:
        entities_multilingual = model_multilingual.predict_entities(
            TEST_TEXT,
            multilingual_labels,
            threshold=0.5
        )

        print(f"\n✓ Detected {len(entities_multilingual)} entities:\n")

        for i, entity in enumerate(entities_multilingual, 1):
            print(f"  {i:2d}. [{entity['label']:20s}] {entity['text'][:50]:50s} (score: {entity['score']:.2f})")

    except Exception as e:
        print(f"✗ Detection failed: {e}")

# Step 6: Compare models
if model_italian and model_multilingual:
    print("\n" + "=" * 70)
    print("[Step 6] Model Comparison")
    print("=" * 70)

    print(f"\nItalian model:      {len(entities_italian):3d} entities detected")
    print(f"Multilingual model: {len(entities_multilingual):3d} entities detected")

    # Find unique entities from each model
    italian_texts = {e['text'] for e in entities_italian}
    multilingual_texts = {e['text'] for e in entities_multilingual}

    only_italian = italian_texts - multilingual_texts
    only_multilingual = multilingual_texts - italian_texts
    both = italian_texts & multilingual_texts

    print(f"\nOverlap Analysis:")
    print(f"  - Detected by BOTH models:    {len(both):3d} entities")
    print(f"  - Only by Italian model:      {len(only_italian):3d} entities")
    print(f"  - Only by multilingual model: {len(only_multilingual):3d} entities")

    if only_italian:
        print(f"\n  Italian model unique finds:")
        for text in list(only_italian)[:5]:
            print(f"    • {text[:60]}")

    if only_multilingual:
        print(f"\n  Multilingual model unique finds:")
        for text in list(only_multilingual)[:5]:
            print(f"    • {text[:60]}")

# Step 7: Threshold sensitivity test
if model_italian:
    print("\n" + "=" * 70)
    print("[Step 7] Threshold Sensitivity Test (Italian Model)")
    print("=" * 70)

    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]

    print(f"\n{'Threshold':<12} {'Entities':<10} {'Change':<10}")
    print("-" * 35)

    prev_count = 0
    for threshold in thresholds:
        entities = model_italian.predict_entities(
            TEST_TEXT,
            italian_labels,
            threshold=threshold
        )
        count = len(entities)
        change = count - prev_count if prev_count > 0 else 0
        change_str = f"{change:+d}" if prev_count > 0 else "baseline"

        print(f"{threshold:<12.1f} {count:<10d} {change_str:<10s}")
        prev_count = count

    print("\nRecommended thresholds:")
    print("  • Fast mode (Presidio only):  N/A")
    print("  • Balanced mode:              0.6 (high precision)")
    print("  • Thorough mode:              0.5 (balanced)")
    print("  • Maximum mode:               0.4 (high recall)")

# Final summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

print("\n✓ GLiNER dual-model setup is working!")

if model_italian:
    print("✓ Italian-specific model: READY")
else:
    print("✗ Italian-specific model: FAILED")

if model_multilingual:
    print("✓ Multilingual PII model: READY")
else:
    print("✗ Multilingual PII model: FAILED")

print("\nNext Steps:")
print("1. Integrate EnhancedPIIDetector into desktop app")
print("2. Connect detection depth slider to GLiNER thresholds")
print("3. Test on real Italian legal documents")
print("4. Measure accuracy improvement vs Presidio-only")

print("\n" + "=" * 70)

