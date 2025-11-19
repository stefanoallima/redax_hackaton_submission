"""
Test redaction with detailed logging to find which entity causes REPUBBLICA redaction
"""
import sys
import logging
from pathlib import Path
import csv

# Add src/python to path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'python'))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_redaction_debug.log', mode='w'),  # Fresh log file
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

print("="*60)
print("REDACTION DEBUG TEST")
print("="*60)
print()
print("This test will re-run the redaction with detailed logging")
print("to find which entity creates the rectangle at x=180-349, y=129-143")
print("that overlaps REPUBBLICA ITALIANA")
print()

# Get absolute paths
script_dir = Path(__file__).parent
csv_path = script_dir / 'test_documents' / 'sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban_MAPPING_TABLE.csv'
input_pdf = str(script_dir / 'test_documents' / 'sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf')

# Load entities from mapping table (the 13 that were actually redacted)
entities_from_csv = []

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        entities_from_csv.append({
            'text': row['Original Text'],
            'entity_type': row['Entity Type'],
            'placeholder': row['Placeholder']
        })

print(f"Loaded {len(entities_from_csv)} entities from mapping table")
print()

# Now we need to simulate getting locations for these entities
# Import the PII detector
from pii_detector import PIIDetector

detector = PIIDetector()

print("Step 1: Getting entity locations using PyMuPDF search...")
print()

# Get locations for all entities
entities_with_locations = []
for i, entity in enumerate(entities_from_csv, 1):
    # Create entity in format expected by get_entity_locations
    entity_obj = {
        'text': entity['text'],
        'entity_type': entity['entity_type'],
        'start': 0,  # Not used for location finding
        'end': len(entity['text'])
    }

    # Get locations
    entity_with_loc = detector.get_entity_locations(input_pdf, [entity_obj])

    if entity_with_loc:
        locations = entity_with_loc[0].get('locations', [])
        entity_obj['locations'] = locations

        print(f"  {i}. '{entity['text'][:40]}' ({entity['entity_type']}): {len(locations)} location(s)")

        # Check if any location overlaps REPUBBLICA
        import fitz
        repubblica_rect = fitz.Rect(212, 121, 383, 137)
        target_rect = fitz.Rect(180.1, 128.8, 349.4, 143.4)

        for loc in locations:
            if loc['page'] == 1:  # First page
                rect_data = loc['rect']
                rect = fitz.Rect(rect_data['x0'], rect_data['y0'], rect_data['x1'], rect_data['y1'])

                # Check if this matches the target rectangle
                rect_match = (
                    abs(rect.x0 - target_rect.x0) < 5 and
                    abs(rect.x1 - target_rect.x1) < 5 and
                    abs(rect.y0 - target_rect.y0) < 5 and
                    abs(rect.y1 - target_rect.y1) < 5
                )

                overlaps_repubblica = rect.intersects(repubblica_rect)

                if rect_match:
                    print(f"     [!] TARGET RECTANGLE FOUND!")
                    print(f"         Position: x={rect.x0:.1f}-{rect.x1:.1f}, y={rect.y0:.1f}-{rect.y1:.1f}")
                elif overlaps_repubblica:
                    overlap = rect & repubblica_rect
                    coverage = (overlap.width * overlap.height) / (repubblica_rect.width * repubblica_rect.height) * 100
                    print(f"     [WARNING] Overlaps REPUBBLICA: {coverage:.1f}%")
                    print(f"               Position: x={rect.x0:.1f}-{rect.x1:.1f}, y={rect.y0:.1f}-{rect.y1:.1f}")

    entities_with_locations.append(entity_obj)

print()
print("="*60)
print("Step 2: Running redaction export with detailed logging...")
print("="*60)
print()

from redaction_exporter import RedactionExporter

exporter = RedactionExporter()

# Run redaction
output_pdf = script_dir / 'test_documents' / 'sentenza_DEBUG_REDACTED.pdf'
output_csv = script_dir / 'test_documents' / 'sentenza_DEBUG_MAPPING.csv'

result = exporter.export_redacted_pdf(
    input_path=input_pdf,
    output_path=str(output_pdf),
    entities=entities_with_locations,
    add_watermark=False,
    clean_metadata=True,
    enable_safety_checks=False
)

if result['status'] == 'success':
    print(f"[OK] Redaction complete: {output_pdf.name}")
    print(f"     Entities redacted: {result['entities_redacted']}")
    print()

    # Export mapping
    mapping_result = exporter.export_mapping_table(str(output_csv))
    print(f"[OK] Mapping exported: {output_csv.name}")
    print()

    print("Check 'test_redaction_debug.log' for detailed entity location logs")
else:
    print(f"[FAIL] Redaction failed: {result.get('error')}")

print()
print("="*60)
print("TEST COMPLETE")
print("="*60)
