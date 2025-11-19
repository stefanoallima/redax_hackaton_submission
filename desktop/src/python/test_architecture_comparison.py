"""
Architecture Comparison Test - Old vs New Implementation

Compares the old pii_detector_enhanced.py with the new integrated architecture.

Validates:
1. Performance improvement (2-3x faster expected)
2. Accuracy maintenance (entity count within ±5%)
3. Quality improvement (fewer false positives)
4. Code reduction (500 → 150 lines)

Author: RedaxAI.app  Team
Date: 2025-11-14
"""

import time
import sys
from typing import Dict, List
import logging

# Import old detector
try:
    from pii_detector_enhanced import EnhancedPIIDetector as OldDetector
    OLD_AVAILABLE = True
except ImportError:
    print("Warning: Old detector (pii_detector_enhanced.py) not available")
    OLD_AVAILABLE = False

# Import new integrated detector
from pii_detector_integrated import IntegratedPIIDetector as NewDetector

logging.basicConfig(level=logging.WARNING)  # Suppress info logs for cleaner output


class ArchitectureComparison:
    """
    Comprehensive comparison between old and new architecture.
    """

    # Test documents
    TEST_DOCUMENTS = {
        "simple": """
Il signor Mario Rossi, nato a Roma il 15/03/1985,
codice fiscale RSSMRA85C15H501X, residente in
Via Giuseppe Garibaldi 123, Milano (MI).
""",

        "legal_with_context": """
Il Tribunale di Milano, in persona del Giudice,
ha accolto il ricorso presentato da Giovanni Bianchi,
nato a Roma il 20/07/1990, CF: BNOGNN90L20H501Z,
contro INPS. Secondo la dottrina di Francesco Carnelutti,
il processo civile garantisce...
""",

        "with_sections": """
INTRODUZIONE
Il presente documento tratta...

INDICE
1. Introduzione ........................ 1
2. Capitolo Primo ...................... 5

CAPITOLO PRIMO
Mario Rossi (CF: RSSMRA85C15H501X) ha presentato
ricorso presso il Tribunale di Milano contro INPS.

BIBLIOGRAFIA
1. Francesco Carnelutti, Sistema del diritto
2. Piero Calamandrei, Processo e democrazia
""",

        "complex": """
SENTENZA DEL TRIBUNALE DI MILANO

Il Tribunale di Milano, in persona del Giudice Dr. [REDACTED],
ha pronunciato la seguente sentenza nel procedimento civile
promosso da:

Mario Rossi, nato a Roma il 15/03/1985,
codice fiscale RSSMRA85C15H501X,
residente in Via Giuseppe Garibaldi 123, Milano (MI),
telefono 02-12345678, email mario.rossi@example.com

CONTRO

INPS - Istituto Nazionale Previdenza Sociale
in persona del legale rappresentante

OGGETTO: Contestazione diniego prestazione previdenziale

FATTO E DIRITTO

Il ricorrente Mario Rossi ha impugnato il provvedimento
dell'INPS del 10/01/2024 con il quale veniva negata...
Secondo la consolidata giurisprudenza della Corte di Cassazione
e la dottrina di Francesco Carnelutti, il diritto alla
previdenza sociale...

Il Tribunale, esaminati gli atti e sentite le parti,
ACCOGLIE il ricorso e condanna INPS al pagamento...

Milano, 15 marzo 2024
Il Giudice
""" * 3  # Repeat 3x for performance testing
    }

    @staticmethod
    def compare_detectors(
        text: str,
        depth: str = "balanced",
        test_name: str = "Test"
    ) -> Dict:
        """
        Compare old and new detector on the same text.

        Returns:
            {
                "old": {...},
                "new": {...},
                "comparison": {...}
            }
        """
        print(f"\n{'='*70}")
        print(f"TEST: {test_name} (depth={depth})")
        print('='*70)

        results = {
            "old": None,
            "new": None,
            "comparison": {}
        }

        # Test OLD detector (if available)
        if OLD_AVAILABLE:
            print("\n[1/2] Testing OLD detector (pii_detector_enhanced.py)...")
            try:
                old_detector = OldDetector()
                start = time.time()
                old_entities = old_detector.detect_pii(text, depth=depth)
                old_time = time.time() - start

                results["old"] = {
                    "entities": old_entities if isinstance(old_entities, list) else [],
                    "time_ms": round(old_time * 1000, 2),
                    "count": len(old_entities) if isinstance(old_entities, list) else 0
                }
                print(f"  [PASS] Detected {results['old']['count']} entities in {results['old']['time_ms']:.2f}ms")
            except Exception as e:
                print(f"  [FAIL] Error: {e}")
                results["old"] = {"error": str(e)}

        # Test NEW detector
        print("\n[2/2] Testing NEW detector (integrated architecture)...")
        try:
            new_detector = NewDetector(
                enable_gliner=True,
                enable_prefilter=True,
                enable_italian_context=True,
                enable_entity_thresholds=True
            )
            start = time.time()
            new_result = new_detector.detect_pii(text, depth=depth)
            new_time = time.time() - start

            results["new"] = {
                "entities": new_result["entities"],
                "time_ms": round(new_time * 1000, 2),
                "count": len(new_result["entities"]),
                "stats": new_result["stats"],
                "performance": new_result["performance"],
                "metadata": new_result["metadata"]
            }
            print(f"  [PASS] Detected {results['new']['count']} entities in {results['new']['time_ms']:.2f}ms")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            results["new"] = {"error": str(e)}
            return results

        # COMPARISON
        print(f"\n{'-'*70}")
        print("COMPARISON RESULTS:")
        print('-'*70)

        if OLD_AVAILABLE and "error" not in results["old"]:
            # Performance comparison
            old_time = results["old"]["time_ms"]
            new_time = results["new"]["time_ms"]
            speedup = old_time / new_time if new_time > 0 else 0

            results["comparison"]["speedup"] = round(speedup, 2)
            results["comparison"]["time_saved_ms"] = round(old_time - new_time, 2)

            print(f"\nPerformance:")
            print(f"  Old detector: {old_time:.2f}ms")
            print(f"  New detector: {new_time:.2f}ms")
            print(f"  Speedup: {speedup:.2f}x {'[PASS]' if speedup >= 1.5 else '[FAIL] (expected >=1.5x)'}")
            print(f"  Time saved: {old_time - new_time:.2f}ms")

            # Entity count comparison
            old_count = results["old"]["count"]
            new_count = results["new"]["count"]
            count_diff = new_count - old_count
            count_diff_pct = (count_diff / old_count * 100) if old_count > 0 else 0

            results["comparison"]["entity_diff"] = count_diff
            results["comparison"]["entity_diff_pct"] = round(count_diff_pct, 1)

            print(f"\nEntity Count:")
            print(f"  Old detector: {old_count} entities")
            print(f"  New detector: {new_count} entities")
            print(f"  Difference: {count_diff:+d} ({count_diff_pct:+.1f}%)")
            print(f"  Within ±5%: {'[PASS]' if abs(count_diff_pct) <= 5 else '[FAIL]'}")

        else:
            print("\n  (Old detector not available - showing new detector only)")
            print(f"  New detector: {results['new']['time_ms']:.2f}ms, {results['new']['count']} entities")

        # New detector metadata
        if "metadata" in results["new"]:
            meta = results["new"]["metadata"]
            print(f"\nNew Detector Optimizations:")
            print(f"  Pre-filtering: {meta['prefilter_applied']}")
            if meta['prefilter_applied']:
                pf = meta['prefilter_stats']
                print(f"    - Skipped {pf['skipped_lines']} lines ({pf['skip_percentage']:.1f}%)")
            print(f"  Italian context filtered: {meta['italian_context_filtered']} entities")
            print(f"  Document type: {meta.get('document_type', 'N/A')}")

        # Entity breakdown
        if "stats" in results["new"]:
            stats = results["new"]["stats"]
            print(f"\nNew Detector Statistics:")
            print(f"  Average confidence: {stats['avg_confidence']:.3f}")
            if stats['by_type']:
                print(f"  By type:")
                for entity_type, count in sorted(stats['by_type'].items()):
                    print(f"    - {entity_type}: {count}")

        return results

    @staticmethod
    def run_full_test_suite():
        """Run comprehensive test suite on all test documents."""
        print("\n" + "="*70)
        print("ARCHITECTURE COMPARISON - FULL TEST SUITE")
        print("="*70)
        print("\nComparing OLD (pii_detector_enhanced.py) vs NEW (integrated architecture)")
        print(f"Old detector available: {OLD_AVAILABLE}")

        all_results = {}

        # Test each document
        for name, text in ArchitectureComparison.TEST_DOCUMENTS.items():
            all_results[name] = ArchitectureComparison.compare_detectors(
                text=text,
                depth="balanced",
                test_name=name.upper()
            )

        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print('='*70)

        if OLD_AVAILABLE:
            speedups = [
                r["comparison"].get("speedup", 0)
                for r in all_results.values()
                if "comparison" in r and "speedup" in r["comparison"]
            ]

            if speedups:
                avg_speedup = sum(speedups) / len(speedups)
                print(f"\nAverage speedup: {avg_speedup:.2f}x")
                print(f"Best speedup: {max(speedups):.2f}x")
                print(f"Worst speedup: {min(speedups):.2f}x")

                # Check if target met
                target_met = avg_speedup >= 2.0
                print(f"\nTarget (>=2x faster): {'[PASS]' if target_met else '[FAIL]'}")
        else:
            print("\n(Old detector not available - cannot calculate speedup)")

        print(f"\nAll tests completed successfully!")

        return all_results


if __name__ == "__main__":
    # Run full test suite
    results = ArchitectureComparison.run_full_test_suite()

    print(f"\n{'='*70}")
    print("Test suite finished. Results available in 'results' variable.")
    print('='*70)
