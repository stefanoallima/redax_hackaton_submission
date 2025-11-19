# -*- coding: utf-8 -*-
"""
Real Document Test - Compare Presidio vs GLiNER-enhanced detection
Tests accuracy improvement on actual Italian CV
"""

import sys
from pathlib import Path

print("=" * 70)
print("Real Document Test - GLiNER vs Presidio Comparison")
print("=" * 70)

# Test document
TEST_PDF = "CV_Luca_Cervone_Ita.pdf"

if not Path(TEST_PDF).exists():
    print(f"\n[ERROR] Test file not found: {TEST_PDF}")
    print("Please ensure the file is in the current directory")
    exit(1)

print(f"\n[INFO] Testing document: {TEST_PDF}")
print(f"[INFO] File size: {Path(TEST_PDF).stat().st_size / 1024:.1f} KB\n")

# Import required modules
print("[Step 1] Importing modules...")
try:
    from document_processor import DocumentProcessor
    from pii_detector import PIIDetector
    from pii_detector_enhanced import EnhancedPIIDetector
    from detection_config import DetectionConfig
    print("[OK] All modules imported\n")
except Exception as e:
    print(f"[FAIL] Import error: {e}")
    exit(1)

# Extract text from PDF
print("[Step 2] Extracting text from PDF...")
try:
    doc_result = DocumentProcessor.process_document(TEST_PDF)
    if doc_result['status'] != 'success':
        print(f"[FAIL] Document processing failed: {doc_result.get('error')}")
        exit(1)

    full_text = doc_result['full_text']
    pages = doc_result.get('metadata', {}).get('pages', 1)

    print(f"[OK] Extracted {len(full_text)} characters from {pages} page(s)")
    print(f"[INFO] Preview: {full_text[:200]}...\n")
except Exception as e:
    print(f"[FAIL] Text extraction failed: {e}")
    exit(1)

# Test 1: Presidio-only (Fast mode)
print("=" * 70)
print("[Test 1] Presidio-only Detection (Fast mode)")
print("=" * 70)

try:
    detector_presidio = PIIDetector()
    config_fast = DetectionConfig(depth='fast')

    result_presidio = detector_presidio.process_document(doc_result, config=config_fast)

    if result_presidio['status'] == 'success':
        presidio_entities = result_presidio['entities']
        presidio_count = len(presidio_entities)
        presidio_summary = result_presidio.get('entity_summary', {})

        print(f"\n[OK] Presidio detected {presidio_count} entities:")
        for entity_type, count in sorted(presidio_summary.items(), key=lambda x: -x[1]):
            print(f"  - {entity_type}: {count}")

        print(f"\n[INFO] Sample entities:")
        for i, entity in enumerate(presidio_entities[:5], 1):
            text = entity['text'][:40]
            print(f"  {i}. [{entity['entity_type']:20s}] {text:40s} ({entity['score']:.0%})")

        if len(presidio_entities) > 5:
            print(f"  ... and {len(presidio_entities) - 5} more")

        print()
    else:
        print(f"[FAIL] Detection failed: {result_presidio.get('error')}")
        exit(1)

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 2: GLiNER-enhanced (Balanced mode - Italian model only)
print("=" * 70)
print("[Test 2] GLiNER-enhanced Detection (Balanced mode)")
print("=" * 70)

try:
    detector_enhanced = EnhancedPIIDetector(enable_gliner=True)
    config_balanced = DetectionConfig(depth='balanced')

    result_balanced = detector_enhanced.process_document(doc_result, config=config_balanced)

    if result_balanced['status'] == 'success':
        balanced_entities = result_balanced['entities']
        balanced_count = len(balanced_entities)
        balanced_summary = result_balanced.get('entity_summary', {})
        source_summary = result_balanced.get('source_summary', {})

        print(f"\n[OK] Enhanced detection found {balanced_count} entities:")
        for entity_type, count in sorted(balanced_summary.items(), key=lambda x: -x[1]):
            print(f"  - {entity_type}: {count}")

        print(f"\n[INFO] Detection sources:")
        for source, count in source_summary.items():
            print(f"  - {source}: {count} entities")

        print(f"\n[INFO] Sample entities:")
        for i, entity in enumerate(balanced_entities[:5], 1):
            text = entity['text'][:40]
            source = entity.get('source', 'unknown')
            print(f"  {i}. [{entity['entity_type']:20s}] {text:40s} ({entity['score']:.0%}) [{source}]")

        if len(balanced_entities) > 5:
            print(f"  ... and {len(balanced_entities) - 5} more")

        print()
    else:
        print(f"[FAIL] Detection failed: {result_balanced.get('error')}")
        exit(1)

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: GLiNER-enhanced (Thorough mode - Both models)
print("=" * 70)
print("[Test 3] GLiNER-enhanced Detection (Thorough mode)")
print("=" * 70)

try:
    config_thorough = DetectionConfig(depth='thorough')

    result_thorough = detector_enhanced.process_document(doc_result, config=config_thorough)

    if result_thorough['status'] == 'success':
        thorough_entities = result_thorough['entities']
        thorough_count = len(thorough_entities)
        thorough_summary = result_thorough.get('entity_summary', {})
        source_summary_thorough = result_thorough.get('source_summary', {})

        print(f"\n[OK] Thorough detection found {thorough_count} entities:")
        for entity_type, count in sorted(thorough_summary.items(), key=lambda x: -x[1]):
            print(f"  - {entity_type}: {count}")

        print(f"\n[INFO] Detection sources:")
        for source, count in source_summary_thorough.items():
            print(f"  - {source}: {count} entities")

        print(f"\n[INFO] Sample entities:")
        for i, entity in enumerate(thorough_entities[:5], 1):
            text = entity['text'][:40]
            source = entity.get('source', 'unknown')
            print(f"  {i}. [{entity['entity_type']:20s}] {text:40s} ({entity['score']:.0%}) [{source}]")

        if len(thorough_entities) > 5:
            print(f"  ... and {len(thorough_entities) - 5} more")

        print()
    else:
        print(f"[FAIL] Detection failed: {result_thorough.get('error')}")
        exit(1)

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Comparison
print("=" * 70)
print("[Comparison] Accuracy Improvement Analysis")
print("=" * 70)

improvement_balanced = ((balanced_count - presidio_count) / presidio_count * 100) if presidio_count > 0 else 0
improvement_thorough = ((thorough_count - presidio_count) / presidio_count * 100) if presidio_count > 0 else 0

print(f"\n[RESULTS]")
print(f"  Presidio-only (Fast):           {presidio_count:3d} entities (baseline)")
print(f"  + GLiNER Italian (Balanced):    {balanced_count:3d} entities (+{improvement_balanced:+.1f}%)")
print(f"  + Both GLiNER models (Thorough): {thorough_count:3d} entities (+{improvement_thorough:+.1f}%)")

# Find new entities detected by GLiNER
presidio_texts = {e['text'] for e in presidio_entities}
balanced_texts = {e['text'] for e in balanced_entities}
thorough_texts = {e['text'] for e in thorough_entities}

new_in_balanced = balanced_texts - presidio_texts
new_in_thorough = thorough_texts - balanced_texts

print(f"\n[NEW ENTITIES]")
if new_in_balanced:
    print(f"  Balanced mode found {len(new_in_balanced)} new entities:")
    for text in list(new_in_balanced)[:5]:
        entity = next((e for e in balanced_entities if e['text'] == text), None)
        if entity:
            print(f"    - {entity['entity_type']:20s}: {text[:40]}")
    if len(new_in_balanced) > 5:
        print(f"    ... and {len(new_in_balanced) - 5} more")

if new_in_thorough:
    print(f"\n  Thorough mode found {len(new_in_thorough)} additional entities:")
    for text in list(new_in_thorough)[:5]:
        entity = next((e for e in thorough_entities if e['text'] == text), None)
        if entity:
            print(f"    - {entity['entity_type']:20s}: {text[:40]}")
    if len(new_in_thorough) > 5:
        print(f"    ... and {len(new_in_thorough) - 5} more")

print("\n" + "=" * 70)
print("[SUCCESS] Real document test complete!")
print("=" * 70)

print("\n[SUMMARY]")
print(f"  Document: {TEST_PDF}")
print(f"  Pages: {pages}")
print(f"  Characters: {len(full_text)}")
print(f"  Detection improvement: +{improvement_thorough:.1f}% (Presidio → GLiNER)")
print(f"  Models used: {', '.join(source_summary_thorough.keys())}")
print("\n  Recommendation: Use 'Thorough' mode for maximum coverage!")
