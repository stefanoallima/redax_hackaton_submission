"""
Email Detection Diagnostic Script
Tests whether Presidio's EMAIL_ADDRESS recognizer is working correctly
"""

import logging
import sys
import os
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_email_detection_presidio_only():
    """Test email detection with Presidio only (no GLiNER)"""
    print("\n" + "="*80)
    print("TEST 1: Presidio-Only Email Detection (GLiNER disabled)")
    print("="*80)

    try:
        from pii_detector_presidio_v2 import EnhancedPIIDetectorV2

        detector = EnhancedPIIDetectorV2(enable_gliner=False)

        test_cases = [
            "Email: danielagambardella@ordineavvocatiroma.org",
            "Contact: avv.gabrielecatarinacci@pec.it",
            "Simple test: test@example.com",
            "My email is john.doe@gmail.com please contact me",
        ]

        for i, text in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {text}")
            entities = detector.detect_pii(text, depth="balanced")

            if entities:
                print(f"  ✅ Detected {len(entities)} entities:")
                for e in entities:
                    print(f"    - {e['entity_type']}: '{e['text']}' (score: {e['score']:.2f}, source: {e['source']})")
            else:
                print(f"  ❌ No entities detected")

        return True

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_detection_integrated():
    """Test email detection with IntegratedPIIDetector"""
    print("\n" + "="*80)
    print("TEST 2: Integrated Detector Email Detection (with filtering)")
    print("="*80)

    try:
        os.environ["USE_NEW_PII_DETECTOR"] = "true"
        from pii_detector_integrated import IntegratedPIIDetector

        detector = IntegratedPIIDetector(
            enable_gliner=False,  # Test without GLiNER first
            enable_prefilter=True,
            enable_italian_context=True,
            enable_entity_thresholds=True
        )

        test_cases = [
            "Email: danielagambardella@ordineavvocatiroma.org",
            "Contact: avv.gabrielecatarinacci@pec.it",
        ]

        for i, text in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {text}")
            result = detector.detect_pii(text, depth="balanced")
            entities = result.get('entities', [])
            metadata = result.get('metadata', {})

            print(f"  Metadata:")
            print(f"    - Prefilter applied: {metadata.get('prefilter_applied')}")
            print(f"    - Italian context filtered: {metadata.get('italian_context_filtered')}")

            if entities:
                print(f"  ✅ Detected {len(entities)} entities (after filtering):")
                for e in entities:
                    print(f"    - {e['entity_type']}: '{e['text']}' (score: {e['score']:.2f})")
            else:
                print(f"  ❌ No entities detected (may have been filtered out)")

        return True

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_recognizer_registry():
    """Test which recognizers are actually loaded"""
    print("\n" + "="*80)
    print("TEST 3: Recognizer Registry Inspection")
    print("="*80)

    try:
        from pii_detector_presidio_v2 import EnhancedPIIDetectorV2

        detector = EnhancedPIIDetectorV2(enable_gliner=False)
        analyzer = detector._get_analyzer(depth="balanced")

        print(f"\nLoaded Recognizers:")
        for recognizer in analyzer.registry.recognizers:
            supported_entities = recognizer.supported_entities if hasattr(recognizer, 'supported_entities') else []
            supported_languages = recognizer.supported_language if hasattr(recognizer, 'supported_language') else []
            print(f"  - {recognizer.name}: {supported_entities} (lang: {supported_languages})")

        # Check if EMAIL_ADDRESS recognizer is present
        email_recognizers = [r for r in analyzer.registry.recognizers if 'EMAIL' in str(r.supported_entities)]
        if email_recognizers:
            print(f"\n✅ EMAIL_ADDRESS recognizer IS loaded:")
            for r in email_recognizers:
                print(f"    - {r.name}: {r.supported_entities}")
        else:
            print(f"\n❌ EMAIL_ADDRESS recognizer NOT found in registry")

        return True

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostic tests"""
    print("\n" + "="*80)
    print("EMAIL DETECTION DIAGNOSTIC SUITE")
    print("Purpose: Identify why email detection is failing (0/2 emails detected)")
    print("="*80)

    results = []

    # Test 1: Presidio-only
    results.append(("Presidio-Only Test", test_email_detection_presidio_only()))

    # Test 2: Integrated detector
    results.append(("Integrated Detector Test", test_email_detection_integrated()))

    # Test 3: Registry inspection
    results.append(("Registry Inspection", test_recognizer_registry()))

    # Summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. If TEST 1 fails: Presidio recognizers not loading correctly")
    print("2. If TEST 1 passes but TEST 2 fails: Filtering is too aggressive")
    print("3. If TEST 3 shows no EMAIL recognizer: Configuration issue")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
