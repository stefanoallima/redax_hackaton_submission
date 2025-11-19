"""
Improved Performance Benchmark - Old vs New PII Detector
Tests actual runtime performance (excludes initialization overhead)
"""

import time
import logging
import sys
import os
import statistics

# Suppress all logging except critical
logging.basicConfig(level=logging.CRITICAL)
for logger_name in ['presidio-analyzer', 'pii_detector', 'pii_detector_enhanced',
                    'pii_detector_integrated', 'pii_detector_presidio_v2',
                    'italian_context_patterns', 'italian_legal_context',
                    'text_prefilter', 'entity_thresholds', 'spacy_optimizer']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Test documents
TEST_TEXTS = [
    """Il signor Mario Rossi, nato a Roma il 15/03/1985,
    codice fiscale RSSMRA85C15H501X, residente in
    Via Giuseppe Garibaldi 123, Milano (MI).
    Email: mario.rossi@example.com, telefono 02-12345678.""",

    """La dottoressa Anna Verdi ha presentato ricorso
    presso il Tribunale di Milano contro INPS.
    Contatto: anna.verdi@pec.it, cell. 333-1234567.""",

    """Giovanni Bianchi, CF BNCGNN80A01H501X,
    domiciliato in Corso Italia 45, Torino.
    Il Chief Technology Officer ha approvato la proposta.""",

    """Firmato Da: il rappresentante legale
    Marco Dell'Utri, nato il 01/01/1970.
    Intergovernativi hanno discusso il caso.""",

    """MARIO ROSSI ha sottoscritto il contratto.
    Email: MARIO.ROSSI@EXAMPLE.COM
    Partita IVA: 12345678901"""
]

def benchmark_detector(detector_class, detector_name, **init_kwargs):
    """Benchmark a detector with proper warm-up and multiple runs"""
    print(f"\n[{detector_name}] Initializing...")

    # Initialize detector (not timed)
    try:
        if detector_name == "OLD":
            from pii_detector_enhanced import EnhancedPIIDetector
            detector = EnhancedPIIDetector()
        else:
            from pii_detector_integrated import IntegratedPIIDetector
            detector = IntegratedPIIDetector(**init_kwargs)
    except ImportError as e:
        return {"status": "import_error", "error": str(e)}
    except Exception as e:
        return {"status": "init_error", "error": str(e)}

    print(f"[{detector_name}] Warming up (first run to cache models)...")

    # Warm-up run (not timed) - ensures models are loaded and cached
    try:
        if detector_name == "OLD":
            _ = detector.detect_pii(TEST_TEXTS[0], depth="balanced")
        else:
            _ = detector.detect_pii(TEST_TEXTS[0], depth="balanced")
    except Exception as e:
        return {"status": "warmup_error", "error": str(e)}

    print(f"[{detector_name}] Running performance tests...")

    # Run multiple tests
    times = []
    entity_counts = []

    for i, text in enumerate(TEST_TEXTS):
        try:
            start = time.time()

            if detector_name == "OLD":
                entities = detector.detect_pii(text, depth="balanced")
                entity_count = len(entities) if isinstance(entities, list) else 0
            else:
                result = detector.detect_pii(text, depth="balanced")
                entities = result["entities"]
                entity_count = len(entities)

            elapsed = time.time() - start
            times.append(elapsed * 1000)  # Convert to ms
            entity_counts.append(entity_count)

            print(f"  Test {i+1}: {elapsed*1000:.2f}ms, {entity_count} entities")

        except Exception as e:
            print(f"  Test {i+1}: ERROR - {e}")

    if not times:
        return {"status": "test_error", "error": "No successful tests"}

    return {
        "status": "success",
        "avg_time_ms": statistics.mean(times),
        "median_time_ms": statistics.median(times),
        "min_time_ms": min(times),
        "max_time_ms": max(times),
        "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "total_entities": sum(entity_counts),
        "avg_entities": statistics.mean(entity_counts),
        "num_tests": len(times)
    }

def main():
    """Run improved benchmark comparison"""
    print("="*70)
    print("IMPROVED PERFORMANCE BENCHMARK - RUNTIME COMPARISON")
    print("="*70)
    print("\nThis test excludes initialization/model loading time")
    print(f"Testing with {len(TEST_TEXTS)} different documents")

    # Test OLD detector
    print("\n" + "="*70)
    print("Testing OLD Detector (EnhancedPIIDetector)")
    print("="*70)
    old_result = benchmark_detector(None, "OLD")

    # Test NEW detector
    print("\n" + "="*70)
    print("Testing NEW Detector (IntegratedPIIDetector)")
    print("="*70)
    new_result = benchmark_detector(
        None, "NEW",
        enable_gliner=False,  # GLiNER not installed
        enable_prefilter=True,
        enable_italian_context=True,
        enable_entity_thresholds=True
    )

    # Show results
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON RESULTS")
    print("="*70)

    if old_result["status"] == "success" and new_result["status"] == "success":
        print("\n[OLD Detector - EnhancedPIIDetector]")
        print(f"  Average time: {old_result['avg_time_ms']:.2f}ms")
        print(f"  Median time:  {old_result['median_time_ms']:.2f}ms")
        print(f"  Min/Max:      {old_result['min_time_ms']:.2f}ms / {old_result['max_time_ms']:.2f}ms")
        print(f"  Std Dev:      {old_result['std_dev_ms']:.2f}ms")
        print(f"  Avg entities: {old_result['avg_entities']:.1f}")

        print("\n[NEW Detector - IntegratedPIIDetector]")
        print(f"  Average time: {new_result['avg_time_ms']:.2f}ms")
        print(f"  Median time:  {new_result['median_time_ms']:.2f}ms")
        print(f"  Min/Max:      {new_result['min_time_ms']:.2f}ms / {new_result['max_time_ms']:.2f}ms")
        print(f"  Std Dev:      {new_result['std_dev_ms']:.2f}ms")
        print(f"  Avg entities: {new_result['avg_entities']:.1f}")

        # Calculate speedup
        speedup = old_result['avg_time_ms'] / new_result['avg_time_ms']
        time_saved = old_result['avg_time_ms'] - new_result['avg_time_ms']
        entity_diff = new_result['avg_entities'] - old_result['avg_entities']

        print("\n" + "-"*70)
        print("ANALYSIS")
        print("-"*70)
        print(f"Performance:")
        print(f"  Speedup:      {speedup:.2f}x")
        print(f"  Time saved:   {time_saved:.2f}ms per detection")

        if speedup >= 2.0:
            print(f"  Result:       [PASS] Target of 2x speedup achieved!")
        elif speedup >= 1.5:
            print(f"  Result:       [PARTIAL] 1.5x speedup achieved")
        elif speedup >= 1.0:
            print(f"  Result:       [OK] Similar performance")
        else:
            print(f"  Result:       [FAIL] NEW detector is slower")

        print(f"\nAccuracy:")
        print(f"  Entity difference: {entity_diff:+.1f} entities per document")
        if entity_diff < 0:
            print(f"  Note: Fewer entities is GOOD (less false positives)")

        # Final verdict
        print("\n" + "="*70)
        print("VERDICT")
        print("="*70)

        if speedup > 1:
            print(f"NEW detector is {speedup:.1f}x FASTER than OLD detector")
        elif speedup == 1:
            print("Both detectors have similar performance")
        else:
            print(f"NEW detector is {1/speedup:.1f}x SLOWER than OLD detector")

        if new_result['avg_entities'] < old_result['avg_entities']:
            print(f"NEW detector has {abs(entity_diff):.1f} fewer false positives per document")
    else:
        print("\nERROR: Could not complete benchmark")
        if old_result["status"] != "success":
            print(f"  OLD detector: {old_result['status']} - {old_result.get('error', '')}")
        if new_result["status"] != "success":
            print(f"  NEW detector: {new_result['status']} - {new_result.get('error', '')}")

if __name__ == "__main__":
    main()