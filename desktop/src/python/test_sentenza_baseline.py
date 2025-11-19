"""
Baseline E2E Test - Minimal Processing Configuration
Tests raw GLiNER performance without preprocessing layers

This test disables:
- Text prefiltering
- Italian legal context filtering
- Entity threshold adjustments

This allows us to see pure GLiNER detection performance and identify
which preprocessing layers may be causing false negatives.
"""

import os
import sys
from test_sentenza_e2e import *  # Import all existing functions
import logging

logger = logging.getLogger(__name__)


def detect_pii_baseline(text: str, depth: str = "balanced") -> Dict:
    """
    Run PII detection with MINIMAL processing layers.

    Configuration:
    - ✓ GLiNER models enabled (core functionality)
    - ✓ Basic normalization enabled
    - ✗ Prefiltering DISABLED
    - ✗ Italian legal context filtering DISABLED
    - ✗ Entity threshold adjustments DISABLED

    Args:
        text: Input text to analyze
        depth: Detection depth level

    Returns:
        Detection result dictionary
    """
    try:
        os.environ["USE_NEW_PII_DETECTOR"] = "true"
        from pii_detector_integrated import IntegratedPIIDetector

        logger.info("=" * 70)
        logger.info("BASELINE CONFIGURATION:")
        logger.info("  ✓ GLiNER models enabled")
        logger.info("  ✗ Prefiltering DISABLED")
        logger.info("  ✗ Italian context filtering DISABLED")
        logger.info("  ✗ Entity thresholds DISABLED")
        logger.info("=" * 70)

        detector = IntegratedPIIDetector(
            enable_gliner=True,           # Core GLiNER functionality
            enable_prefilter=False,       # ← DISABLED for baseline
            enable_italian_context=False, # ← DISABLED for baseline
            enable_entity_thresholds=False # ← DISABLED for baseline
        )

        result = detector.detect_pii(text, depth=depth)
        return result

    except Exception as e:
        logger.error(f"Error detecting PII: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"entities": [], "metadata": {}}


def main_baseline():
    """Run baseline test"""
    print("\n" + "="*80)
    print("BASELINE E2E TEST - Minimal Processing Configuration")
    print("="*80)
    print("\nPurpose: Establish baseline GLiNER performance without preprocessing")
    print("This helps identify which filters may be causing false negatives.\n")

    # Step 1: Load expected PII
    print("[Step 1] Loading expected PII from ground truth...")
    expected_pii = load_expected_pii()
    total_expected = sum(len(items) for items in expected_pii.values())
    print(f"  Loaded {total_expected} expected PII entities:")
    for category, items in expected_pii.items():
        if items:
            print(f"    - {category}: {len(items)}")

    # Step 2: Extract text from PDF (using pdfplumber)
    print("\n[Step 2] Extracting text from PDF (pdfplumber)...")
    INPUT_PDF = "input/sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex.pdf"

    if not os.path.exists(INPUT_PDF):
        print(f"  ERROR: PDF file not found: {INPUT_PDF}")
        return

    text = extract_text_from_pdf(INPUT_PDF)
    print(f"  Extracted {len(text)} characters from PDF")

    # Check for email symbols
    email_count = text.count('@')
    print(f"  Email symbols (@) found in text: {email_count}")

    # Step 3: Run BASELINE detection
    print("\n[Step 3] Running BASELINE PII detection...")
    print("  (No preprocessing filters - raw GLiNER only)")
    detection_result = detect_pii_baseline(text, depth="balanced")

    detected_entities = detection_result.get('entities', [])
    print(f"  Detected {len(detected_entities)} PII entities")

    # Step 4: Compare results
    print("\n[Step 4] Comparing detected vs expected PII...")

    # Debug: Show sample detections
    print(f"\nDEBUG - Sample detected entities:")
    for i, entity in enumerate(detected_entities[:10]):  # Show first 10
        entity_text = entity.get('text', entity.get('entity', ''))
        print(f"  {i+1}. {entity.get('entity_type')}: '{entity_text}' (score: {entity.get('score', 0):.2f})")

    results = compare_detections(detected_entities, expected_pii)

    # Step 5: Print results
    print_results(results)

    # Step 6: Save results
    output_file = "output/test_results/sentenza_baseline_results.txt"
    save_results_to_file(results, output_file)
    print(f"\nBaseline results saved to: {output_file}")

    # Step 7: Summary
    total_tp = sum(len(r['true_positives']) for r in results.values())
    total_detected = sum(r['detected_count'] for r in results.values())
    overall_precision = total_tp / total_detected if total_detected > 0 else 0
    overall_recall = total_tp / total_expected if total_expected > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

    print("\n" + "="*80)
    print("BASELINE SUMMARY")
    print("="*80)
    print(f"F1 Score (Baseline): {overall_f1:.2%}")
    print(f"This represents raw GLiNER performance without any preprocessing filters.")
    print(f"Compare this to the full pipeline to see impact of each optimization layer.")
    print("="*80)


if __name__ == "__main__":
    main_baseline()
