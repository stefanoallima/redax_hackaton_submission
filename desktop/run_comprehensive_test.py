"""
Comprehensive test to verify the page numbering fix
Simulates the full redaction workflow from the desktop app
"""
import sys
import json
from pathlib import Path

# Add src/python to path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'python'))

print("="*70)
print("COMPREHENSIVE REDACTION TEST")
print("="*70)
print()

# Import the main processing functions
from document_processor import DocumentProcessor
from pii_detector import PIIDetector
from redaction_exporter import RedactionExporter

# Get absolute paths
script_dir = Path(__file__).parent
test_file = script_dir / 'test_documents' / 'sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf'

if not test_file.exists():
    print(f"[ERROR] Test file not found: {test_file}")
    sys.exit(1)

print(f"Test file: {test_file.name}")
print()

# Step 1: Extract text from PDF
print("Step 1: Extracting text from PDF...")
print("-" * 70)

processor = DocumentProcessor()
doc_result = processor.process_document(str(test_file))

if doc_result['status'] != 'success':
    print(f"[ERROR] Document processing failed: {doc_result.get('error')}")
    sys.exit(1)

print(f"[OK] Extracted text from {doc_result['metadata']['page_count']} pages")
print(f"     Total characters: {doc_result['metadata']['total_chars']}")
print()

# Step 2: Detect PII entities
print("Step 2: Detecting PII entities...")
print("-" * 70)

detector = PIIDetector()
entities = detector.detect_pii(doc_result['full_text'])

print(f"[OK] Detected {len(entities)} PII entities")
print()
print("Entity types found:")
entity_types = {}
for e in entities:
    entity_types[e['entity_type']] = entity_types.get(e['entity_type'], 0) + 1

for etype, count in sorted(entity_types.items()):
    print(f"  - {etype}: {count}")
print()

# Step 3: Get entity locations in PDF
print("Step 3: Finding entity locations in PDF...")
print("-" * 70)

entities_with_locations = detector.get_entity_locations(str(test_file), entities)

print(f"[OK] Found locations for {len(entities_with_locations)} entities")
print()

# Show key entities and their page locations
print("Key entities and their pages:")
for entity in entities_with_locations[:15]:  # First 15
    text = entity['text'][:40]
    pages = set([loc['page'] for loc in entity.get('locations', [])])
    pages_str = ', '.join([f"Page {p}" for p in sorted(pages)])
    print(f"  - '{text}' ({entity['entity_type']}): {pages_str}")
print()

# CRITICAL CHECK: Verify email is on Page 2
print("CRITICAL VERIFICATION:")
print("-" * 70)

email_entity = next((e for e in entities_with_locations if 'marcovannini' in e['text'].lower()), None)

if email_entity:
    email_pages = [loc['page'] for loc in email_entity.get('locations', [])]
    email_text = email_entity['text']

    print(f"Email: '{email_text}'")
    print(f"  Pages: {email_pages}")

    if 2 in email_pages and 1 not in email_pages:
        print(f"  [OK] Email correctly located on Page 2 ONLY")
    elif 1 in email_pages:
        print(f"  [ERROR] Email incorrectly on Page 1 - PAGE NUMBERING BUG STILL PRESENT!")
    else:
        print(f"  [WARNING] Email not on expected pages")
else:
    print("[WARNING] Email entity not found")

print()

# Step 4: Export redacted PDF
print("Step 4: Exporting redacted PDF...")
print("-" * 70)

output_dir = script_dir / 'test_documents'
output_pdf = output_dir / f"{test_file.stem}_TEST_REDACTED.pdf"
output_csv = output_dir / f"{test_file.stem}_TEST_MAPPING.csv"

exporter = RedactionExporter()

# Convert entities to format expected by exporter (add accepted flag)
for entity in entities_with_locations:
    entity['accepted'] = True

result = exporter.export_redacted_pdf(
    input_path=str(test_file),
    output_path=str(output_pdf),
    entities=entities_with_locations,
    add_watermark=False,
    clean_metadata=True,
    enable_safety_checks=False
)

if result['status'] != 'success':
    print(f"[ERROR] Redaction export failed: {result.get('error')}")
    sys.exit(1)

print(f"[OK] Redacted PDF created: {output_pdf.name}")
print(f"     Entities redacted: {result['entities_redacted']}")
print()

# Export mapping table
mapping_result = exporter.export_mapping_table(str(output_csv))
if mapping_result['status'] == 'success':
    print(f"[OK] Mapping table created: {output_csv.name}")
    print(f"     Rows: {mapping_result['rows']}")
else:
    print(f"[WARNING] Mapping table export failed: {mapping_result.get('error')}")

print()

# Step 5: Verify the redacted PDF
print("Step 5: Verifying redacted PDF...")
print("-" * 70)

import fitz

doc = fitz.open(str(output_pdf))

# Check Page 1: REPUBBLICA ITALIANA should be VISIBLE
page1 = doc[0]
repubblica_results = page1.search_for('REPUBBLICA ITALIANA')

if repubblica_results:
    print("[OK] Page 1: 'REPUBBLICA ITALIANA' is VISIBLE (not redacted)")
    for rect in repubblica_results:
        print(f"     Position: x={rect.x0:.1f}-{rect.x1:.1f}, y={rect.y0:.1f}-{rect.y1:.1f}")
else:
    # Check if partially redacted
    partial_results = page1.search_for('ANA')
    if partial_results:
        print("[ERROR] Page 1: 'REPUBBLICA ITALIANA' is PARTIALLY REDACTED")
        print("        THIS IS THE BUG WE WERE TRYING TO FIX!")
    else:
        print("[ERROR] Page 1: 'REPUBBLICA ITALIANA' is COMPLETELY REDACTED")

print()

# Check Page 2: Email should be REDACTED
if len(doc) >= 2:
    page2 = doc[1]
    email_rect = fitz.Rect(180.1, 128.8, 349.4, 143.4)
    text_at_email = page2.get_textbox(email_rect)

    if 'EML' in text_at_email or '[' in text_at_email:
        print("[OK] Page 2: Email is REDACTED")
        print(f"     Redacted text: '{text_at_email.strip()[:40]}'")
    else:
        print(f"[ERROR] Page 2: Email NOT redacted")
        print(f"        Found: '{text_at_email.strip()[:40]}'")
else:
    print("[WARNING] Document has fewer than 2 pages")

doc.close()

print()
print("="*70)
print("TEST SUMMARY")
print("="*70)
print()

# Final verdict
if repubblica_results and ('EML' in text_at_email or '[' in text_at_email):
    print("[SUCCESS] All tests passed!")
    print()
    print("✅ REPUBBLICA ITALIANA visible on Page 1")
    print("✅ Email redacted on Page 2")
    print("✅ Page numbering fix is working correctly")
    print()
    print("Next step: Test in the desktop application")
else:
    print("[FAILURE] Some tests failed")
    print()
    if not repubblica_results:
        print("❌ REPUBBLICA ITALIANA is redacted (should be visible)")
    if 'EML' not in text_at_email and '[' not in text_at_email:
        print("❌ Email is not redacted (should be redacted)")
    print()
    print("Please review the output above for details")

print()
print("="*70)
