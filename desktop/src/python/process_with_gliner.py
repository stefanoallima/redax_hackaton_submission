# -*- coding: utf-8 -*-
"""
Process document with GLiNER-enhanced detection
Saves results to organized folders with timestamp naming
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import modules
from file_utils import FileManager
from document_processor import DocumentProcessor
from pii_detector import PIIDetector
from pii_detector_enhanced import EnhancedPIIDetector
from detection_config import DetectionConfig

def process_document(input_file: str):
    """
    Process document with comparison: Presidio vs GLiNER-enhanced

    Args:
        input_file: Path to input document
    """
    print("=" * 80)
    print("GLiNER-Enhanced Document Processing")
    print("=" * 80)

    # Initialize file manager
    fm = FileManager()

    # Get all file paths
    paths = fm.get_file_paths(input_file)

    print(f"\nInput file: {Path(input_file).name}")
    print(f"File size: {Path(input_file).stat().st_size / 1024:.1f} KB")

    print(f"\nOutput files will be saved as:")
    print(f"  Processed: {paths['processed'].name}")
    print(f"  Entities:  {paths['entities_json'].name}")
    print()

    # Step 1: Extract text from document
    print("[Step 1] Extracting text from document...")
    try:
        doc_result = DocumentProcessor.process_document(input_file)

        if doc_result['status'] != 'success':
            print(f"[ERROR] Document processing failed: {doc_result.get('error')}")
            return

        full_text = doc_result['full_text']
        pages = doc_result.get('metadata', {}).get('pages', 1)

        print(f"[OK] Extracted {len(full_text):,} characters from {pages} page(s)")
        print(f"Preview: {full_text[:150]}...")
        print()
    except Exception as e:
        print(f"[ERROR] Text extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: Presidio-only detection (baseline)
    print("=" * 80)
    print("[Step 2] Baseline Detection - Presidio Only (Fast mode)")
    print("=" * 80)

    try:
        detector_presidio = PIIDetector()
        config_fast = DetectionConfig(depth='fast')

        result_presidio = detector_presidio.process_document(doc_result, config=config_fast)

        if result_presidio['status'] != 'success':
            print(f"[ERROR] Presidio detection failed: {result_presidio.get('error')}")
            return

        presidio_entities = result_presidio['entities']
        presidio_summary = result_presidio.get('entity_summary', {})

        print(f"\n[OK] Presidio detected {len(presidio_entities)} entities:")
        for entity_type, count in sorted(presidio_summary.items(), key=lambda x: -x[1]):
            print(f"  - {entity_type:25s}: {count:3d}")

        print(f"\nSample entities (showing first 10):")
        for i, entity in enumerate(presidio_entities[:10], 1):
            text = entity['text'][:50].ljust(50)
            score = entity['score']
            print(f"  {i:2d}. [{entity['entity_type']:20s}] {text} ({score:.0%})")

        if len(presidio_entities) > 10:
            print(f"  ... and {len(presidio_entities) - 10} more")

        print()
    except Exception as e:
        print(f"[ERROR] Presidio detection failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: GLiNER-enhanced detection (Balanced mode)
    print("=" * 80)
    print("[Step 3] Enhanced Detection - GLiNER Italian Model (Balanced mode)")
    print("=" * 80)

    try:
        detector_enhanced = EnhancedPIIDetector(enable_gliner=True)
        config_balanced = DetectionConfig(depth='balanced')

        print("[INFO] Loading GLiNER Italian model (this may take 10-20s on first run)...")
        result_balanced = detector_enhanced.process_document(doc_result, config=config_balanced)

        if result_balanced['status'] != 'success':
            print(f"[ERROR] GLiNER detection failed: {result_balanced.get('error')}")
            return

        balanced_entities = result_balanced['entities']
        balanced_summary = result_balanced.get('entity_summary', {})
        source_summary_balanced = result_balanced.get('source_summary', {})

        print(f"\n[OK] GLiNER (Balanced) detected {len(balanced_entities)} entities:")
        for entity_type, count in sorted(balanced_summary.items(), key=lambda x: -x[1]):
            print(f"  - {entity_type:25s}: {count:3d}")

        print(f"\nDetection sources:")
        for source, count in source_summary_balanced.items():
            print(f"  - {source:25s}: {count:3d} entities")

        print(f"\nSample entities (showing first 10):")
        for i, entity in enumerate(balanced_entities[:10], 1):
            text = entity['text'][:40].ljust(40)
            score = entity['score']
            source = entity.get('source', 'unknown')
            print(f"  {i:2d}. [{entity['entity_type']:20s}] {text} ({score:.0%}) [{source}]")

        if len(balanced_entities) > 10:
            print(f"  ... and {len(balanced_entities) - 10} more")

        print()
    except Exception as e:
        print(f"[ERROR] GLiNER (Balanced) detection failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: GLiNER-enhanced detection (Thorough mode - both models)
    print("=" * 80)
    print("[Step 4] Maximum Detection - Both GLiNER Models (Thorough mode)")
    print("=" * 80)

    try:
        config_thorough = DetectionConfig(depth='thorough')

        print("[INFO] Loading GLiNER multilingual PII model...")
        result_thorough = detector_enhanced.process_document(doc_result, config=config_thorough)

        if result_thorough['status'] != 'success':
            print(f"[ERROR] GLiNER (Thorough) detection failed: {result_thorough.get('error')}")
            return

        thorough_entities = result_thorough['entities']
        thorough_summary = result_thorough.get('entity_summary', {})
        source_summary_thorough = result_thorough.get('source_summary', {})

        print(f"\n[OK] GLiNER (Thorough) detected {len(thorough_entities)} entities:")
        for entity_type, count in sorted(thorough_summary.items(), key=lambda x: -x[1]):
            print(f"  - {entity_type:25s}: {count:3d}")

        print(f"\nDetection sources:")
        for source, count in source_summary_thorough.items():
            print(f"  - {source:25s}: {count:3d} entities")

        print(f"\nSample entities (showing first 10):")
        for i, entity in enumerate(thorough_entities[:10], 1):
            text = entity['text'][:40].ljust(40)
            score = entity['score']
            source = entity.get('source', 'unknown')
            print(f"  {i:2d}. [{entity['entity_type']:20s}] {text} ({score:.0%}) [{source}]")

        if len(thorough_entities) > 10:
            print(f"  ... and {len(thorough_entities) - 10} more")

        print()
    except Exception as e:
        print(f"[ERROR] GLiNER (Thorough) detection failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 5: Comparison & Analysis
    print("=" * 80)
    print("[Step 5] Comparison & Accuracy Improvement")
    print("=" * 80)

    presidio_count = len(presidio_entities)
    balanced_count = len(balanced_entities)
    thorough_count = len(thorough_entities)

    improvement_balanced = ((balanced_count - presidio_count) / presidio_count * 100) if presidio_count > 0 else 0
    improvement_thorough = ((thorough_count - presidio_count) / presidio_count * 100) if presidio_count > 0 else 0

    print(f"\nEntity Count Comparison:")
    print(f"  Presidio only (Fast):        {presidio_count:4d} entities (baseline)")
    print(f"  + GLiNER Italian (Balanced): {balanced_count:4d} entities ({improvement_balanced:+.1f}%)")
    print(f"  + Both GLiNER (Thorough):    {thorough_count:4d} entities ({improvement_thorough:+.1f}%)")

    # Find new entities
    presidio_texts = {e['text'] for e in presidio_entities}
    balanced_texts = {e['text'] for e in balanced_entities}
    thorough_texts = {e['text'] for e in thorough_entities}

    new_in_balanced = balanced_texts - presidio_texts
    new_in_thorough = thorough_texts - balanced_texts

    print(f"\nNew Entities Discovered:")
    if new_in_balanced:
        print(f"  Balanced mode: +{len(new_in_balanced)} new entities")
        for text in list(new_in_balanced)[:5]:
            entity = next((e for e in balanced_entities if e['text'] == text), None)
            if entity:
                print(f"    - {entity['entity_type']:20s}: {text[:50]}")
        if len(new_in_balanced) > 5:
            print(f"    ... and {len(new_in_balanced) - 5} more")

    if new_in_thorough:
        print(f"\n  Thorough mode: +{len(new_in_thorough)} additional entities")
        for text in list(new_in_thorough)[:5]:
            entity = next((e for e in thorough_entities if e['text'] == text), None)
            if entity:
                print(f"    - {entity['entity_type']:20s}: {text[:50]}")
        if len(new_in_thorough) > 5:
            print(f"    ... and {len(new_in_thorough) - 5} more")

    print()

    # Step 6: Save results
    print("=" * 80)
    print("[Step 6] Saving Results")
    print("=" * 80)

    try:
        # Save entities JSON (thorough mode - best results)
        entities_json_path = paths['entities_json']

        results_data = {
            'timestamp': datetime.now().isoformat(),
            'input_file': str(Path(input_file).name),
            'document_info': {
                'pages': pages,
                'characters': len(full_text)
            },
            'detection_modes': {
                'presidio_only': {
                    'entities_count': presidio_count,
                    'entities': presidio_entities,
                    'summary': presidio_summary
                },
                'gliner_balanced': {
                    'entities_count': balanced_count,
                    'entities': balanced_entities,
                    'summary': balanced_summary,
                    'sources': source_summary_balanced
                },
                'gliner_thorough': {
                    'entities_count': thorough_count,
                    'entities': thorough_entities,
                    'summary': thorough_summary,
                    'sources': source_summary_thorough
                }
            },
            'improvement': {
                'balanced_vs_presidio': f"{improvement_balanced:+.1f}%",
                'thorough_vs_presidio': f"{improvement_thorough:+.1f}%"
            }
        }

        with open(entities_json_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Entities saved to:")
        print(f"  {entities_json_path}")

        # Print file size
        file_size = entities_json_path.stat().st_size / 1024
        print(f"  File size: {file_size:.1f} KB")

        print()
    except Exception as e:
        print(f"[ERROR] Failed to save results: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("=" * 80)
    print("[SUCCESS] Processing Complete!")
    print("=" * 80)

    print(f"\nSummary:")
    print(f"  Document: {Path(input_file).name}")
    print(f"  Pages: {pages}")
    print(f"  Characters: {len(full_text):,}")
    print(f"  Detection improvement: {improvement_thorough:+.1f}% (Presidio → GLiNER)")
    print(f"  Best mode: Thorough ({thorough_count} entities)")
    print(f"  Models used: {', '.join(source_summary_thorough.keys())}")

    print(f"\nResults saved to:")
    print(f"  {paths['entities_json']}")

    print(f"\nRecommendation:")
    if improvement_thorough > 10:
        print(f"  GLiNER detected {improvement_thorough:.1f}% more entities!")
        print(f"  Use 'Thorough' mode for this document type")
    elif improvement_thorough > 0:
        print(f"  GLiNER detected {improvement_thorough:.1f}% more entities")
        print(f"  Use 'Balanced' or 'Thorough' mode for better coverage")
    else:
        print(f"  Presidio coverage is already excellent for this document")
        print(f"  'Fast' mode is sufficient")

    print()


if __name__ == "__main__":
    # Check if file provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "CV_Luca_Cervone_Ita.pdf"

    if not Path(input_file).exists():
        print(f"[ERROR] File not found: {input_file}")
        sys.exit(1)

    process_document(input_file)
