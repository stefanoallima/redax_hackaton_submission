"""
Simple Performance Benchmark - Old vs New PII Detector
Tests performance without excessive logging
"""

import time
import logging
import sys
import os

# Suppress all logging except critical
logging.basicConfig(level=logging.CRITICAL)
for logger_name in ['presidio-analyzer', 'pii_detector', 'pii_detector_enhanced',
                    'pii_detector_integrated', 'pii_detector_presidio_v2',
                    'italian_context_patterns']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Suppress stderr output temporarily
sys.stderr = open(os.devnull, 'w')

# Simple test document
TEST_TEXT = """
Il signor Mario Rossi, nato a Roma il 15/03/1985,
codice fiscale RSSMRA85C15H501X, residente in
Via Giuseppe Garibaldi 123, Milano (MI).
Email: mario.rossi@example.com, telefono 02-12345678.
Il Tribunale di Milano ha accolto il ricorso.
INPS ha confermato la prestazione previdenziale.
""" * 10  # Repeat 10x for more realistic performance

def test_old_detector():
    """Test old enhanced detector"""
    try:
        from pii_detector_enhanced import EnhancedPIIDetector
        detector = EnhancedPIIDetector()

        start = time.time()
        entities = detector.detect_pii(TEST_TEXT, depth="balanced")
        elapsed = time.time() - start

        return {
            "status": "success",
            "time_ms": round(elapsed * 1000, 2),
            "entities": len(entities) if isinstance(entities, list) else 0
        }
    except ImportError:
        return {"status": "not_available", "error": "Old detector not found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def test_new_detector():
    """Test new integrated detector"""
    try:
        from pii_detector_integrated import IntegratedPIIDetector
        detector = IntegratedPIIDetector(
            enable_gliner=False,  # Disabled since GLiNER not installed
            enable_prefilter=True,
            enable_italian_context=True,
            enable_entity_thresholds=True
        )

        start = time.time()
        result = detector.detect_pii(TEST_TEXT, depth="balanced")
        elapsed = time.time() - start

        return {
            "status": "success",
            "time_ms": round(elapsed * 1000, 2),
            "entities": len(result["entities"])
        }
    except ImportError:
        return {"status": "not_available", "error": "New detector not found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def main():
    """Run comparison"""
    # Restore stderr for output
    sys.stderr = sys.__stderr__

    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK - OLD vs NEW DETECTOR")
    print("="*60)
    print(f"\nTest document size: {len(TEST_TEXT)} characters")

    # Test OLD
    print("\n[1/2] Testing OLD detector...")
    old_result = test_old_detector()
    if old_result["status"] == "success":
        print(f"  Time: {old_result['time_ms']:.2f}ms")
        print(f"  Entities: {old_result['entities']}")
    else:
        print(f"  Status: {old_result['status']}")
        if "error" in old_result:
            print(f"  Error: {old_result['error']}")

    # Test NEW
    print("\n[2/2] Testing NEW detector...")
    new_result = test_new_detector()
    if new_result["status"] == "success":
        print(f"  Time: {new_result['time_ms']:.2f}ms")
        print(f"  Entities: {new_result['entities']}")
    else:
        print(f"  Status: {new_result['status']}")
        if "error" in new_result:
            print(f"  Error: {new_result['error']}")

    # Comparison
    print("\n" + "-"*60)
    print("COMPARISON RESULTS")
    print("-"*60)

    if old_result["status"] == "success" and new_result["status"] == "success":
        speedup = old_result["time_ms"] / new_result["time_ms"]
        time_saved = old_result["time_ms"] - new_result["time_ms"]
        entity_diff = new_result["entities"] - old_result["entities"]

        print(f"\nPerformance:")
        print(f"  Old detector: {old_result['time_ms']:.2f}ms")
        print(f"  New detector: {new_result['time_ms']:.2f}ms")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Time saved: {time_saved:.2f}ms")

        if speedup >= 2.0:
            print(f"  Result: [PASS] Target of 2x speedup achieved!")
        elif speedup >= 1.5:
            print(f"  Result: [PARTIAL] 1.5x speedup achieved")
        else:
            print(f"  Result: [FAIL] Speedup below 1.5x target")

        print(f"\nEntity Detection:")
        print(f"  Old: {old_result['entities']} entities")
        print(f"  New: {new_result['entities']} entities")
        print(f"  Difference: {entity_diff:+d}")

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"The new detector is {speedup:.1f}x {'faster' if speedup > 1 else 'slower'} than the old detector")

        if speedup < 1:
            print("\nNOTE: The new detector is SLOWER than expected.")
            print("This may be due to:")
            print("  1. GLiNER not being installed (falling back to Presidio only)")
            print("  2. First-time model loading overhead")
            print("  3. Additional filtering and validation steps")
    else:
        print("\nCannot compare - one or both detectors failed")

    print("\nTest complete.")

if __name__ == "__main__":
    main()