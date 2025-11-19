"""
End-to-End Test for Real Legal Document (Sentenza)
Tests PII detection accuracy against manually annotated ground truth
"""

import os
import sys
import csv
import logging
from typing import List, Dict, Set, Tuple
from pathlib import Path
import pdfplumber  # Better email/structured data extraction for legal documents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logs from other modules
logging.getLogger('presidio-analyzer').setLevel(logging.WARNING)
logging.getLogger('pii_detector').setLevel(logging.WARNING)
logging.getLogger('pii_detector_integrated').setLevel(logging.WARNING)

# Paths
INPUT_PDF = "input/sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex.pdf"
EXPECTED_PII_CSV = "../../../docs/sentenza_document_all_pii.txt"  # From desktop/src/python to docs/
OUTPUT_FOLDER = "output/test_results"


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, strip whitespace)"""
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
            difficulty = row['presidio_detection'].strip()

            if category in expected:
                expected[category].append({
                    'text': pii_text,
                    'normalized': normalize_text(pii_text),
                    'difficulty': difficulty
                })

    return expected


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF file using pdfplumber.

    Advantages over PyMuPDF:
    - Better email address extraction (preserves @ symbols and structure)
    - Preserves structured data (tables, forms)
    - Better handling of Italian legal document formatting
    - More accurate for documents with embedded objects
    """
    try:
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:  # Only add non-empty pages
                    text_parts.append(page_text)

        full_text = "\n\n".join(text_parts)  # Double newline between pages
        logger.info(f"Extracted {len(full_text)} chars from {len(text_parts)} pages")
        return full_text

    except Exception as e:
        logger.error(f"Error extracting PDF text with pdfplumber: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return ""


def detect_pii(text: str, depth: str = "balanced") -> Dict:
    """Run PII detection using IntegratedPIIDetector"""
    try:
        # Force new detector
        os.environ["USE_NEW_PII_DETECTOR"] = "true"

        from pii_detector_integrated import IntegratedPIIDetector

        detector = IntegratedPIIDetector(
            enable_gliner=True,  # ENABLED: Using GLiNER for better Italian NER
            use_multi_model=True,  # ENABLED: Use both Italian + Multilingual models for better email/address detection
            enable_prefilter=True,
            enable_italian_context=True,
            enable_entity_thresholds=True
        )

        result = detector.detect_pii(text, depth=depth)
        return result
    except Exception as e:
        logger.error(f"Error detecting PII: {e}")
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
    """
    Compare detected entities with expected PII

    Returns:
        Dictionary with comparison results
    """
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
        # IntegratedPIIDetector uses 'text' not 'entity'
        entity_text = entity.get('text', entity.get('entity', ''))
        normalized = normalize_text(entity_text)
        detected_by_category[category].append({
            'text': entity_text,
            'normalized': normalized,
            'score': entity.get('score', 0),
            'type': entity.get('entity_type')
        })

    # Calculate matches for each category
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

        # Breakdown by difficulty
        easy_tp = sum(1 for item in expected_items if item['normalized'] in true_positives and item['difficulty'] == 'easy')
        moderate_tp = sum(1 for item in expected_items if item['normalized'] in true_positives and item['difficulty'] == 'moderate')
        difficult_tp = sum(1 for item in expected_items if item['normalized'] in true_positives and item['difficulty'] == 'difficult')

        easy_fn = sum(1 for item in expected_items if item['normalized'] in false_negatives and item['difficulty'] == 'easy')
        moderate_fn = sum(1 for item in expected_items if item['normalized'] in false_negatives and item['difficulty'] == 'moderate')
        difficult_fn = sum(1 for item in expected_items if item['normalized'] in false_negatives and item['difficulty'] == 'difficult')

        # Calculate precision, recall, F1
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
            'f1': f1,
            'breakdown': {
                'easy': {'tp': easy_tp, 'fn': easy_fn},
                'moderate': {'tp': moderate_tp, 'fn': moderate_fn},
                'difficult': {'tp': difficult_tp, 'fn': difficult_fn}
            }
        }

    return results


def print_results(results: Dict):
    """Print formatted test results"""
    print("\n" + "="*80)
    print("SENTENZA E2E TEST RESULTS")
    print("="*80)

    # Overall metrics
    total_expected = sum(r['expected_count'] for r in results.values())
    total_detected = sum(r['detected_count'] for r in results.values())
    total_tp = sum(len(r['true_positives']) for r in results.values())
    total_fn = sum(len(r['false_negatives']) for r in results.values())
    total_fp = sum(len(r['false_positives']) for r in results.values())

    overall_precision = total_tp / total_detected if total_detected > 0 else 0
    overall_recall = total_tp / total_expected if total_expected > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

    print("\n[OVERALL METRICS]")
    print(f"  Expected PII entities: {total_expected}")
    print(f"  Detected PII entities: {total_detected}")
    print(f"  True Positives:  {total_tp}")
    print(f"  False Negatives: {total_fn}")
    print(f"  False Positives: {total_fp}")
    print(f"  Precision: {overall_precision:.2%}")
    print(f"  Recall:    {overall_recall:.2%}")
    print(f"  F1 Score:  {overall_f1:.2%}")

    # Per-category results
    print("\n" + "-"*80)
    print("[PER-CATEGORY RESULTS]")
    print("-"*80)

    for category, result in results.items():
        if result['expected_count'] == 0:
            continue

        print(f"\n{category.upper()}:")
        print(f"  Expected: {result['expected_count']}, Detected: {result['detected_count']}")
        print(f"  Precision: {result['precision']:.2%}, Recall: {result['recall']:.2%}, F1: {result['f1']:.2%}")

        # Breakdown by difficulty
        breakdown = result['breakdown']
        print(f"  Difficulty Breakdown:")
        for diff in ['easy', 'moderate', 'difficult']:
            tp = breakdown[diff]['tp']
            fn = breakdown[diff]['fn']
            total = tp + fn
            if total > 0:
                rate = tp / total * 100
                print(f"    {diff.capitalize()}: {tp}/{total} detected ({rate:.0f}%)")

        # Show missed entities
        if result['false_negatives']:
            print(f"  MISSED ({len(result['false_negatives'])}):")
            for missed in sorted(result['false_negatives']):
                print(f"    - {missed}")

        # Show false positives
        if result['false_positives']:
            print(f"  FALSE POSITIVES ({len(result['false_positives'])}):")
            for fp in sorted(result['false_positives']):
                print(f"    - {fp}")

        # Show correctly detected
        if result['true_positives']:
            print(f"  CORRECTLY DETECTED ({len(result['true_positives'])}):")
            for tp in sorted(result['true_positives']):
                print(f"    - {tp}")

    # Test verdict
    print("\n" + "="*80)
    print("[TEST VERDICT]")
    print("="*80)

    if overall_f1 >= 0.95:
        print("EXCELLENT: F1 >= 95%")
    elif overall_f1 >= 0.90:
        print("GOOD: F1 >= 90%")
    elif overall_f1 >= 0.80:
        print("ACCEPTABLE: F1 >= 80%")
    elif overall_f1 >= 0.70:
        print("NEEDS IMPROVEMENT: F1 >= 70%")
    else:
        print("POOR: F1 < 70%")

    # Critical issues
    if total_fn > 0:
        print(f"\nWARNING: {total_fn} PII entities were MISSED!")

    if total_fp > 0:
        print(f"WARNING: {total_fp} false positives detected")

    print("\n" + "="*80)


def save_results_to_file(results: Dict, output_path: str):
    """Save detailed results to a file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("SENTENZA E2E TEST RESULTS\n")
        f.write("="*80 + "\n\n")

        # Write overall metrics
        total_expected = sum(r['expected_count'] for r in results.values())
        total_detected = sum(r['detected_count'] for r in results.values())
        total_tp = sum(len(r['true_positives']) for r in results.values())

        overall_precision = total_tp / total_detected if total_detected > 0 else 0
        overall_recall = total_tp / total_expected if total_expected > 0 else 0
        overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

        f.write(f"Overall Precision: {overall_precision:.2%}\n")
        f.write(f"Overall Recall: {overall_recall:.2%}\n")
        f.write(f"Overall F1 Score: {overall_f1:.2%}\n\n")

        # Write per-category details
        for category, result in results.items():
            if result['expected_count'] == 0:
                continue

            f.write(f"\n{category.upper()}:\n")
            f.write(f"  Expected: {result['expected_count']}\n")
            f.write(f"  Detected: {result['detected_count']}\n")
            f.write(f"  Precision: {result['precision']:.2%}\n")
            f.write(f"  Recall: {result['recall']:.2%}\n")
            f.write(f"  F1: {result['f1']:.2%}\n\n")

            if result['false_negatives']:
                f.write(f"  MISSED:\n")
                for missed in sorted(result['false_negatives']):
                    f.write(f"    - {missed}\n")

            if result['false_positives']:
                f.write(f"  FALSE POSITIVES:\n")
                for fp in sorted(result['false_positives']):
                    f.write(f"    - {fp}\n")


def main():
    """Run the end-to-end test"""
    print("\n" + "="*80)
    print("SENTENZA E2E TEST - PII Detection Accuracy Validation")
    print("="*80)

    # Step 1: Load expected PII
    print("\n[Step 1] Loading expected PII from ground truth...")
    expected_pii = load_expected_pii()

    total_expected = sum(len(items) for items in expected_pii.values())
    print(f"  Loaded {total_expected} expected PII entities:")
    for category, items in expected_pii.items():
        if items:
            print(f"    - {category}: {len(items)}")

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

    # Step 3: Run PII detection
    print("\n[Step 3] Running PII detection (IntegratedPIIDetector)...")
    detection_result = detect_pii(text, depth="balanced")

    detected_entities = detection_result.get('entities', [])
    print(f"  Detected {len(detected_entities)} PII entities")

    # Step 4: Compare results
    print("\n[Step 4] Comparing detected vs expected PII...")

    # Debug: Show what was detected
    print(f"\nDEBUG - Sample detected entities:")
    for i, entity in enumerate(detected_entities[:10]):  # Show first 10
        entity_text = entity.get('text', entity.get('entity', ''))
        print(f"  {i+1}. {entity.get('entity_type')}: '{entity_text}' (score: {entity.get('score', 0):.2f})")

    results = compare_detections(detected_entities, expected_pii)

    # Step 5: Print results
    print_results(results)

    # Step 6: Save results
    output_file = os.path.join(OUTPUT_FOLDER, "sentenza_e2e_results.txt")
    save_results_to_file(results, output_file)
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
