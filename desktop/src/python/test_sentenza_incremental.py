"""
Incremental Filter Testing - Identify Problematic Preprocessing Layers

This test runs PII detection with each filter enabled individually to identify
which preprocessing layer is causing the performance degradation.

Test Configurations:
- Baseline: No filters (F1 = 12.63%)
- Test A: Only entity_thresholds enabled
- Test B: Only prefilter enabled
- Test C: Only italian_context enabled
- Full: All filters enabled (F1 = 4.82%)

Goal: Identify which filter(s) cause the most false negatives
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


def detect_pii_with_config(
    text: str,
    enable_prefilter: bool = False,
    enable_italian_context: bool = False,
    enable_entity_thresholds: bool = False,
    depth: str = "balanced"
) -> Dict:
    """Run PII detection with specific filter configuration"""
    try:
        os.environ["USE_NEW_PII_DETECTOR"] = "true"
        from pii_detector_integrated import IntegratedPIIDetector

        detector = IntegratedPIIDetector(
            enable_gliner=True,
            use_multi_model=True,
            enable_prefilter=enable_prefilter,
            enable_italian_context=enable_italian_context,
            enable_entity_thresholds=enable_entity_thresholds
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

    # Calculate overall metrics
    total_expected = sum(len(items) for items in expected.values())
    total_detected = sum(len(items) for items in detected_by_category.values() if items)

    # Find true positives across all categories
    total_tp = 0
    for category in ['person', 'email', 'address', 'organization']:
        expected_items = expected.get(category, [])
        detected_items = detected_by_category.get(category, [])

        expected_set = {item['normalized'] for item in expected_items}
        detected_set = {item['normalized'] for item in detected_items}

        true_positives = expected_set & detected_set
        total_tp += len(true_positives)

    # Calculate metrics
    precision = total_tp / total_detected if total_detected > 0 else 0
    recall = total_tp / total_expected if total_expected > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'total_expected': total_expected,
        'total_detected': total_detected,
        'true_positives': total_tp,
        'false_negatives': total_expected - total_tp,
        'false_positives': total_detected - total_tp,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def run_incremental_tests(text: str, expected_pii: Dict):
    """Run all incremental filter tests"""

    test_configs = [
        {
            'name': 'Baseline (No Filters)',
            'enable_prefilter': False,
            'enable_italian_context': False,
            'enable_entity_thresholds': False
        },
        {
            'name': 'Test A (Entity Thresholds Only)',
            'enable_prefilter': False,
            'enable_italian_context': False,
            'enable_entity_thresholds': True
        },
        {
            'name': 'Test B (Prefilter Only)',
            'enable_prefilter': True,
            'enable_italian_context': False,
            'enable_entity_thresholds': False
        },
        {
            'name': 'Test C (Italian Context Only)',
            'enable_prefilter': False,
            'enable_italian_context': True,
            'enable_entity_thresholds': False
        },
        {
            'name': 'Full Pipeline (All Filters)',
            'enable_prefilter': True,
            'enable_italian_context': True,
            'enable_entity_thresholds': True
        }
    ]

    results_summary = []

    print("\n" + "="*80)
    print("INCREMENTAL FILTER TESTING - IDENTIFYING PROBLEMATIC LAYERS")
    print("="*80)

    for config in test_configs:
        print(f"\n{'='*80}")
        print(f"TESTING: {config['name']}")
        print(f"{'='*80}")
        print(f"  Prefilter: {config['enable_prefilter']}")
        print(f"  Italian Context: {config['enable_italian_context']}")
        print(f"  Entity Thresholds: {config['enable_entity_thresholds']}")
        print()

        # Run detection
        detection_result = detect_pii_with_config(
            text,
            enable_prefilter=config['enable_prefilter'],
            enable_italian_context=config['enable_italian_context'],
            enable_entity_thresholds=config['enable_entity_thresholds'],
            depth="balanced"
        )

        detected_entities = detection_result.get('entities', [])
        print(f"  Detected {len(detected_entities)} entities")

        # Compare results
        comparison = compare_detections(detected_entities, expected_pii)

        # Print metrics
        print(f"\n  METRICS:")
        print(f"    Expected:    {comparison['total_expected']}")
        print(f"    Detected:    {comparison['total_detected']}")
        print(f"    True Pos:    {comparison['true_positives']}")
        print(f"    False Neg:   {comparison['false_negatives']}")
        print(f"    False Pos:   {comparison['false_positives']}")
        print(f"    Precision:   {comparison['precision']:.2%}")
        print(f"    Recall:      {comparison['recall']:.2%}")
        print(f"    F1 Score:    {comparison['f1']:.2%}")

        # Store results
        results_summary.append({
            'config': config['name'],
            'f1': comparison['f1'],
            'precision': comparison['precision'],
            'recall': comparison['recall'],
            'tp': comparison['true_positives'],
            'fn': comparison['false_negatives'],
            'fp': comparison['false_positives']
        })

    # Print summary comparison
    print("\n" + "="*80)
    print("SUMMARY - FILTER IMPACT ANALYSIS")
    print("="*80)
    print(f"\n{'Configuration':<40} {'F1 Score':<12} {'Precision':<12} {'Recall':<12}")
    print("-"*80)

    for result in results_summary:
        print(f"{result['config']:<40} {result['f1']:<12.2%} {result['precision']:<12.2%} {result['recall']:<12.2%}")

    # Calculate filter impact
    baseline_f1 = results_summary[0]['f1']
    print("\n" + "="*80)
    print("FILTER IMPACT (compared to baseline):")
    print("="*80)

    for i, result in enumerate(results_summary[1:], 1):
        impact = result['f1'] - baseline_f1
        impact_pct = (impact / baseline_f1 * 100) if baseline_f1 > 0 else 0
        symbol = "✓" if impact >= 0 else "✗"
        print(f"{symbol} {result['config']:<40} {impact:+.2%} ({impact_pct:+.1f}%)")

    print("\n" + "="*80)

    return results_summary


def main():
    """Run incremental filter tests"""

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

    # Step 3: Run incremental tests
    print("\n[Step 3] Running incremental filter tests...")
    results = run_incremental_tests(text, expected_pii)

    # Step 4: Save results
    output_file = os.path.join(OUTPUT_FOLDER, "incremental_filter_results.txt")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("INCREMENTAL FILTER TEST RESULTS\n")
        f.write("="*80 + "\n\n")

        for result in results:
            f.write(f"{result['config']}\n")
            f.write(f"  F1: {result['f1']:.2%}\n")
            f.write(f"  Precision: {result['precision']:.2%}\n")
            f.write(f"  Recall: {result['recall']:.2%}\n")
            f.write(f"  TP: {result['tp']}, FN: {result['fn']}, FP: {result['fp']}\n\n")

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
