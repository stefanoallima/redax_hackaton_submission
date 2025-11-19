# -*- coding: utf-8 -*-
"""
Simple GLiNER test script (Windows-compatible, no Unicode characters)
"""

print("=" * 70)
print("GLiNER Dual-Model Test")
print("=" * 70)

# Test text
TEST_TEXT = """
CONTRATTO DI LAVORO

TechItalia S.p.A., Partita IVA: 12345678901
Rappresentata da: Dott. Giovanni Bianchi

LAVORATORE:
Mario Rossi, nato a Roma il 15 marzo 1985
Residente in Via Mura Anteo Zamboni 22, 40126 Bologna (BO)
Codice Fiscale: RSSMRA85C15H501X

CONTATTI:
Telefono: +39 333 1234567
Email: mario.rossi@example.com
PEC: mario.rossi@pec.example.it

DATI BANCARI:
IBAN: IT60 X054 2811 1010 0000 0123 456
"""

print("\n[Step 1] Importing GLiNER...")
try:
    from gliner import GLiNER
    print("[OK] Import successful\n")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    exit(1)

print("[Step 2] Loading Italian model (DeepMount00/universal_ner_ita)...")
try:
    model_italian = GLiNER.from_pretrained("DeepMount00/universal_ner_ita")
    print("[OK] Model loaded\n")
except Exception as e:
    print(f"[FAIL] Model loading failed: {e}")
    model_italian = None

print("[Step 3] Loading multilingual PII model (urchade/gliner_multi_pii-v1)...")
try:
    model_multilingual = GLiNER.from_pretrained("urchade/gliner_multi_pii-v1")
    print("[OK] Model loaded\n")
except Exception as e:
    print(f"[FAIL] Model loading failed: {e}")
    model_multilingual = None

if model_italian is None and model_multilingual is None:
    print("[FAIL] Both models failed to load")
    exit(1)

# Test Italian model
if model_italian:
    print("=" * 70)
    print("[Step 4] Testing Italian Model")
    print("=" * 70)

    italian_labels = [
        "persona", "codice fiscale", "partita iva",
        "email", "telefono", "indirizzo", "iban", "data"
    ]

    try:
        entities_italian = model_italian.predict_entities(TEST_TEXT, italian_labels, threshold=0.5)
        print(f"\n[OK] Detected {len(entities_italian)} entities:\n")

        for i, entity in enumerate(entities_italian[:10], 1):  # Show first 10
            label = entity['label'][:15].ljust(15)
            text = entity['text'][:40].ljust(40)
            score = entity['score']
            print(f"  {i:2d}. [{label}] {text} ({score:.0%})")

        if len(entities_italian) > 10:
            print(f"  ... and {len(entities_italian) - 10} more")

    except Exception as e:
        print(f"[FAIL] Detection failed: {e}")

# Test multilingual model
if model_multilingual:
    print("\n" + "=" * 70)
    print("[Step 5] Testing Multilingual PII Model")
    print("=" * 70)

    multilingual_labels = [
        "person", "email", "phone number", "address",
        "fiscal code", "vat number", "iban", "date"
    ]

    try:
        entities_multilingual = model_multilingual.predict_entities(TEST_TEXT, multilingual_labels, threshold=0.5)
        print(f"\n[OK] Detected {len(entities_multilingual)} entities:\n")

        for i, entity in enumerate(entities_multilingual[:10], 1):  # Show first 10
            label = entity['label'][:15].ljust(15)
            text = entity['text'][:40].ljust(40)
            score = entity['score']
            print(f"  {i:2d}. [{label}] {text} ({score:.0%})")

        if len(entities_multilingual) > 10:
            print(f"  ... and {len(entities_multilingual) - 10} more")

    except Exception as e:
        print(f"[FAIL] Detection failed: {e}")

# Comparison
if model_italian and model_multilingual:
    print("\n" + "=" * 70)
    print("[Step 6] Model Comparison")
    print("=" * 70)

    italian_count = len(entities_italian)
    multi_count = len(entities_multilingual)

    print(f"\nItalian model:      {italian_count:3d} entities")
    print(f"Multilingual model: {multi_count:3d} entities")

    italian_texts = {e['text'] for e in entities_italian}
    multi_texts = {e['text'] for e in entities_multilingual}

    both = italian_texts & multi_texts
    only_italian = italian_texts - multi_texts
    only_multi = multi_texts - italian_texts

    print(f"\nOverlap:")
    print(f"  Both models:    {len(both):3d} entities")
    print(f"  Only Italian:   {len(only_italian):3d} entities")
    print(f"  Only Multi PII: {len(only_multi):3d} entities")

print("\n" + "=" * 70)
print("[SUCCESS] GLiNER dual-model test complete!")
print("=" * 70)

print("\nNext Steps:")
print("1. Integrate EnhancedPIIDetector into desktop app")
print("2. Connect detection depth slider to GLiNER thresholds")
print("3. Test on real Italian legal documents")
print("4. Measure accuracy improvement vs Presidio-only")
