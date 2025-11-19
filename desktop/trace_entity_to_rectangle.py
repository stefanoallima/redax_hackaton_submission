"""
Trace exactly which entity causes rectangle #4 to be created at x=180-349, y=129-143
This simulates the redaction process with detailed logging
"""
import fitz
import csv
import re

# Read the 13 entities from mapping table
entities = []
with open('test_documents/sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban_MAPPING_TABLE.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        entities.append({
            'text': row['Original Text'],
            'entity_type': row['Entity Type'],
            'placeholder': row['Placeholder']
        })

print(f"=== TRACING {len(entities)} ENTITIES ===")
print()

# Open original PDF
doc = fitz.open('test_documents/sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf')
page = doc[0]

# Target rectangle that overlaps REPUBBLICA
target_rect = fitz.Rect(180.1, 128.8, 349.4, 143.4)
print(f"Target redaction rectangle: x=180.1-349.4, y=128.8-143.4")
print(f"(This overlaps REPUBBLICA ITALIANA)")
print()

# REPUBBLICA position for reference
repubblica_rect = fitz.Rect(212, 121, 383, 137)
print(f"REPUBBLICA ITALIANA position: x=212-383, y=121-137")
print()

# Search for each entity with all strategies (matching pii_detector.py logic)
def find_entity_locations(entity_text):
    """Replicate the fuzzy search logic from pii_detector.py"""
    locations = []

    # Strategy 1: Exact match
    text_instances = page.search_for(entity_text)
    if text_instances:
        locations.extend(text_instances)
        return locations, "exact"

    # Strategy 2: Normalized (remove whitespace)
    normalized_text = re.sub(r'\s+', ' ', entity_text).strip()
    if normalized_text != entity_text:
        text_instances = page.search_for(normalized_text)
        if text_instances:
            locations.extend(text_instances)
            return locations, "normalized"

    # Strategy 3: Case variations
    for variant in [entity_text.lower(), entity_text.upper(), entity_text.title()]:
        text_instances = page.search_for(variant)
        if text_instances:
            locations.extend(text_instances)
            return locations, f"case-variant: {variant}"

    # Strategy 4: Word boundary multi-word matching
    if ' ' in normalized_text:
        words = normalized_text.split()
        if len(words) >= 2:
            first_word_instances = page.search_for(words[0])
            last_word_instances = page.search_for(words[-1])

            if first_word_instances and last_word_instances:
                for first_rect in first_word_instances:
                    for last_rect in last_word_instances:
                        # Same line check
                        if abs(first_rect.y0 - last_rect.y0) < 5:
                            combined_rect = fitz.Rect(
                                min(first_rect.x0, last_rect.x0),
                                min(first_rect.y0, last_rect.y0),
                                max(first_rect.x1, last_rect.x1),
                                max(first_rect.y1, last_rect.y1)
                            )
                            locations.append(combined_rect)

                if locations:
                    return locations, f"word-boundary: '{words[0]}' ... '{words[-1]}'"

    return locations, "not-found"

# Check each entity
found_culprit = False

for i, entity in enumerate(entities, 1):
    entity_text = entity['text']
    entity_type = entity['entity_type']

    locations, strategy = find_entity_locations(entity_text)

    if locations:
        for loc_idx, rect in enumerate(locations):
            # Check if this rectangle matches our target
            rect_match = (
                abs(rect.x0 - target_rect.x0) < 5 and
                abs(rect.x1 - target_rect.x1) < 5 and
                abs(rect.y0 - target_rect.y0) < 5 and
                abs(rect.y1 - target_rect.y1) < 5
            )

            # Check if overlaps REPUBBLICA
            overlaps_repubblica = rect.intersects(repubblica_rect)

            status = ""
            if rect_match:
                status = " <<< TARGET RECTANGLE FOUND!"
                found_culprit = True
            elif overlaps_repubblica:
                overlap = rect & repubblica_rect
                coverage = (overlap.width * overlap.height) / (repubblica_rect.width * repubblica_rect.height) * 100
                status = f" [OVERLAPS REPUBBLICA {coverage:.0f}%]"

            print(f"{i}. {entity_type}: '{entity_text}'")
            print(f"   Strategy: {strategy}")
            print(f"   Location {loc_idx}: x={rect.x0:.1f}-{rect.x1:.1f}, y={rect.y0:.1f}-{rect.y1:.1f}{status}")

            if rect_match or overlaps_repubblica:
                # Show what text is actually at this position
                actual_text = page.get_textbox(rect)
                print(f"   Actual text at position: '{actual_text.strip()[:60]}'")

            if status:
                print()

if not found_culprit:
    print()
    print("="*60)
    print("CULPRIT NOT FOUND IN 13 ENTITIES!")
    print("="*60)
    print()
    print("Possible causes:")
    print("1. Additional entities were added beyond the 13 in mapping table")
    print("2. Coordinate transformation error in redaction code")
    print("3. Rectangle was drawn manually/outside entity loop")
    print()
    print("Next: Check if there are more than 13 entities in actual redaction data")

doc.close()
