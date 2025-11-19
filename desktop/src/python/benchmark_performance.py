"""
Performance Benchmark - Old vs New PII Detection Configuration
Compares performance metrics between old and optimized configurations
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Ground truth for test document (sentenza.txt)
# Street names (Giuseppe Garibaldi, Ciro il Grande) should NOT be detected as persons
GROUND_TRUTH = {
    "PERSON": [
        "Mario Rossi",
        "Laura Bianchi"
    ],
    "EMAIL_ADDRESS": [
        "mario.rossi@example.com",
        "laura.bianchi@pec.avvocati.it"
    ],
    "IT_FISCAL_CODE": [
        "RSSMRA85C15H501X"
    ],
    "ADDRESS": [
        "Via Giuseppe Garibaldi 123, 20100 Milano (MI)"
    ],
    "PHONE_NUMBER": [
        "+39 02 12345678"
    ],
    "IBAN": [
        "IT60X0542811101000000123456"
    ]
}

# Test document (same as test_sentenza_verification.py)
TEST_DOCUMENT = """
SENTENZA N. 1234/2025

Il Tribunale di Milano, in composizione collegiale, ha pronunciato la seguente sentenza
nel procedimento civile promosso da:

Attore: Mario Rossi (C.F. RSSMRA85C15H501X)
Indirizzo: Via Giuseppe Garibaldi 123, 20100 Milano (MI)
Email: mario.rossi@example.com
Telefono: +39 02 12345678

contro

Convenuto: INPS - Istituto Nazionale Previdenza Sociale
con sede in Roma, Via Ciro il Grande 21

Difensore: Avv. Laura Bianchi
Email PEC: laura.bianchi@pec.avvocati.it

IBAN per spese: IT60X0542811101000000123456

Visto il ricorso depositato in data 15 gennaio 2025
"""

def calculate_metrics(detected: List[Dict], ground_truth_category: List[str], entity_type: str) -> Dict:
    """Calculate precision, recall, F1 for a specific entity type"""

    # Get detected entities of this type
    detected_texts = [e['text'] for e in detected if e['entity_type'] == entity_type or
                      (entity_type == 'IBAN' and e['entity_type'] == 'IBAN_CODE')]

    # Normalize for comparison
    detected_normalized = set([text.lower().strip() for text in detected_texts])
    ground_truth_normalized = set([text.lower().strip() for text in ground_truth_category])

    # Calculate metrics
    true_positives = len(detected_normalized & ground_truth_normalized)
    false_positives = len(detected_normalized - ground_truth_normalized)
    false_negatives = len(ground_truth_normalized - detected_normalized)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "detected_count": len(detected_texts),
        "expected_count": len(ground_truth_category)
    }

def run_benchmark_config(config_name: str, detector_params: Dict) -> Dict:
    """Run benchmark with specific configuration"""

    from pii_detector_integrated import IntegratedPIIDetector

    print(f"\n{'='*80}")
    print(f"BENCHMARK: {config_name}")
    print(f"{'='*80}")
    print(f"Configuration: {json.dumps(detector_params, indent=2)}")

    # Initialize detector
    start_init = time.time()
    detector = IntegratedPIIDetector(**detector_params)
    init_time = time.time() - start_init
    print(f"\n[OK] Detector initialized in {init_time:.2f}s")

    # Run detection
    start_detect = time.time()
    result = detector.detect_pii(TEST_DOCUMENT, depth="balanced")
    detect_time = time.time() - start_detect

    entities = result.get('entities', [])
    print(f"[OK] Detection completed in {detect_time:.2f}s")
    print(f"[OK] Detected {len(entities)} entities")

    # Calculate per-entity metrics
    metrics = {}
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for entity_type, ground_truth_list in GROUND_TRUTH.items():
        entity_metrics = calculate_metrics(entities, ground_truth_list, entity_type)
        metrics[entity_type] = entity_metrics

        total_tp += entity_metrics['true_positives']
        total_fp += entity_metrics['false_positives']
        total_fn += entity_metrics['false_negatives']

    # Calculate overall metrics
    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

    # Display results
    print(f"\nOverall Metrics:")
    print(f"  True Positives: {total_tp}")
    print(f"  False Positives: {total_fp}")
    print(f"  False Negatives: {total_fn}")
    print(f"  Precision: {overall_precision*100:.2f}%")
    print(f"  Recall: {overall_recall*100:.2f}%")
    print(f"  F1 Score: {overall_f1*100:.2f}%")

    print(f"\nPer-Entity Metrics:")
    for entity_type, entity_metrics in metrics.items():
        print(f"  {entity_type}:")
        print(f"    F1: {entity_metrics['f1']*100:.2f}% | P: {entity_metrics['precision']*100:.2f}% | R: {entity_metrics['recall']*100:.2f}%")
        print(f"    Detected: {entity_metrics['detected_count']}/{entity_metrics['expected_count']} | TP: {entity_metrics['true_positives']} FP: {entity_metrics['false_positives']} FN: {entity_metrics['false_negatives']}")

    return {
        "config_name": config_name,
        "config_params": detector_params,
        "init_time": init_time,
        "detect_time": detect_time,
        "total_entities": len(entities),
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "precision": overall_precision,
        "recall": overall_recall,
        "f1": overall_f1,
        "per_entity_metrics": metrics
    }

def main():
    """Run performance benchmarks"""

    print("="*80)
    print("PERFORMANCE BENCHMARK SUITE")
    print("Old Configuration vs New Configuration")
    print("="*80)

    # Configuration 1: OLD (Problematic)
    old_config = {
        "enable_gliner": True,
        "use_multi_model": False,         # Single model only
        "enable_prefilter": True,
        "enable_italian_context": True,
        "enable_entity_thresholds": True  # HARMFUL FILTER
    }

    # Configuration 2: NEW (Optimized)
    new_config = {
        "enable_gliner": True,
        "use_multi_model": True,          # Both models
        "enable_prefilter": True,
        "enable_italian_context": True,
        "enable_entity_thresholds": False # DISABLED (42% F1 improvement)
    }

    # Run benchmarks
    results = []

    print("\n" + "="*80)
    print("BENCHMARK 1/2: OLD CONFIGURATION")
    print("="*80)
    old_results = run_benchmark_config("Old Configuration (Problematic)", old_config)
    results.append(old_results)

    print("\n" + "="*80)
    print("BENCHMARK 2/2: NEW CONFIGURATION")
    print("="*80)
    new_results = run_benchmark_config("New Configuration (Optimized)", new_config)
    results.append(new_results)

    # Generate comparison report
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON REPORT")
    print("="*80)

    print(f"\nSpeed Performance:")
    print(f"  Old Init Time: {old_results['init_time']:.2f}s")
    print(f"  New Init Time: {new_results['init_time']:.2f}s")
    if old_results['init_time'] > 0:
        print(f"  Improvement: {((old_results['init_time'] - new_results['init_time']) / old_results['init_time'] * 100):.1f}%")
    else:
        print(f"  Improvement: N/A (models already loaded)")

    print(f"\n  Old Detect Time: {old_results['detect_time']:.2f}s")
    print(f"  New Detect Time: {new_results['detect_time']:.2f}s")
    if old_results['detect_time'] > 0:
        print(f"  Improvement: {((old_results['detect_time'] - new_results['detect_time']) / old_results['detect_time'] * 100):.1f}%")
    else:
        print(f"  Improvement: N/A")

    print(f"\nAccuracy Performance:")
    print(f"  Old F1 Score: {old_results['f1']*100:.2f}%")
    print(f"  New F1 Score: {new_results['f1']*100:.2f}%")
    print(f"  Improvement: {((new_results['f1'] - old_results['f1']) / old_results['f1'] * 100 if old_results['f1'] > 0 else 0):.1f}%")

    print(f"\n  Old Precision: {old_results['precision']*100:.2f}%")
    print(f"  New Precision: {new_results['precision']*100:.2f}%")
    print(f"  Improvement: {((new_results['precision'] - old_results['precision']) / old_results['precision'] * 100 if old_results['precision'] > 0 else 0):.1f}%")

    print(f"\n  Old Recall: {old_results['recall']*100:.2f}%")
    print(f"  New Recall: {new_results['recall']*100:.2f}%")
    print(f"  Improvement: {((new_results['recall'] - old_results['recall']) / old_results['recall'] * 100 if old_results['recall'] > 0 else 0):.1f}%")

    print(f"\nFalse Positive Reduction:")
    print(f"  Old FP Count: {old_results['false_positives']}")
    print(f"  New FP Count: {new_results['false_positives']}")
    print(f"  Reduction: {((old_results['false_positives'] - new_results['false_positives']) / old_results['false_positives'] * 100 if old_results['false_positives'] > 0 else 0):.1f}%")

    print(f"\nPer-Entity Improvements:")
    for entity_type in GROUND_TRUTH.keys():
        old_f1 = old_results['per_entity_metrics'][entity_type]['f1']
        new_f1 = new_results['per_entity_metrics'][entity_type]['f1']
        improvement = ((new_f1 - old_f1) / old_f1 * 100) if old_f1 > 0 else 0
        print(f"  {entity_type}: {old_f1*100:.1f}% -> {new_f1*100:.1f}% ({improvement:+.1f}%)")

    # Save results to JSON
    output_file = Path("output/benchmark_results.json")
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "old_config": old_results,
            "new_config": new_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Benchmark results saved to: {output_file}")
    print("\n" + "="*80)
    print("BENCHMARK COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
