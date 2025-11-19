"""
Quick GLiNER test for Italian PII detection
Run this after installing Visual C++ Redistributable
"""

# Disable symlinks for Windows compatibility
import os
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'

print("=" * 80)
print("GLiNER Quick Test - Italian PII Detection")
print("=" * 80)

# Test 1: Import
print("\n[Test 1] Importing GLiNER...")
try:
    from gliner import GLiNER
    print("[OK] GLiNER import successful")
except Exception as e:
    print(f"[ERROR] GLiNER import failed: {e}")
    print("\nSolution:")
    print("1. Install Visual C++ Redistributable:")
    print("   https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print("2. Restart your computer")
    print("3. Run this test again")
    exit(1)

# Test 2: Model loading
print("\n[Test 2] Loading GLiNER PII model...")
print("(This may take 1-2 minutes on first run - downloading ~250MB)")
try:
    model = GLiNER.from_pretrained("urchade/gliner_multi_pii-v1")
    print("[OK] Model loaded successfully")
except Exception as e:
    print(f"[ERROR] Model loading failed: {e}")
    exit(1)

# Test 3: Italian PII detection
print("\n[Test 3] Detecting PII in Italian legal text...")

test_text = """
CONTRATTO DI LAVORO SUBORDINATO

Tra:
- DATORE DI LAVORO: TechItalia S.p.A., P.IVA 12345678901,
  Sede: Via Milano 45, 20100 Milano (MI)
  Rappresentante: Dott. Giovanni Bianchi

- LAVORATORE: Mario Rossi
  Nato il: 15/08/1990 a Roma (RM)
  Codice Fiscale: RSSMRA90M55H501A
  Residenza: Via Roma 123, 00100 Roma (RM)
  Telefono: +39 333 1234567
  Email: mario.rossi@email.com

COORDINATE BANCARIE:
IBAN: IT60 X054 2811 1010 0000 0123 456
Intestato a: Mario Rossi
Banca: UniCredit S.p.A.
"""

# Italian PII labels
labels = [
    "person",
    "email",
    "phone number",
    "address",
    "codice fiscale",
    "fiscal code",
    "iban",
    "bank account",
    "partita iva",
    "vat number",
    "date",
    "organization",
    "location"
]

try:
    entities = model.predict_entities(test_text, labels, threshold=0.5)
    print(f"[OK] Detected {len(entities)} PII entities\n")

    # Print results
    print("=" * 80)
    print("DETECTED PII ENTITIES")
    print("=" * 80)

    # Group by entity type
    from collections import defaultdict
    grouped = defaultdict(list)
    for entity in entities:
        grouped[entity['label']].append(entity)

    for label in sorted(grouped.keys()):
        print(f"\n{label.upper()}:")
        for entity in grouped[label]:
            print(f"  - '{entity['text']}' (confidence: {entity['score']:.2%})")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for label in sorted(grouped.keys()):
        print(f"  {label}: {len(grouped[label])} found")

    print(f"\nTotal: {len(entities)} PII entities detected")

    # Validate key entities were found
    print("\n" + "=" * 80)
    print("VALIDATION")
    print("=" * 80)

    expected_pii = {
        "codice fiscale": "RSSMRA90M55H501A",
        "person": "Mario Rossi",
        "email": "mario.rossi@email.com",
        "iban": "IT60 X054 2811 1010 0000 0123 456"
    }

    all_found = True
    for pii_type, expected_value in expected_pii.items():
        found = any(
            expected_value.lower() in entity['text'].lower()
            for entity in entities
            if entity['label'].lower() == pii_type.lower()
        )
        status = "[OK]" if found else "[MISS]"
        print(f"{status} {pii_type}: {expected_value}")
        if not found:
            all_found = False

    print("\n" + "=" * 80)
    if all_found:
        print("[SUCCESS] All key PII entities were detected!")
        print("GLiNER is working correctly for Italian legal text.")
    else:
        print("[WARNING] Some expected entities were not detected.")
        print("This may indicate threshold tuning needed.")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Review the detection results above")
    print("2. Test with your own Italian legal documents")
    print("3. Run full test suite: python test_gliner.py")
    print("4. See GLINER_INTEGRATION_PLAN.md for integration steps")
    print("=" * 80 + "\n")

except Exception as e:
    print(f"[ERROR] Detection failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
