"""
Verification Test - Confirm Entity Thresholds Fix

This test verifies that disabling entity_thresholds resolves the performance degradation.

Configuration:
- GLiNER: ENABLED (both Italian + Multilingual models)
- Prefilter: ENABLED (no harm, may help with other documents)
- Italian Context: ENABLED (no harm, may help with other documents)
- Entity Thresholds: DISABLED (root cause of 42% F1 degradation)

Expected Result: F1 score should return to 7.84% baseline
"""

import os
import sys
import csv
import logging
from typing import List, Dict
from pathlib import Path
import pdfplumber

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logs
logging.getLogger('presidio-analyzer').setLevel(logging.WARNING)
logging.getLogger('pii_detector').setLevel(logging.WARNING)
logging.getLogger('pii_detector_integrated').setLevel(logging.WARNING)

# Paths
INPUT_PDF = "input/sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex.pdf"
EXPECTED_PII_CSV = "../../../docs/sentenza_document_all_pii.txt"
OUTPUT_FOLDER = "output/test_results"


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    return text.lower().strip()


def load_expected_pii() -> Dict[str, List[Dict]]:
    """Load expected PII from CSV file"""
    expected = {
        'person': [],
        'email': [],
        'address': [],
        'organization': []
    }

    csv_path = Path(EXPECTED_PII_CSV)
    if not csv_path.exists():
        logger.error(f"Expected PII file not found: {csv_path}")
        return expected

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pii_text = row['String_pii'].strip()
            category = row['category'].strip().lower()

            if category in expected:
                expected[category].append({
                    'text': pii_text,
                    'normalized': normalize_text(pii_text)
                })

    return expected


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber"""
    try:
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = "\n\n".join(text_parts)
        logger.info(f"Extracted {len(full_text)} chars from {len(text_parts)} pages")
        return full_text

    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""


def detect_pii_optimized(text: str, depth: str = "balanced") -> Dict:
    """
    Run PII detection with OPTIMIZED configuration (entity_thresholds DISABLED)

    This configuration keeps all filters except entity_thresholds which was
    identified as the root cause of 42% F1 degradation.
    """
    try:
        os.environ["USE_NEW_PII_DETECTOR"] = "true"
        from pii_detector_integrated import IntegratedPIIDetector

        detector = IntegratedPIIDetector(
            enable_gliner=True,           # Core GLiNER functionality
            use_multi_model=True,         # Both Italian + Multilingual models
            enable_prefilter=True,        # Keep enabled (no harm)
            enable_italian_context=True,  # Keep enabled (no harm)
            enable_entity_thresholds=False # DISABLED - root cause of degradation
        )

        result = detector.detect_pii(text, depth=depth)
        return result

    except Exception as e:
        logger.error(f"Error detecting PII: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"entities": [], "metadata": {}}


def map_entity_type(presidio_type: str) -> str:
    """Map Presidio entity types to our categories"""
    mapping = {
        'PERSON': 'person',
        'EMAIL_ADDRESS': 'email',
        'LOCATION': 'address',
        'ORGANIZATION': 'organization',
        'IT_FISCAL_CODE': 'person',
        'PHONE_NUMBER': 'phone',
        'IBAN_CODE': 'financial',
        'CREDIT_CARD': 'financial'
    }
    return mapping.get(presidio_type, 'other')


def compare_detections(detected: List[Dict], expected: Dict[str, List[Dict]]) -> Dict:
    """Compare detected entities with expected PII"""
    # Normalize detected entities
    detected_by_category = {
        'person': [],
        'email': [],
        'address': [],
        'organization': [],
        'other': []
    }

    for entity in detected:
        category = map_entity_type(entity.get('entity_type', ''))
        entity_text = entity.get('text', entity.get('entity', ''))
        normalized = normalize_text(entity_text)
        detected_by_category[category].append({
            'text': entity_text,
            'normalized': normalized,
            'score': entity.get('score', 0),
            'type': entity.get('entity_type')
        })

    # Calculate metrics for each category
    results = {}

    for category in ['person', 'email', 'address', 'organization']:
        expected_items = expected.get(category, [])
        detected_items = detected_by_category.get(category, [])

        expected_set = {item['normalized'] for item in expected_items}
        detected_set = {item['normalized'] for item in detected_items}

        # Calculate metrics
        true_positives = expected_set & detected_set
        false_negatives = expected_set - detected_set
        false_positives = detected_set - expected_set

        precision = len(true_positives) / len(detected_set) if detected_set else 0
        recall = len(true_positives) / len(expected_set) if expected_set else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        results[category] = {
            'expected_count': len(expected_items),
            'detected_count': len(detected_items),
            'true_positives': list(true_positives),
            'false_negatives': list(false_negatives),
            'false_positives': list(false_positives),
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    # Calculate overall metrics
    total_expected = sum(r['expected_count'] for r in results.values())
    total_detected = sum(r['detected_count'] for r in results.values())
    total_tp = sum(len(r['true_positives']) for r in results.values())
    total_fn = sum(len(r['false_negatives']) for r in results.values())
    total_fp = sum(len(r['false_positives']) for r in results.values())

    overall_precision = total_tp / total_detected if total_detected > 0 else 0
    overall_recall = total_tp / total_expected if total_expected > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

    results['overall'] = {
        'total_expected': total_expected,
        'total_detected': total_detected,
        'true_positives': total_tp,
        'false_negatives': total_fn,
        'false_positives': total_fp,
        'precision': overall_precision,
        'recall': overall_recall,
        'f1': overall_f1
    }

    return results


def main():
    """Run verification test with optimized configuration"""

    print("\n" + "="*80)
    print("VERIFICATION TEST - Optimized Configuration (entity_thresholds DISABLED)")
    print("="*80)

    # Step 1: Load expected PII
    print("\n[Step 1] Loading expected PII from ground truth...")
    expected_pii = load_expected_pii()

    total_expected = sum(len(items) for items in expected_pii.values())
    print(f"  Loaded {total_expected} expected PII entities")

    # Step 2: Extract text from PDF
    print("\n[Step 2] Extracting text from PDF...")
    if not os.path.exists(INPUT_PDF):
        print(f"  ERROR: PDF file not found: {INPUT_PDF}")
        return

    text = extract_text_from_pdf(INPUT_PDF)
    print(f"  Extracted {len(text)} characters from PDF")

    if not text:
        print("  ERROR: No text extracted from PDF")
        return

    # Step 3: Run PII detection with optimized configuration
    print("\n[Step 3] Running PII detection with OPTIMIZED configuration...")
    print("  Configuration:")
    print("    - GLiNER: ENABLED (Italian + Multilingual)")
    print("    - Prefilter: ENABLED")
    print("    - Italian Context: ENABLED")
    print("    - Entity Thresholds: DISABLED (root cause of degradation)")
    print()

    detection_result = detect_pii_optimized(text, depth="balanced")
    detected_entities = detection_result.get('entities', [])
    print(f"  Detected {len(detected_entities)} PII entities")

    # Step 4: Compare results
    print("\n[Step 4] Comparing detected vs expected PII...")
    results = compare_detections(detected_entities, expected_pii)

    # Step 5: Print results
    overall = results['overall']

    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)

    print("\n[OVERALL METRICS]")
    print(f"  Expected PII entities: {overall['total_expected']}")
    print(f"  Detected PII entities: {overall['total_detected']}")
    print(f"  True Positives:  {overall['true_positives']}")
    print(f"  False Negatives: {overall['false_negatives']}")
    print(f"  False Positives: {overall['false_positives']}")
    print(f"  Precision: {overall['precision']:.2%}")
    print(f"  Recall:    {overall['recall']:.2%}")
    print(f"  F1 Score:  {overall['f1']:.2%}")

    # Step 6: Verification against expected baseline
    expected_f1 = 0.0784  # 7.84% from incremental tests
    print("\n" + "="*80)
    print("VERIFICATION AGAINST BASELINE")
    print("="*80)
    print(f"  Expected F1 (from incremental tests): {expected_f1:.2%}")
    print(f"  Actual F1 (optimized config):         {overall['f1']:.2%}")

    if abs(overall['f1'] - expected_f1) < 0.01:  # Within 1% tolerance
        print("\n  VERIFICATION PASSED - F1 score matches expected baseline")
    else:
        difference = overall['f1'] - expected_f1
        print(f"\n  VERIFICATION WARNING - F1 differs by {difference:+.2%}")

    # Step 7: Per-category breakdown
    print("\n" + "-"*80)
    print("[PER-CATEGORY RESULTS]")
    print("-"*80)

    for category in ['person', 'email', 'address', 'organization']:
        result = results[category]
        if result['expected_count'] == 0:
            continue

        print(f"\n{category.upper()}:")
        print(f"  Expected: {result['expected_count']}, Detected: {result['detected_count']}")
        print(f"  Precision: {result['precision']:.2%}, Recall: {result['recall']:.2%}, F1: {result['f1']:.2%}")

        if result['true_positives']:
            print(f"  CORRECTLY DETECTED ({len(result['true_positives'])}):")
            for tp in sorted(result['true_positives']):
                print(f"    - {tp}")

        if result['false_negatives']:
            print(f"  MISSED ({len(result['false_negatives'])}):")
            for fn in sorted(result['false_negatives']):
                print(f"    - {fn}")

    print("\n" + "="*80)

    # Step 8: Save results
    output_file = os.path.join(OUTPUT_FOLDER, "verification_test_results.txt")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("VERIFICATION TEST RESULTS - Optimized Configuration\n")
        f.write("="*80 + "\n\n")
        f.write("Configuration:\n")
        f.write("  - GLiNER: ENABLED (Italian + Multilingual)\n")
        f.write("  - Prefilter: ENABLED\n")
        f.write("  - Italian Context: ENABLED\n")
        f.write("  - Entity Thresholds: DISABLED (root cause fix)\n\n")
        f.write(f"Overall F1 Score: {overall['f1']:.2%}\n")
        f.write(f"Overall Precision: {overall['precision']:.2%}\n")
        f.write(f"Overall Recall: {overall['recall']:.2%}\n\n")
        f.write(f"True Positives: {overall['true_positives']}\n")
        f.write(f"False Negatives: {overall['false_negatives']}\n")
        f.write(f"False Positives: {overall['false_positives']}\n")

    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
