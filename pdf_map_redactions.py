#!/usr/bin/env python3
"""
Map what text is covered by white box coordinates
"""
import sys
import re
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import IndirectObject

def map_redaction_boxes(filepath):
    """Identify text covered by white boxes based on coordinates"""
    print(f"\n{'='*80}")
    print("REDACTION BOX MAPPING")
    print(f"{'='*80}\n")

    reader = PdfReader(filepath)

    # Focus on first 5 pages where redactions are
    for page_num in range(min(5, len(reader.pages))):
        page = reader.pages[page_num]

        print(f"\n{'='*80}")
        print(f"PAGE {page_num + 1}")
        print(f"{'='*80}\n")

        # First, get all white box redaction coordinates
        redaction_boxes = []

        if "/Resources" in page:
            resources = page["/Resources"]
            if isinstance(resources, IndirectObject):
                resources = reader.get_object(resources)

            if "/XObject" in resources:
                xobjects = resources["/XObject"]
                if isinstance(xobjects, IndirectObject):
                    xobjects = reader.get_object(xobjects)

                for xobj_name, xobj in xobjects.items():
                    if isinstance(xobj, IndirectObject):
                        xobj = reader.get_object(xobj)

                    # Check if it's a Form XObject with white fill
                    if "/Subtype" in xobj and xobj["/Subtype"] == "/Form":
                        try:
                            stream_data = xobj.get_data()
                            decoded = stream_data.decode('latin-1', errors='ignore')

                            # Check if it's a white rectangle
                            if '1 1 1 rg' in decoded and ' f\n' in decoded:
                                bbox = xobj.get('/BBox', None)
                                if bbox:
                                    redaction_boxes.append({
                                        'name': xobj_name,
                                        'bbox': bbox,
                                        'x': float(bbox[0]),
                                        'y': float(bbox[1]),
                                        'width': float(bbox[2]) - float(bbox[0]),
                                        'height': float(bbox[3]) - float(bbox[1])
                                    })
                        except Exception as e:
                            pass

        if redaction_boxes:
            print(f"Found {len(redaction_boxes)} WHITE BOX REDACTIONS:\n")
            for box in redaction_boxes:
                print(f"  {box['name']}: Area = {box['width']:.1f}x{box['height']:.1f} pts")
                print(f"    Position: x={box['x']:.1f}, y={box['y']:.1f}")
                print(f"    BBox: {box['bbox']}")
                print()

        # Now extract ALL text with positioning info from content stream
        print("ANALYZING CONTENT STREAM FOR TEXT UNDER REDACTIONS:\n")

        if "/Contents" in page:
            contents = page["/Contents"]

            if isinstance(contents, list):
                stream_objects = contents
            else:
                stream_objects = [contents]

            for stream_obj in stream_objects:
                if isinstance(stream_obj, IndirectObject):
                    stream_obj = reader.get_object(stream_obj)

                try:
                    stream_data = stream_obj.get_data()
                    decoded = stream_data.decode('latin-1', errors='ignore')

                    # Look for text positioning commands followed by text
                    # Td, TD, Tm set text position
                    # Then Tj or TJ show text

                    # Split into BT...ET blocks
                    bt_et_blocks = re.findall(r'BT\s+(.*?)\s+ET', decoded, re.DOTALL)

                    for block_idx, block in enumerate(bt_et_blocks):
                        # Look for positioning + text
                        lines = block.split('\n')

                        current_y = None
                        current_x = None

                        for line in lines:
                            line = line.strip()

                            # Text matrix: a b c d e f Tm
                            tm_match = re.match(r'([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)\s+Tm', line)
                            if tm_match:
                                current_x = float(tm_match.group(5))
                                current_y = float(tm_match.group(6))

                            # Text move: x y Td
                            td_match = re.match(r'([\d.-]+)\s+([\d.-]+)\s+Td', line)
                            if td_match:
                                if current_x is not None:
                                    current_x += float(td_match.group(1))
                                    current_y += float(td_match.group(2))

                            # Text show: (text) Tj
                            tj_match = re.search(r'\(([^)]*)\)\s*Tj', line)
                            if tj_match and current_x is not None and current_y is not None:
                                text = tj_match.group(1)

                                # Check if this text position overlaps with any redaction box
                                for box in redaction_boxes:
                                    # Check if point is within redaction box
                                    if (box['x'] <= current_x <= box['x'] + box['width'] and
                                        box['y'] <= current_y <= box['y'] + box['height']):

                                        print(f"[!] HIDDEN TEXT under {box['name']}:")
                                        print(f"    Position: ({current_x:.1f}, {current_y:.1f})")
                                        print(f"    Text: \"{text}\"")
                                        print()

                except Exception as e:
                    print(f"Error: {e}")

        # Also print visible text for comparison
        print(f"\n{'='*60}")
        print("VISIBLE TEXT (for reference):")
        print(f"{'='*60}")
        try:
            visible_text = page.extract_text()
            print(visible_text[:500])
            if len(visible_text) > 500:
                print(f"\n... ({len(visible_text) - 500} more chars)")
        except Exception as e:
            print(f"Could not extract: {e}")

if __name__ == "__main__":
    filepath = r"C:\Users\tucan\Documents\stefano\hackaton\huggingface_gradio\codicecivileai\desktop\test_documents\sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex.pdf"
    map_redaction_boxes(filepath)
