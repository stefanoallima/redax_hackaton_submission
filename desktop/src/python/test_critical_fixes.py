"""
Test the 3 critical false positive fixes
"""

import os
os.environ["USE_NEW_PII_DETECTOR"] = "true"

from pii_detector_integrated import IntegratedPIIDetector

# Initialize detector
detector = IntegratedPIIDetector(
    enable_gliner=False,
    enable_prefilter=True,
    enable_italian_context=True,
    enable_entity_thresholds=True
)

# Test cases for the 3 critical false positives
test_cases = [
    ("B1-1", "Il Chief Technology Officer ha presentato la relazione tecnica."),
    ("B2-1", "Gli organismi Intergovernativi hanno approvato la risoluzione."),
    ("B3-1", "Firmato Da: [signature]"),
]

print("=" * 60)
print("CRITICAL FALSE POSITIVE FIXES TEST")
print("=" * 60)
print()

for test_id, text in test_cases:
    result = detector.detect_pii(text, depth="balanced")
    entities = result["entities"]

    print(f"Test {test_id}:")
    print(f"  Text: {text[:50]}...")
    print(f"  Detected entities: {len(entities)}")
    if entities:
        print(f"  Entities found: {[e['text'] for e in entities]}")
        print(f"  [FAIL] - Should NOT detect anything")
    else:
        print(f"  [PASS] - Correctly filtered (no detection)")
    print()

print("=" * 60)