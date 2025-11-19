#!/usr/bin/env python3
"""
Extract actual content from Form XObjects and stream data
"""
import sys
import zlib
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import IndirectObject

def extract_form_content(filepath):
    """Extract raw content streams from Form XObjects"""
    print(f"\n{'='*80}")
    print("FORM XOBJECT CONTENT EXTRACTION")
    print(f"{'='*80}\n")

    reader = PdfReader(filepath)

    for page_num, page in enumerate(reader.pages):
        print(f"\n{'='*80}")
        print(f"PAGE {page_num + 1}")
        print(f"{'='*80}\n")

        # First extract all visible text
        try:
            text = page.extract_text()
            print(f"VISIBLE TEXT ({len(text)} chars):")
            print("-" * 80)
            print(text)
            print("-" * 80)
        except Exception as e:
            print(f"Could not extract text: {e}")

        if "/Resources" not in page:
            continue

        resources = page["/Resources"]
        if isinstance(resources, IndirectObject):
            resources = reader.get_object(resources)

        # Extract Form XObjects
        if "/XObject" in resources:
            xobjects = resources["/XObject"]
            if isinstance(xobjects, IndirectObject):
                xobjects = reader.get_object(xobjects)

            for xobj_name, xobj in xobjects.items():
                if isinstance(xobj, IndirectObject):
                    xobj = reader.get_object(xobj)

                if "/Subtype" in xobj and xobj["/Subtype"] == "/Form":
                    print(f"\n{'='*60}")
                    print(f"FORM XOBJECT: {xobj_name}")
                    print(f"{'='*60}")

                    # Get the content stream
                    try:
                        if hasattr(xobj, 'get_data'):
                            stream_data = xobj.get_data()
                        elif hasattr(xobj, '_data'):
                            stream_data = xobj._data
                        else:
                            stream_data = None

                        if stream_data:
                            # Try to decode as text
                            try:
                                decoded = stream_data.decode('latin-1')
                                print(f"Content Stream ({len(decoded)} chars):")
                                print("-" * 60)
                                print(decoded[:2000])  # First 2000 chars
                                if len(decoded) > 2000:
                                    print(f"\n... (truncated, {len(decoded) - 2000} chars remaining)")
                                print("-" * 60)
                            except:
                                print(f"Binary content: {len(stream_data)} bytes")

                            # Look for text operators
                            text_content = []
                            decoded_str = stream_data.decode('latin-1', errors='ignore')

                            # Extract text between BT/ET (BeginText/EndText) operators
                            import re
                            bt_et_blocks = re.findall(r'BT\s+(.*?)\s+ET', decoded_str, re.DOTALL)

                            for block in bt_et_blocks:
                                # Look for Tj and TJ operators (show text)
                                tj_matches = re.findall(r'\(([^)]*)\)\s*Tj', block)
                                text_content.extend(tj_matches)

                                # TJ with arrays
                                tj_array_matches = re.findall(r'\[\s*([^\]]*)\s*\]\s*TJ', block)
                                for match in tj_array_matches:
                                    strings = re.findall(r'\(([^)]*)\)', match)
                                    text_content.extend(strings)

                            if text_content:
                                print(f"\nEXTRACTED TEXT FROM FORM:")
                                for i, txt in enumerate(text_content):
                                    print(f"  [{i+1}] {txt}")

                        else:
                            print("No stream data found")

                    except Exception as e:
                        print(f"Error extracting stream: {e}")
                        import traceback
                        traceback.print_exc()

                    # Check for nested resources
                    if "/Resources" in xobj:
                        nested_res = xobj["/Resources"]
                        if isinstance(nested_res, IndirectObject):
                            nested_res = reader.get_object(nested_res)

                        if "/XObject" in nested_res:
                            print("\n  [!] Has nested XObjects")
                        if "/Font" in nested_res:
                            fonts = nested_res["/Font"]
                            print(f"\n  Uses {len(fonts)} font(s): {list(fonts.keys())}")

if __name__ == "__main__":
    filepath = r"C:\Users\tucan\Documents\stefano\hackaton\huggingface_gradio\codicecivileai\desktop\test_documents\sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf"
    extract_form_content(filepath)
