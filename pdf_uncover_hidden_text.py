#!/usr/bin/env python3
"""
Extract text hidden UNDER white box redactions
"""
import sys
import re
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import IndirectObject

def extract_hidden_text(filepath):
    """Extract content streams to find text covered by white boxes"""
    print(f"\n{'='*80}")
    print("HIDDEN TEXT EXTRACTION (Under White Boxes)")
    print(f"{'='*80}\n")

    reader = PdfReader(filepath)

    for page_num, page in enumerate(reader.pages):
        print(f"\n{'='*80}")
        print(f"PAGE {page_num + 1}")
        print(f"{'='*80}\n")

        # Get the raw content stream
        if "/Contents" in page:
            contents = page["/Contents"]

            # Contents can be a single stream or an array of streams
            if isinstance(contents, list):
                stream_objects = contents
            else:
                stream_objects = [contents]

            all_text_operations = []

            for stream_obj in stream_objects:
                if isinstance(stream_obj, IndirectObject):
                    stream_obj = reader.get_object(stream_obj)

                try:
                    # Get raw stream data
                    stream_data = stream_obj.get_data()
                    decoded = stream_data.decode('latin-1', errors='ignore')

                    # Extract all text operations
                    # BT...ET blocks contain text
                    bt_et_blocks = re.findall(r'BT\s+(.*?)\s+ET', decoded, re.DOTALL)

                    for block in bt_et_blocks:
                        all_text_operations.append(block)

                except Exception as e:
                    print(f"Error extracting stream: {e}")

            # Now parse all text operations to extract strings
            if all_text_operations:
                print("RAW TEXT OPERATIONS (including hidden text):\n")

                for i, block in enumerate(all_text_operations):
                    # Extract all text strings (both Tj and TJ)
                    # Tj: simple text show
                    tj_matches = re.findall(r'\(([^)]*)\)\s*Tj', block)

                    # TJ: array of text
                    tj_array_matches = re.findall(r'\[\s*([^\]]*)\s*\]\s*TJ', block)

                    text_fragments = []

                    for match in tj_matches:
                        if match.strip():
                            text_fragments.append(match)

                    for match in tj_array_matches:
                        strings = re.findall(r'\(([^)]*)\)', match)
                        text_fragments.extend([s for s in strings if s.strip()])

                    if text_fragments:
                        print(f"--- Text Block {i+1} ---")
                        reconstructed = ' '.join(text_fragments)
                        print(reconstructed)
                        print()

        # Check for XObject Forms that might have hidden content
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

                    # Check if it's a Form XObject
                    if "/Subtype" in xobj and xobj["/Subtype"] == "/Form":
                        # Check if it's a white fill (redaction box)
                        try:
                            stream_data = xobj.get_data()
                            decoded = stream_data.decode('latin-1', errors='ignore')

                            # Check if it's a white rectangle
                            if '1 1 1 rg' in decoded and ' f' in decoded:
                                # Get BBox to understand covered area
                                bbox = xobj.get('/BBox', None)
                                print(f"\n[!] WHITE BOX REDACTION FOUND: {xobj_name}")
                                if bbox:
                                    print(f"    Covers area: {bbox}")
                                print(f"    This is covering content underneath!\n")

                        except Exception as e:
                            pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = r"C:\Users\tucan\Documents\stefano\hackaton\huggingface_gradio\codicecivileai\desktop\test_documents\sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex.pdf"

    extract_hidden_text(filepath)
