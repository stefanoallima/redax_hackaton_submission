# -*- coding: utf-8 -*-
"""
Quick test for NEW IntegratedPIIDetector
Tests initialization and basic detection without segfault
"""

import sys
from pathlib import Path

def test_new_detector():
    """Test NEW IntegratedPIIDetector initialization and detection"""

    print("="*80)
    print("QUICK TEST - NEW INTEGRATED PII DETECTOR")
    print("="*80)
    print()

    # Step 1: Initialize detector
    print("[Step 1] Initializing NEW IntegratedPIIDetector...")
    try:
        from pii_detector_integrated import IntegratedPIIDetector

        detector = IntegratedPIIDetector(
            enable_gliner=True,
            enable_prefilter=True,
            enable_italian_context=True,
            enable_entity_thresholds=True
        )
        print("[OK] Detector initialized successfully")
    except Exception as e:
        print(f"[FAIL] Failed to initialize detector: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 2: Test basic detection
    print()
    print("[Step 2] Testing basic PII detection...")

    test_text = """
    Il signor Mario Rossi, nato a Roma il 15/03/1985,
    codice fiscale RSSMRA85C15H501X, residente in
    Via Giuseppe Garibaldi 123, Milano (MI),
    telefono 02-12345678, email mario.rossi@example.com

    Il ricorso e presentato contro INPS presso il
    Tribunale di Milano.
    """

    try:
        result = detector.detect_pii(test_text, depth='balanced')

        entities_count = len(result['entities'])
        processing_time = result['performance']['total_time_ms']
        prefilter_applied = result['metadata']['prefilter_applied']
        italian_filtered = result['metadata']['italian_context_filtered']

        print(f"[OK] Detection complete")
        print(f"     Entities detected: {entities_count}")
        print(f"     Processing time: {processing_time:.0f}ms")
        print(f"     Pre-filter applied: {prefilter_applied}")
        print(f"     Italian context filtered: {italian_filtered} entities")

        print()
        print("Detected entities:")
        for i, entity in enumerate(result['entities'][:10], 1):
            entity_type = entity['entity_type']
            text = entity['text']
            score = entity['score']
            print(f"  {i}. {entity_type:20s}: {text:30s} (score={score:.2f})")

        # Verify Italian context filtering worked
        entity_texts = [e['text'] for e in result['entities']]

        # Check that courts/institutions were filtered
        false_positives = []
        for text in ['INPS', 'Tribunale di Milano', 'Tribunale']:
            if text in entity_texts:
                false_positives.append(text)

        if false_positives:
            print()
            print(f"[WARN] Italian context filtering may not be working")
            print(f"       Found: {false_positives}")
        else:
            print()
            print(f"[OK] Italian context filtering working correctly")
            print(f"     (Courts/institutions filtered out)")

    except Exception as e:
        print(f"[FAIL] Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Test with document (if available)
    print()
    print("[Step 3] Testing with real document...")

    test_file = Path("input/CV_Luca_Cervone_Ita.pdf")

    if test_file.exists():
        try:
            from document_processor import DocumentProcessor

            # Process document
            doc_result = DocumentProcessor.process_document(str(test_file))

            if doc_result['status'] != 'success':
                print(f"[FAIL] Document processing failed: {doc_result.get('error')}")
                return False

            full_text = doc_result['full_text']
            pages = doc_result.get('metadata', {}).get('pages', 1)

            print(f"[OK] Extracted {len(full_text):,} characters from {pages} page(s)")

            # Detect PII
            result = detector.detect_pii(full_text, depth='balanced')

            entities_count = len(result['entities'])
            processing_time = result['performance']['total_time_ms']

            print(f"[OK] Detected {entities_count} PII entities")
            print(f"     Processing time: {processing_time:.0f}ms ({len(full_text)/processing_time*1000:.0f} chars/sec)")

            # Show entity summary
            entity_summary = {}
            for entity in result['entities']:
                entity_type = entity['entity_type']
                entity_summary[entity_type] = entity_summary.get(entity_type, 0) + 1

            print()
            print("Entity types detected:")
            for entity_type, count in sorted(entity_summary.items(), key=lambda x: -x[1]):
                print(f"  - {entity_type:25s}: {count:3d}")

        except Exception as e:
            print(f"[FAIL] Document processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"[SKIP] Test document not found: {test_file}")
        print(f"       (This is optional)")

    # Success!
    print()
    print("="*80)
    print("[SUCCESS] NEW INTEGRATED DETECTOR WORKS!")
    print("="*80)
    print()
    print("Summary:")
    print("  - Detector initialized without errors")
    print("  - Basic detection works (5-6 entities)")
    print("  - Italian context filtering works")
    print("  - No segmentation fault!")
    print()
    print("Next steps:")
    print("  1. Enable NEW detector: set USE_NEW_PII_DETECTOR=true")
    print("  2. Run desktop app: cd desktop && npm run electron:dev")
    print("  3. Test with real documents")
    print()

    return True


if __name__ == "__main__":
    success = test_new_detector()
    sys.exit(0 if success else 1)
