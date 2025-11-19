"""
Test IntegratedPIIDetector with problematic entities
"""

import logging
import os

# Set environment variable for new detector
os.environ["USE_NEW_PII_DETECTOR"] = "true"

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

from pii_detector_integrated import IntegratedPIIDetector

print("="*60)
print("INTEGRATED DETECTOR TEST")
print("="*60)

# Initialize detector
detector = IntegratedPIIDetector(
    enable_gliner=False,  # Disable GLiNER for now (not installed)
    enable_prefilter=False,  # Disable prefilter for clarity
    enable_italian_context=True,  # Enable Italian context filtering
    enable_entity_thresholds=False  # Disable thresholds for clarity
)

# Test text with problematic entities
test_text = """
The Chief Technology Officer of the company presented the report.
The Intergovernativi organization was involved.
Firmato Da Giovanni Rossi, the document is complete.
Mario Rossi signed the contract.
"""

print(f"\nTest text contains:")
print("  1. Chief Technology Officer (should be filtered)")
print("  2. Intergovernativi (should be filtered)")
print("  3. Firmato Da (should be filtered)")
print("  4. Giovanni Rossi (should be detected)")
print("  5. Mario Rossi (should be detected)")

result = detector.detect_pii(test_text, depth="balanced")

print(f"\nDetected {len(result['entities'])} entities:")
for entity in result['entities']:
    print(f"  - '{entity['text']}' (type={entity['entity_type']}, score={entity['score']:.2f})")

print(f"\nItalian context filtered: {result['metadata']['italian_context_filtered']} entities")

# Check if problematic entities were filtered
problematic = ["Chief Technology Officer", "Intergovernativi", "Firmato Da"]
detected_texts = [e['text'] for e in result['entities']]

print("\n" + "="*60)
print("RESULTS:")
for term in problematic:
    if term in detected_texts:
        print(f"  [FAIL] '{term}' was NOT filtered")
    else:
        print(f"  [PASS] '{term}' was correctly filtered")

print("="*60)