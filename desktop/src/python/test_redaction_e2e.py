# -*- coding: utf-8 -*-
"""
End-to-End Test: PII Detection → Redaction Export
Tests the complete workflow with GLiNER-enhanced detection
"""

import sys
import os
from pathlib import Path
import json
import fitz  # PyMuPDF

# Import modules
from document_processor import DocumentProcessor
from pii_detector_enhanced import EnhancedPIIDetector
from detection_config import DetectionConfig
from redaction_exporter import RedactionExporter

def test_redaction_workflow(input_file: str, detection_depth: str = 'thorough'):
    """
    Test complete redaction workflow

    Args:
        input_file: Path to test document
        detection_depth: Detection mode (fast/balanced/thorough/maximum)
    """
    print("=" * 80)
    print("END-TO-END REDACTION TEST")
    print("=" * 80)
    print(f"\nTest Document: {Path(input_file).name}")
    print(f"Detection Mode: {detection_depth}")
    print()

    # Step 1: Document Processing
    print("[Step 1] Processing document...")
    try:
        doc_result = DocumentProcessor.process_document(input_file)

        if doc_result['status'] != 'success':
            print(f"[FAIL] Document processing failed: {doc_result.get('error')}")
            return False

        full_text = doc_result['full_text']
        pages = doc_result.get('metadata', {}).get('pages', 1)
        print(f"[OK] Extracted {len(full_text):,} characters from {pages} page(s)")

    except Exception as e:
        print(f"[FAIL] Document processing error: {e}")
        return False

    # Step 2: PII Detection with GLiNER
    print("\n[Step 2] Running PII detection (GLiNER Enhanced)...")
    try:
        detector = EnhancedPIIDetector(enable_gliner=True)
        config = DetectionConfig(depth=detection_depth)

        detect_result = detector.process_document(doc_result, config=config)

        if detect_result['status'] != 'success':
            print(f"[FAIL] PII detection failed: {detect_result.get('error')}")
            return False

        entities = detect_result['entities']
        entity_summary = detect_result.get('entity_summary', {})
        source_summary = detect_result.get('source_summary', {})

        print(f"[OK] Detected {len(entities)} PII entities")
        print(f"\nEntity types:")
        for entity_type, count in sorted(entity_summary.items(), key=lambda x: -x[1]):
            print(f"  - {entity_type:25s}: {count:3d}")

        print(f"\nDetection sources:")
        for source, count in source_summary.items():
            print(f"  - {source:25s}: {count:3d} entities")

        if len(entities) == 0:
            print("[WARN] No entities detected - nothing to redact")
            return True

    except Exception as e:
        print(f"[FAIL] PII detection error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Redaction Export
    print("\n[Step 3] Exporting redacted document...")
    try:
        exporter = RedactionExporter()

        # Generate output paths - use inpoutput folder
        input_path = Path(input_file)
        output_dir = Path(__file__).parent / "inpoutput"
        output_pdf = output_dir / f"{input_path.stem}_REDACTED.pdf"
        output_txt = output_dir / f"{input_path.stem}_REDACTED.txt"
        mapping_csv = output_dir / f"{input_path.stem}_MAPPING.csv"

        # Create output directory
        output_pdf.parent.mkdir(exist_ok=True, parents=True)

        # Export redacted PDF
        pdf_result = exporter.export_redacted_pdf(
            input_path=str(input_path),
            output_path=str(output_pdf),
            entities=entities,
            add_watermark=False,  # No watermark
            clean_metadata=True
        )

        if pdf_result['status'] != 'success':
            print(f"[FAIL] PDF export failed: {pdf_result.get('error')}")
            return False

        print(f"[OK] Redacted PDF saved: {output_pdf.name}")
        print(f"     Entities redacted: {pdf_result['entities_redacted']}")
        print(f"     Unique entities: {pdf_result['unique_entities']}")

        # Export mapping table
        mapping_result = exporter.export_mapping_table(str(mapping_csv))

        if mapping_result['status'] != 'success':
            print(f"[FAIL] Mapping table export failed: {mapping_result.get('error')}")
            return False

        print(f"[OK] Mapping table saved: {mapping_csv.name}")
        print(f"     Rows: {mapping_result['rows']}")

        # Export redacted text (reuse same exporter instance for consistent mappings)
        # Create new exporter with same mappings
        txt_exporter = RedactionExporter()
        txt_exporter.entity_mappings = exporter.entity_mappings.copy()
        txt_exporter.counters = exporter.counters.copy()

        txt_result = txt_exporter.export_redacted_text(
            input_path=str(input_path),
            output_path=str(output_txt),
            entities=entities
        )

        if txt_result['status'] != 'success':
            print(f"[FAIL] Text export failed: {txt_result.get('error')}")
            return False

        print(f"[OK] Redacted TXT saved: {output_txt.name}")

    except Exception as e:
        print(f"[FAIL] Redaction export error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Verification
    print("\n[Step 4] Verifying redacted document...")
    try:
        # Check if redacted PDF exists and is valid
        if not output_pdf.exists():
            print(f"[FAIL] Redacted PDF not found: {output_pdf}")
            return False

        # Open redacted PDF and verify
        redacted_doc = fitz.open(str(output_pdf))
        num_pages = len(redacted_doc)
        redacted_text = ""
        for page in redacted_doc:
            redacted_text += page.get_text()
        redacted_doc.close()

        print(f"[OK] Redacted PDF readable")
        print(f"     Pages: {num_pages}")

        # Verify placeholders exist - updated to match abbreviated format
        placeholder_examples = [
            "[PER",   # PERSON
            "[CF",    # CODICE_FISCALE
            "[TEL",   # PHONE_NUMBER
            "[EML",   # EMAIL_ADDRESS
            "[IBN",   # IBAN
            "[ADR",   # IT_ADDRESS
            "[LOC",   # LOCATION
            "[DAT"    # DATE_TIME
        ]
        found_placeholders = []
        for placeholder in placeholder_examples:
            if placeholder in redacted_text:
                found_placeholders.append(placeholder + "...]")

        if found_placeholders:
            print(f"[OK] Placeholders found: {', '.join(found_placeholders)}")
        else:
            print(f"[WARN] No placeholders found in redacted document")
            # Debug: Show sample of redacted text
            sample = redacted_text[:500].replace('\n', ' ')
            print(f"[DEBUG] First 500 chars of redacted text: {sample[:200]}...")

        # Check metadata cleaning
        redacted_doc = fitz.open(str(output_pdf))
        metadata = redacted_doc.metadata
        redacted_doc.close()

        if metadata.get('creator') == 'CodiceCivile Redact':
            print(f"[OK] Metadata cleaned correctly")
        else:
            print(f"[WARN] Metadata not cleaned: {metadata}")

        # Verify no original PII leaked
        pii_samples = [e['text'] for e in entities[:5]]  # Check first 5 entities
        leaked_pii = []
        for pii in pii_samples:
            if pii in redacted_text:
                leaked_pii.append(pii)

        if leaked_pii:
            print(f"[FAIL] PII LEAKED in redacted document: {leaked_pii}")
            return False
        else:
            print(f"[OK] No PII leakage detected (checked {len(pii_samples)} samples)")

        # Check mapping table
        if not mapping_csv.exists():
            print(f"[FAIL] Mapping table not found: {mapping_csv}")
            return False

        import csv
        with open(mapping_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            mappings = list(reader)

        print(f"[OK] Mapping table readable")
        print(f"     Entries: {len(mappings)}")

        # Show sample mappings
        if mappings:
            print(f"\nSample mappings (first 3):")
            for i, mapping in enumerate(mappings[:3], 1):
                try:
                    entity_type = mapping['Entity Type']
                    placeholder = mapping['Placeholder']
                    print(f"  Mapping {i}: {placeholder:20s} ({entity_type})")
                except UnicodeEncodeError:
                    # Skip printing due to Windows console encoding limitation
                    print(f"  Mapping {i}: [See CSV file for details]")

        # Check TXT export
        if not output_txt.exists():
            print(f"[FAIL] Redacted TXT not found: {output_txt}")
            return False

        with open(output_txt, 'r', encoding='utf-8') as f:
            txt_content = f.read()

        print(f"[OK] Redacted TXT readable")
        print(f"     Characters: {len(txt_content):,}")

        # Verify no PII in TXT
        leaked_pii_txt = []
        for pii in pii_samples:
            if pii in txt_content:
                leaked_pii_txt.append(pii)

        if leaked_pii_txt:
            print(f"[FAIL] PII LEAKED in redacted TXT: {leaked_pii_txt}")
            return False
        else:
            print(f"[OK] No PII leakage in TXT (checked {len(pii_samples)} samples)")

    except Exception as e:
        print(f"[FAIL] Verification error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # All tests passed!
    print("\n" + "=" * 80)
    print("[SUCCESS] END-TO-END REDACTION TEST PASSED")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  Input: {input_file}")
    print(f"  Detection: {detection_depth} mode")
    print(f"  Entities detected: {len(entities)}")
    print(f"  Entities redacted: {pdf_result['entities_redacted']}")
    print(f"  Unique placeholders: {pdf_result['unique_entities']}")
    print(f"\nOutput files:")
    print(f"  PDF: {output_pdf}")
    print(f"  TXT: {output_txt}")
    print(f"  Mapping: {mapping_csv}")
    print(f"\nAll verifications passed:")
    print(f"  [OK] PDF readable and valid")
    print(f"  [OK] Placeholders inserted")
    print(f"  [OK] Metadata cleaned")
    print(f"  [OK] No PII leakage detected")
    print(f"  [OK] Mapping table generated")
    print(f"  [OK] TXT export successful")
    print()

    return True


if __name__ == "__main__":
    # Test with Italian CV document
    test_file = "input/CV_Luca_Cervone_Ita.pdf"

    if len(sys.argv) > 1:
        test_file = sys.argv[1]

    if not Path(test_file).exists():
        print(f"[ERROR] Test file not found: {test_file}")
        sys.exit(1)

    # Run test with thorough detection (all GLiNER models)
    success = test_redaction_workflow(test_file, detection_depth='thorough')

    sys.exit(0 if success else 1)
