#!/usr/bin/env python3
"""
Automated Validation Test Suite for Phase 1 PII Detection

This script automatically tests the PII detector against comprehensive test cases
and generates a detailed validation report.

Usage:
    python automated_validation_test.py

Output:
    - Console: Real-time progress and summary
    - File: test_results/automated_validation_results_TIMESTAMP.json
    - File: test_results/automated_validation_report_TIMESTAMP.md
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Use the same detector that the desktop app uses
os.environ["USE_NEW_PII_DETECTOR"] = "true"
from pii_detector_integrated import IntegratedPIIDetector


# Test Cases Definition
TEST_CASES = [
    # ========================================================================
    # SECTION A: TRUE POSITIVES - Should Detect PII
    # ========================================================================

    # A1. Simple Names
    {
        "id": "A1-1",
        "category": "Simple Names",
        "text": "Il contratto è firmato da Mario Rossi.",
        "expected_entities": ["Mario Rossi"],
        "expected_types": ["PERSON"],
        "should_detect": True
    },
    {
        "id": "A1-2",
        "category": "Simple Names",
        "text": "La signora Anna Verdi ha presentato ricorso.",
        "expected_entities": ["Anna Verdi"],
        "expected_types": ["PERSON"],
        "should_detect": True
    },

    # A2. ALL CAPS Names
    {
        "id": "A2-1",
        "category": "ALL CAPS Names",
        "text": "MARIO ROSSI è nato a Roma il 15 marzo 1985.",
        "expected_entities": ["MARIO ROSSI"],
        "expected_types": ["PERSON"],
        "should_detect": True
    },
    {
        "id": "A2-2",
        "category": "ALL CAPS Names",
        "text": "GIOVANNI BIANCHI ha sottoscritto il documento.",
        "expected_entities": ["GIOVANNI BIANCHI"],
        "expected_types": ["PERSON"],
        "should_detect": True
    },

    # A3. Names with Apostrophe - Title Case (CRITICAL)
    {
        "id": "A3-1-REGRESSION",
        "category": "Apostrophe Names (Title Case)",
        "text": "Marco Dell'Utri è un politico italiano.",
        "expected_entities": ["Marco Dell'Utri"],
        "expected_types": ["PERSON"],
        "should_detect": True,
        "critical": True,
        "note": "KNOWN REGRESSION - User reported this stopped working"
    },
    {
        "id": "A3-2",
        "category": "Apostrophe Names (Title Case)",
        "text": "Pasquale D'Ascola è nato a Catania nel 1960.",
        "expected_entities": ["Pasquale D'Ascola"],
        "expected_types": ["PERSON"],
        "should_detect": True,
        "critical": True
    },
    {
        "id": "A3-3",
        "category": "Apostrophe Names (Title Case)",
        "text": "Giovanni D'Angelo ha firmato il contratto.",
        "expected_entities": ["Giovanni D'Angelo"],
        "expected_types": ["PERSON"],
        "should_detect": True
    },

    # A4. Names with Apostrophe - ALL CAPS
    {
        "id": "A4-1",
        "category": "Apostrophe Names (ALL CAPS)",
        "text": "MARCO DELL'UTRI è citato nella sentenza.",
        "expected_entities": ["MARCO DELL'UTRI"],
        "expected_types": ["PERSON"],
        "should_detect": True
    },
    {
        "id": "A4-2",
        "category": "Apostrophe Names (ALL CAPS)",
        "text": "PASQUALE D'ASCOLA ha presentato ricorso.",
        "expected_entities": ["PASQUALE D'ASCOLA"],
        "expected_types": ["PERSON"],
        "should_detect": True
    },

    # A5. Names in Strong PII Context
    {
        "id": "A5-1",
        "category": "Names in Strong Context",
        "text": "Il sottoscritto Mario Rossi, nato a Roma il 15/03/1985.",
        "expected_entities": ["Mario Rossi"],
        "expected_types": ["PERSON"],
        "should_detect": True
    },

    # A6. Italian Document IDs
    {
        "id": "A6-1",
        "category": "Italian Document IDs",
        "text": "Codice Fiscale: RSSMRA85C15H501X",
        "expected_entities": ["RSSMRA85C15H501X"],
        "expected_types": ["IT_FISCAL_CODE"],
        "should_detect": True
    },
    {
        "id": "A6-2",
        "category": "Italian Document IDs",
        "text": "Patente di guida: FI1234567A",
        "expected_entities": ["FI1234567A"],
        "expected_types": ["IT_DRIVER_LICENSE"],
        "should_detect": True
    },

    # A7. Contact Information
    {
        "id": "A7-1",
        "category": "Contact Information",
        "text": "Email: mario.rossi@example.com",
        "expected_entities": ["mario.rossi@example.com"],
        "expected_types": ["EMAIL_ADDRESS"],
        "should_detect": True
    },
    {
        "id": "A7-2",
        "category": "Contact Information",
        "text": "Telefono: +39 333 1234567",
        "expected_entities": ["+39 333 1234567"],
        "expected_types": ["PHONE_NUMBER"],
        "should_detect": True
    },

    # A8. ALL CAPS Emails
    {
        "id": "A8-1",
        "category": "ALL CAPS Emails",
        "text": "MARIO.ROSSI@EXAMPLE.COM",
        "expected_entities": ["MARIO.ROSSI@EXAMPLE.COM"],
        "expected_types": ["EMAIL_ADDRESS"],
        "should_detect": True
    },

    # A11. Email with Professional Prefixes (User Reported)
    {
        "id": "A11-1-USER-REPORTED",
        "category": "Emails with Prefixes",
        "text": "avv.gabrielecatarinacci@pec.it",
        "expected_entities": ["avv.gabrielecatarinacci@pec.it"],
        "expected_types": ["EMAIL_ADDRESS"],
        "should_detect": True,
        "critical": True,
        "note": "USER REPORTED - Email with prefix not detected"
    },

    # ========================================================================
    # SECTION B: TRUE NEGATIVES - Should NOT Detect
    # ========================================================================

    # B1. Job Titles (Previously FALSE POSITIVES)
    {
        "id": "B1-1-FIXED",
        "category": "Job Titles (False Positive Fix)",
        "text": "Il Chief Technology Officer ha presentato la relazione tecnica.",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False,
        "critical": True,
        "note": "Previously FALSE POSITIVE - Should be fixed by deny list"
    },
    {
        "id": "B1-2-FIXED",
        "category": "Job Titles (False Positive Fix)",
        "text": "Il Chief Executive Officer della società ha firmato l'accordo.",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False,
        "critical": True
    },

    # B2. Organizational Terms (Previously FALSE POSITIVES)
    {
        "id": "B2-1-FIXED",
        "category": "Organizational Terms (False Positive Fix)",
        "text": "Gli organismi Intergovernativi hanno approvato la risoluzione.",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False,
        "critical": True,
        "note": "Previously FALSE POSITIVE - Should be fixed by deny list"
    },

    # B3. Document Labels (Previously FALSE POSITIVES)
    {
        "id": "B3-1-FIXED",
        "category": "Document Labels (False Positive Fix)",
        "text": "Firmato Da: [signature]",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False,
        "critical": True,
        "note": "Previously FALSE POSITIVE - Should be fixed by deny list"
    },
    {
        "id": "B3-2-FIXED",
        "category": "Document Labels (False Positive Fix)",
        "text": "Sottoscritto Da: il rappresentante legale",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False
    },

    # B4. Legal Institutions
    {
        "id": "B4-1",
        "category": "Legal Institutions",
        "text": "Il Tribunale di Milano ha emesso sentenza.",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False
    },
    {
        "id": "B4-2",
        "category": "Legal Institutions",
        "text": "La Corte di Cassazione ha rigettato il ricorso.",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False
    },

    # B5. Government Agencies
    {
        "id": "B5-1",
        "category": "Government Agencies",
        "text": "L'INPS ha rilasciato il certificato pensionistico.",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False
    },
    {
        "id": "B5-2",
        "category": "Government Agencies",
        "text": "L'INAIL ha liquidato l'indennizzo.",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False
    },

    # B7. Legal References
    {
        "id": "B7-1",
        "category": "Legal References",
        "text": "Secondo l'articolo 123 del codice civile.",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False
    },

    # ========================================================================
    # SECTION C: EDGE CASES
    # ========================================================================

    # C1. Invalid Codice Fiscale (Checksum validation should fail)
    {
        "id": "C1-1",
        "category": "Invalid Document IDs",
        "text": "Codice Fiscale invalido: RSSMRA85C15XXXX",
        "expected_entities": [],
        "expected_types": [],
        "should_detect": False,
        "note": "Invalid checksum - should NOT detect"
    },
]


def initialize_detector() -> IntegratedPIIDetector:
    """Initialize the PII detector with Phase 1 configuration."""
    print("Initializing PII detector...")
    detector = IntegratedPIIDetector(
        enable_gliner=False,  # GLiNER not installed
        enable_prefilter=True,
        enable_italian_context=True,
        enable_entity_thresholds=True
    )
    print("[OK] Detector initialized\n")
    return detector


def run_test_case(detector: IntegratedPIIDetector, test_case: Dict) -> Dict:
    """
    Run a single test case and return results.

    Returns:
        {
            "test_id": str,
            "passed": bool,
            "detected_entities": List[Dict],
            "expected_entities": List[str],
            "details": str
        }
    """
    test_id = test_case["id"]
    text = test_case["text"]
    expected_entities = test_case["expected_entities"]
    should_detect = test_case["should_detect"]

    # Run detection
    result = detector.detect_pii(text, depth="balanced")
    detected = result["entities"]  # IntegratedPIIDetector returns dict with 'entities' key

    # Extract detected entity texts
    detected_texts = [e["text"] for e in detected]
    detected_types = [e["entity_type"] for e in detected]

    # Determine if test passed
    if should_detect:
        # Should detect: Check if expected entities were found
        passed = any(exp in detected_texts for exp in expected_entities)
        details = f"Expected: {expected_entities}, Detected: {detected_texts}"
    else:
        # Should NOT detect: Check if nothing was detected
        passed = len(detected) == 0
        details = f"Expected: NO DETECTION, Detected: {detected_texts if detected else 'NONE'}"

    return {
        "test_id": test_id,
        "category": test_case["category"],
        "passed": passed,
        "detected_entities": detected,
        "expected_entities": expected_entities,
        "detected_count": len(detected),
        "details": details,
        "critical": test_case.get("critical", False),
        "note": test_case.get("note", "")
    }


def run_all_tests(detector: IntegratedPIIDetector) -> List[Dict]:
    """Run all test cases and return results."""
    results = []
    total = len(TEST_CASES)

    print(f"Running {total} test cases...\n")
    print("=" * 80)

    for i, test_case in enumerate(TEST_CASES, 1):
        test_id = test_case["id"]
        category = test_case["category"]
        critical = test_case.get("critical", False)

        # Run test
        result = run_test_case(detector, test_case)
        results.append(result)

        # Print progress
        status = "[PASS]" if result["passed"] else "[FAIL]"
        critical_mark = " [CRITICAL]" if critical else ""
        print(f"[{i}/{total}] {test_id} - {category}{critical_mark}")
        print(f"  {status}: {result['details']}")

        if not result["passed"] and critical:
            print(f"  [WARNING] CRITICAL TEST FAILED!")

        if result.get("note"):
            print(f"  Note: {result['note']}")

        print()

    print("=" * 80)
    return results


def calculate_metrics(results: List[Dict]) -> Dict:
    """Calculate validation metrics."""
    # Separate by should_detect
    true_positive_tests = [r for r in results if any(tc["id"] == r["test_id"] and tc["should_detect"] for tc in TEST_CASES)]
    true_negative_tests = [r for r in results if any(tc["id"] == r["test_id"] and not tc["should_detect"] for tc in TEST_CASES)]

    # Calculate metrics
    tp = sum(1 for r in true_positive_tests if r["passed"])
    fn = sum(1 for r in true_positive_tests if not r["passed"])
    tn = sum(1 for r in true_negative_tests if r["passed"])
    fp = sum(1 for r in true_negative_tests if not r["passed"])

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Critical tests
    critical_tests = [r for r in results if r.get("critical", False)]
    critical_passed = sum(1 for r in critical_tests if r["passed"])
    critical_failed = len(critical_tests) - critical_passed

    return {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "true_positives": tp,
        "false_negatives": fn,
        "true_negatives": tn,
        "false_positives": fp,
        "critical_tests": len(critical_tests),
        "critical_passed": critical_passed,
        "critical_failed": critical_failed
    }


def generate_report(results: List[Dict], metrics: Dict, output_dir: str = "../../test_results"):
    """Generate markdown and JSON reports."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create output directory
    output_path = Path(__file__).parent / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    # Save JSON results
    json_file = output_path / f"automated_validation_results_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "metrics": metrics,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    # Generate markdown report
    md_file = output_path / f"automated_validation_report_{timestamp}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# Automated Validation Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Detector:** IntegratedPIIDetector (pii_detector_integrated.py)\n")
        f.write(f"**Test Cases:** {metrics['total_tests']}\n\n")

        f.write("---\n\n")
        f.write("## Summary\n\n")

        # Overall status
        overall_pass = metrics['accuracy'] >= 0.80 and metrics['critical_failed'] == 0
        status = "[PASS]" if overall_pass else "[FAIL]"
        f.write(f"**Overall Status:** {status}\n\n")

        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| **Accuracy** | {metrics['accuracy']:.2%} |\n")
        f.write(f"| **Precision** | {metrics['precision']:.2%} |\n")
        f.write(f"| **Recall** | {metrics['recall']:.2%} |\n")
        f.write(f"| **F1 Score** | {metrics['f1_score']:.2%} |\n")
        f.write(f"| Tests Passed | {metrics['passed']} / {metrics['total_tests']} |\n")
        f.write(f"| Tests Failed | {metrics['failed']} / {metrics['total_tests']} |\n")
        f.write(f"| Critical Passed | {metrics['critical_passed']} / {metrics['critical_tests']} |\n")
        f.write(f"| **Critical Failed** | {metrics['critical_failed']} / {metrics['critical_tests']} |\n\n")

        f.write("---\n\n")
        f.write("## Detailed Results\n\n")

        # Failed tests
        failed_tests = [r for r in results if not r["passed"]]
        if failed_tests:
            f.write("### [FAIL] Failed Tests\n\n")
            for result in failed_tests:
                critical_mark = " **[CRITICAL]**" if result.get("critical") else ""
                f.write(f"#### {result['test_id']} - {result['category']}{critical_mark}\n\n")
                f.write(f"- **Status:** FAILED\n")
                f.write(f"- **Details:** {result['details']}\n")
                if result.get("note"):
                    f.write(f"- **Note:** {result['note']}\n")
                f.write("\n")

        # Passed tests
        f.write("### [PASS] Passed Tests\n\n")
        passed_tests = [r for r in results if r["passed"]]
        for result in passed_tests:
            f.write(f"- {result['test_id']} - {result['category']}\n")

        f.write("\n---\n\n")
        f.write("## Recommendations\n\n")

        if overall_pass:
            f.write("[PASS] **Validation PASSED** - Ready to proceed\n\n")
            f.write("- Architecture improvements confirmed\n")
            f.write("- False positive fixes working\n")
            f.write("- Consider implementing Phase 2 enhancements\n")
        else:
            f.write("[FAIL] **Validation FAILED** - Do NOT proceed\n\n")
            f.write("- Fix failed tests before continuing\n")
            f.write("- Focus on critical failures first\n")
            f.write("- Re-run validation after fixes\n")

        if metrics['critical_failed'] > 0:
            f.write(f"\n[WARNING] **{metrics['critical_failed']} CRITICAL TEST(S) FAILED** - IMMEDIATE ACTION REQUIRED\n")

    return json_file, md_file


def print_summary(metrics: Dict):
    """Print summary to console."""
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {metrics['total_tests']}")
    print(f"Passed: {metrics['passed']} ({metrics['accuracy']:.2%})")
    print(f"Failed: {metrics['failed']}")
    print()
    print(f"Accuracy:  {metrics['accuracy']:.2%}")
    print(f"Precision: {metrics['precision']:.2%}")
    print(f"Recall:    {metrics['recall']:.2%}")
    print(f"F1 Score:  {metrics['f1_score']:.2%}")
    print()
    print(f"True Positives:  {metrics['true_positives']}")
    print(f"False Negatives: {metrics['false_negatives']}")
    print(f"True Negatives:  {metrics['true_negatives']}")
    print(f"False Positives: {metrics['false_positives']}")
    print()
    print(f"Critical Tests: {metrics['critical_tests']}")
    print(f"Critical Passed: {metrics['critical_passed']}")
    print(f"Critical Failed: {metrics['critical_failed']}")
    print("=" * 80)

    # Overall verdict
    if metrics['accuracy'] >= 0.80 and metrics['critical_failed'] == 0:
        print("\n[PASS] VALIDATION PASSED - Ready to proceed!")
    else:
        print("\n[FAIL] VALIDATION FAILED - Fix issues before proceeding")
        if metrics['critical_failed'] > 0:
            print(f"[WARNING] {metrics['critical_failed']} CRITICAL TEST(S) FAILED - IMMEDIATE ACTION REQUIRED")


def main():
    """Main execution."""
    print("=" * 80)
    print("AUTOMATED VALIDATION TEST - Phase 1 PII Detection")
    print("=" * 80)
    print()

    try:
        # Initialize detector
        detector = initialize_detector()

        # Run tests
        results = run_all_tests(detector)

        # Calculate metrics
        metrics = calculate_metrics(results)

        # Print summary
        print_summary(metrics)

        # Generate reports
        json_file, md_file = generate_report(results, metrics)

        print(f"\nReports generated:")
        print(f"  - JSON: {json_file}")
        print(f"  - Markdown: {md_file}")

    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
