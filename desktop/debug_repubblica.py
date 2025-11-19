"""
Debug script to find which entity location is matching REPUBBLICA ITALIANA
"""
import fitz
import re
import csv

# The 13 entities that were redacted (from mapping table)
entities = [
    "Pasquale D'Anconn",
    "P.Q.M.\nAccoglie",
    "att. c.p.c.",
    "FLAVIO TRONBONE",
    "O.\nUdito",
    "avv.marcovannini@pec.com",
    "Marco Vannini",
    "Iban",
    "danielagambardella@ordineavvocatiroma.org",
    "DANIELA GAMBARDELLA",
    "Giovanni Francesco Biasiotti Mogliazza",
    "Magistrati",
    "Ill.mi"
]

# REPUBBLICA ITALIANA known position
repubblica_rect = fitz.Rect(212, 121, 383, 137)
print("REPUBBLICA ITALIANA position: x=212-383, y=121-137")
print()

# Open PDF
doc = fitz.open('test_documents/sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf')
page = doc[0]

print("=== Testing which entity search finds REPUBBLICA area ===")
print()

overlaps_found = []

for entity_text in entities:
    print(f"Testing: '{entity_text}'")

    # Strategy 1: Exact match
    text_instances = page.search_for(entity_text)

    # Strategy 2: Normalized (remove whitespace)
    if not text_instances:
        normalized_text = re.sub(r'\s+', ' ', entity_text).strip()
        if normalized_text != entity_text:
            text_instances = page.search_for(normalized_text)
            if text_instances:
                print(f"  [MATCH via normalized: '{normalized_text}']")

    # Strategy 3: Case variations
    if not text_instances:
        for variant in [entity_text.lower(), entity_text.upper(), entity_text.title()]:
            text_instances = page.search_for(variant)
            if text_instances:
                print(f"  [MATCH via case variant: '{variant}']")
                break

    # Strategy 4: Word boundary multi-word matching
    if not text_instances and ' ' in entity_text.replace('\n', ' '):
        normalized = re.sub(r'\s+', ' ', entity_text).strip()
        words = normalized.split()
        if len(words) >= 2:
            first_word_instances = page.search_for(words[0])
            last_word_instances = page.search_for(words[-1])

            if first_word_instances and last_word_instances:
                for first_rect in first_word_instances:
                    for last_rect in last_word_instances:
                        # Same line check (y-coordinate within 5 points)
                        if abs(first_rect.y0 - last_rect.y0) < 5:
                            # Combine rectangles
                            combined_rect = fitz.Rect(
                                min(first_rect.x0, last_rect.x0),
                                min(first_rect.y0, last_rect.y0),
                                max(first_rect.x1, last_rect.x1),
                                max(first_rect.y1, last_rect.y1)
                            )
                            text_instances = [combined_rect]
                            print(f"  [MATCH via word boundary: '{words[0]}' ... '{words[-1]}']")
                            break

    # Check for overlaps with REPUBBLICA
    if text_instances:
        print(f"  Found {len(text_instances)} location(s)")
        for i, rect in enumerate(text_instances):
            print(f"    Location {i}: x={rect.x0:.1f}-{rect.x1:.1f}, y={rect.y0:.1f}-{rect.y1:.1f}")

            # Check overlap with REPUBBLICA
            if rect.intersects(repubblica_rect):
                overlap = rect & repubblica_rect
                overlap_area = overlap.width * overlap.height
                repubblica_area = repubblica_rect.width * repubblica_rect.height
                coverage = (overlap_area / repubblica_area) * 100

                print(f"    *** OVERLAPS REPUBBLICA! Coverage: {coverage:.1f}% ***")
                overlaps_found.append({
                    'entity': entity_text,
                    'rect': rect,
                    'coverage': coverage
                })
    else:
        print("  [NO MATCH]")

    print()

print()
print("="*60)
print("SUMMARY")
print("="*60)
if overlaps_found:
    print(f"Found {len(overlaps_found)} entity location(s) that overlap REPUBBLICA:")
    for item in overlaps_found:
        print(f"  - '{item['entity']}'")
        print(f"    Position: x={item['rect'].x0:.1f}-{item['rect'].x1:.1f}, y={item['rect'].y0:.1f}-{item['rect'].y1:.1f}")
        print(f"    Coverage: {item['coverage']:.1f}%")
else:
    print("NO entities found that overlap REPUBBLICA ITALIANA")
    print("This suggests the redaction came from a different source!")

doc.close()
