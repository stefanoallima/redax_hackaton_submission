#!/usr/bin/env python3
"""
PDF Forensic Analyzer - Extract all metadata, layers, and hidden data
"""
import sys
import json
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import IndirectObject
import re

def analyze_pdf(filepath):
    """Comprehensive PDF analysis"""
    print(f"\n{'='*80}")
    print(f"PDF FORENSIC ANALYSIS")
    print(f"{'='*80}")
    print(f"File: {Path(filepath).name}")
    print(f"Size: {Path(filepath).stat().st_size / 1024:.1f} KB\n")

    try:
        reader = PdfReader(filepath)

        # ===== DOCUMENT METADATA =====
        print(f"\n{'='*80}")
        print("DOCUMENT METADATA")
        print(f"{'='*80}")
        if reader.metadata:
            for key, value in reader.metadata.items():
                print(f"{key}: {value}")
        else:
            print("No metadata found")

        # ===== DOCUMENT INFO =====
        print(f"\n{'='*80}")
        print("DOCUMENT INFO")
        print(f"{'='*80}")
        print(f"Pages: {len(reader.pages)}")
        print(f"Encrypted: {reader.is_encrypted}")
        if hasattr(reader, 'pdf_header'):
            print(f"PDF Version: {reader.pdf_header}")

        # ===== LAYERS (Optional Content Groups) =====
        print(f"\n{'='*80}")
        print("LAYERS / OPTIONAL CONTENT GROUPS (OCGs)")
        print(f"{'='*80}")
        try:
            catalog = reader.trailer["/Root"]
            if "/OCProperties" in catalog:
                oc_props = catalog["/OCProperties"]
                if "/OCGs" in oc_props:
                    ocgs = oc_props["/OCGs"]
                    print(f"Found {len(ocgs)} layer(s):")
                    for i, ocg in enumerate(ocgs):
                        if isinstance(ocg, IndirectObject):
                            ocg = reader.get_object(ocg)
                        if "/Name" in ocg:
                            print(f"  Layer {i+1}: {ocg['/Name']}")
                        print(f"    Full data: {dict(ocg)}")
                else:
                    print("No OCGs found")

                if "/D" in oc_props:
                    print("\nDefault Configuration:")
                    default_config = oc_props["/D"]
                    if isinstance(default_config, IndirectObject):
                        default_config = reader.get_object(default_config)
                    print(f"  {dict(default_config)}")
            else:
                print("No layers/OCGs found in document")
        except Exception as e:
            print(f"Could not extract layers: {e}")

        # ===== PAGE-BY-PAGE ANALYSIS =====
        print(f"\n{'='*80}")
        print("PAGE-BY-PAGE ANALYSIS")
        print(f"{'='*80}")
        for page_num, page in enumerate(reader.pages):
            print(f"\n--- Page {page_num + 1} ---")

            # Page dimensions
            box = page.mediabox
            print(f"Dimensions: {float(box.width):.1f} x {float(box.height):.1f} pts")

            # Annotations (comments, highlights, redactions)
            if "/Annots" in page:
                annots = page["/Annots"]
                print(f"Annotations: {len(annots)}")
                for i, annot in enumerate(annots):
                    if isinstance(annot, IndirectObject):
                        annot_obj = reader.get_object(annot)
                        print(f"  Annotation {i+1}:")
                        print(f"    Type: {annot_obj.get('/Subtype', 'Unknown')}")
                        print(f"    Contents: {annot_obj.get('/Contents', 'N/A')}")
                        if '/AP' in annot_obj:
                            print(f"    Has appearance stream: Yes")
                        if '/Rect' in annot_obj:
                            print(f"    Position: {annot_obj['/Rect']}")

            # Resources (fonts, images, etc.)
            if "/Resources" in page:
                resources = page["/Resources"]
                if isinstance(resources, IndirectObject):
                    resources = reader.get_object(resources)

                if "/Font" in resources:
                    fonts = resources["/Font"]
                    print(f"Fonts: {len(fonts)}")
                    for font_name in fonts:
                        print(f"  - {font_name}")

                if "/XObject" in resources:
                    xobjects = resources["/XObject"]
                    print(f"XObjects (Images/Forms): {len(xobjects)}")
                    for xobj_name in xobjects:
                        xobj = xobjects[xobj_name]
                        if isinstance(xobj, IndirectObject):
                            xobj = reader.get_object(xobj)
                        if "/Subtype" in xobj:
                            print(f"  - {xobj_name}: {xobj['/Subtype']}")

                # Check for Properties (OCG references)
                if "/Properties" in resources:
                    props = resources["/Properties"]
                    print(f"Properties (Layer refs): {len(props)}")
                    for prop_name in props:
                        print(f"  - {prop_name}")

            # Check for hidden content
            if "/Contents" in page:
                contents = page["/Contents"]
                try:
                    # Get content stream
                    content_text = page.extract_text()
                    print(f"Extracted text length: {len(content_text)} chars")
                except Exception as e:
                    print(f"Could not extract text: {e}")

        # ===== EMBEDDED FILES =====
        print(f"\n{'='*80}")
        print("EMBEDDED FILES")
        print(f"{'='*80}")
        try:
            if "/Names" in reader.trailer["/Root"]:
                names = reader.trailer["/Root"]["/Names"]
                if isinstance(names, IndirectObject):
                    names = reader.get_object(names)
                if "/EmbeddedFiles" in names:
                    print("Found embedded files!")
                    embedded = names["/EmbeddedFiles"]
                    print(f"  {embedded}")
                else:
                    print("No embedded files")
            else:
                print("No embedded files")
        except Exception as e:
            print(f"No embedded files: {e}")

        # ===== JAVASCRIPT =====
        print(f"\n{'='*80}")
        print("JAVASCRIPT")
        print(f"{'='*80}")
        try:
            if "/Names" in reader.trailer["/Root"]:
                names = reader.trailer["/Root"]["/Names"]
                if isinstance(names, IndirectObject):
                    names = reader.get_object(names)
                if "/JavaScript" in names:
                    print("WARNING: JavaScript found in PDF!")
                    js_data = names["/JavaScript"]
                    print(f"  {js_data}")
                else:
                    print("No JavaScript")
            else:
                print("No JavaScript")
        except Exception as e:
            print(f"No JavaScript: {e}")

        # ===== FORM FIELDS =====
        print(f"\n{'='*80}")
        print("FORM FIELDS")
        print(f"{'='*80}")
        try:
            if "/AcroForm" in reader.trailer["/Root"]:
                acroform = reader.trailer["/Root"]["/AcroForm"]
                if isinstance(acroform, IndirectObject):
                    acroform = reader.get_object(acroform)
                print(f"Form data: {dict(acroform)}")
                if "/Fields" in acroform:
                    fields = acroform["/Fields"]
                    print(f"Found {len(fields)} form field(s)")
                    for i, field in enumerate(fields):
                        if isinstance(field, IndirectObject):
                            field_obj = reader.get_object(field)
                            print(f"  Field {i+1}: {field_obj.get('/T', 'unnamed')}")
                            print(f"    Value: {field_obj.get('/V', 'N/A')}")
            else:
                print("No form fields")
        except Exception as e:
            print(f"No form fields: {e}")

        # ===== DOCUMENT STRUCTURE =====
        print(f"\n{'='*80}")
        print("DOCUMENT STRUCTURE TREE")
        print(f"{'='*80}")
        try:
            if "/StructTreeRoot" in reader.trailer["/Root"]:
                print("Document has structure tree (tagged PDF)")
                struct_root = reader.trailer["/Root"]["/StructTreeRoot"]
                if isinstance(struct_root, IndirectObject):
                    struct_root = reader.get_object(struct_root)
                print(f"  Root type: {struct_root.get('/Type', 'N/A')}")
            else:
                print("No structure tree (not a tagged PDF)")
        except Exception as e:
            print(f"Could not analyze structure: {e}")

        # ===== TRAILER INFO =====
        print(f"\n{'='*80}")
        print("TRAILER / CATALOG INFO")
        print(f"{'='*80}")
        print(f"Trailer keys: {list(reader.trailer.keys())}")
        if "/Root" in reader.trailer:
            root = reader.trailer["/Root"]
            if isinstance(root, IndirectObject):
                root = reader.get_object(root)
            print(f"Catalog keys: {list(root.keys())}")

        print(f"\n{'='*80}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = r"C:\Users\tucan\Documents\stefano\hackaton\huggingface_gradio\codicecivileai\desktop\test_documents\sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf"

    analyze_pdf(filepath)
