#!/usr/bin/env python3
"""
Deep scan for ALL possible hidden metadata and text
"""
import sys
import re
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import IndirectObject, ArrayObject, DictionaryObject
import struct

def deep_scan(filepath):
    """Exhaustive search for hidden data"""
    print(f"\n{'='*80}")
    print("DEEP METADATA & HIDDEN TEXT SCAN")
    print(f"{'='*80}\n")

    reader = PdfReader(filepath)

    # 1. XMP METADATA
    print(f"\n{'='*80}")
    print("1. XMP METADATA (Extended)")
    print(f"{'='*80}")
    try:
        if "/Metadata" in reader.trailer["/Root"]:
            metadata_ref = reader.trailer["/Root"]["/Metadata"]
            if isinstance(metadata_ref, IndirectObject):
                metadata_obj = reader.get_object(metadata_ref)
                xmp_data = metadata_obj.get_data()
                xmp_text = xmp_data.decode('utf-8', errors='ignore')

                print(f"XMP Metadata found ({len(xmp_text)} chars):")
                print("-" * 80)

                # Extract key fields
                author_match = re.search(r'<dc:creator>.*?<rdf:li>(.*?)</rdf:li>', xmp_text, re.DOTALL)
                if author_match:
                    print(f"Author: {author_match.group(1)}")

                title_match = re.search(r'<dc:title>.*?<rdf:li.*?>(.*?)</rdf:li>', xmp_text, re.DOTALL)
                if title_match:
                    print(f"Title: {title_match.group(1)}")

                # Show full XMP (first 2000 chars)
                print(f"\nFull XMP preview:")
                print(xmp_text[:2000])
                if len(xmp_text) > 2000:
                    print(f"\n... ({len(xmp_text) - 2000} more chars)")
        else:
            print("No XMP metadata found")
    except Exception as e:
        print(f"No XMP metadata: {e}")

    # 2. DOCUMENT INFO EXTENDED
    print(f"\n{'='*80}")
    print("2. DOCUMENT INFO (All Fields)")
    print(f"{'='*80}")
    if reader.metadata:
        for key, value in reader.metadata.items():
            print(f"{key}: {value}")

    # Check trailer info
    if "/Info" in reader.trailer:
        info = reader.trailer["/Info"]
        if isinstance(info, IndirectObject):
            info = reader.get_object(info)
        print("\nRaw Info Dictionary:")
        if hasattr(info, 'items'):
            for k, v in info.items():
                print(f"  {k}: {v}")

    # 3. ANNOTATIONS & COMMENTS
    print(f"\n{'='*80}")
    print("3. ANNOTATIONS & COMMENTS (All Pages)")
    print(f"{'='*80}")
    total_annots = 0
    for page_num, page in enumerate(reader.pages):
        if "/Annots" in page:
            annots = page["/Annots"]
            if annots:
                print(f"\nPage {page_num + 1}: {len(annots)} annotation(s)")
                total_annots += len(annots)

                for i, annot_ref in enumerate(annots):
                    if isinstance(annot_ref, IndirectObject):
                        annot = reader.get_object(annot_ref)
                    else:
                        annot = annot_ref

                    print(f"  Annotation {i+1}:")
                    print(f"    Type: {annot.get('/Subtype', 'Unknown')}")

                    if '/Contents' in annot:
                        print(f"    Contents: {annot['/Contents']}")

                    if '/T' in annot:  # Title/Author
                        print(f"    Author: {annot['/T']}")

                    if '/Subj' in annot:  # Subject
                        print(f"    Subject: {annot['/Subj']}")

                    if '/RC' in annot:  # Rich text
                        print(f"    Rich Text: {annot['/RC']}")

    if total_annots == 0:
        print("No annotations found")

    # 4. BOOKMARKS/OUTLINE
    print(f"\n{'='*80}")
    print("4. BOOKMARKS/OUTLINE")
    print(f"{'='*80}")
    try:
        if "/Outlines" in reader.trailer["/Root"]:
            outlines = reader.trailer["/Root"]["/Outlines"]
            if isinstance(outlines, IndirectObject):
                outlines = reader.get_object(outlines)
            print(f"Outlines found: {outlines}")

            # Traverse outline tree
            if "/First" in outlines:
                print("Bookmark structure exists")
        else:
            print("No bookmarks/outline")
    except Exception as e:
        print(f"No outline: {e}")

    # 5. INCREMENTAL UPDATES / REVISIONS
    print(f"\n{'='*80}")
    print("5. PDF REVISIONS (Incremental Updates)")
    print(f"{'='*80}")
    try:
        # Check for multiple xref tables (indicates revisions)
        with open(filepath, 'rb') as f:
            content = f.read()

            # Count PDF headers (each revision adds one)
            pdf_headers = content.count(b'%PDF-')
            print(f"PDF headers found: {pdf_headers}")

            # Count xref entries
            xref_count = content.count(b'xref')
            print(f"Xref tables: {xref_count}")

            if xref_count > 1:
                print(f"[!] MULTIPLE REVISIONS DETECTED - may contain previous versions!")

            # Check for startxref
            startxref_positions = [m.start() for m in re.finditer(b'startxref', content)]
            print(f"Startxref entries: {len(startxref_positions)}")

    except Exception as e:
        print(f"Could not analyze revisions: {e}")

    # 6. HIDDEN OBJECTS
    print(f"\n{'='*80}")
    print("6. UNREFERENCED OBJECTS (Orphaned)")
    print(f"{'='*80}")
    try:
        # Get all object numbers
        all_objects = set()
        for key in reader.xref:
            all_objects.add(key)

        print(f"Total objects in PDF: {len(all_objects)}")

        # Try to find unreferenced objects
        # This is complex - would need to traverse entire object tree
        print("Note: Full orphan detection requires deep tree traversal")

    except Exception as e:
        print(f"Could not analyze objects: {e}")

    # 7. FONT METADATA
    print(f"\n{'='*80}")
    print("7. FONT INFORMATION")
    print(f"{'='*80}")
    unique_fonts = set()
    for page_num, page in enumerate(reader.pages):
        if "/Resources" in page:
            resources = page["/Resources"]
            if isinstance(resources, IndirectObject):
                resources = reader.get_object(resources)

            if "/Font" in resources:
                fonts = resources["/Font"]
                if isinstance(fonts, IndirectObject):
                    fonts = reader.get_object(fonts)

                for font_name, font_ref in fonts.items():
                    if isinstance(font_ref, IndirectObject):
                        font_obj = reader.get_object(font_ref)
                    else:
                        font_obj = font_ref

                    font_info = f"{font_name}"
                    if "/BaseFont" in font_obj:
                        font_info += f" - {font_obj['/BaseFont']}"
                    if "/Subtype" in font_obj:
                        font_info += f" ({font_obj['/Subtype']})"

                    unique_fonts.add(font_info)

    if unique_fonts:
        print(f"Unique fonts ({len(unique_fonts)}):")
        for font in sorted(unique_fonts):
            print(f"  - {font}")

    # 8. IMAGE METADATA (EXIF)
    print(f"\n{'='*80}")
    print("8. IMAGE METADATA")
    print(f"{'='*80}")
    image_count = 0
    for page_num, page in enumerate(reader.pages):
        if "/Resources" in page:
            resources = page["/Resources"]
            if isinstance(resources, IndirectObject):
                resources = reader.get_object(resources)

            if "/XObject" in resources:
                xobjects = resources["/XObject"]
                if isinstance(xobjects, IndirectObject):
                    xobjects = reader.get_object(xobjects)

                for xobj_name, xobj_ref in xobjects.items():
                    if isinstance(xobj_ref, IndirectObject):
                        xobj = reader.get_object(xobj_ref)
                    else:
                        xobj = xobj_ref

                    if "/Subtype" in xobj and xobj["/Subtype"] == "/Image":
                        image_count += 1
                        print(f"\nImage {image_count} ({xobj_name}):")
                        print(f"  Size: {xobj.get('/Width', '?')}x{xobj.get('/Height', '?')}")
                        print(f"  ColorSpace: {xobj.get('/ColorSpace', 'Unknown')}")
                        print(f"  BitsPerComponent: {xobj.get('/BitsPerComponent', '?')}")
                        print(f"  Filter: {xobj.get('/Filter', 'None')}")

                        # Check for embedded EXIF
                        if "/Metadata" in xobj:
                            print(f"  [!] Has embedded metadata stream")

    # 9. CUSTOM METADATA FIELDS
    print(f"\n{'='*80}")
    print("9. CUSTOM METADATA FIELDS")
    print(f"{'='*80}")
    catalog = reader.trailer["/Root"]
    if isinstance(catalog, IndirectObject):
        catalog = reader.get_object(catalog)

    custom_fields = []
    standard_keys = {'/Type', '/Pages', '/Metadata', '/StructTreeRoot', '/MarkInfo',
                     '/Lang', '/AcroForm', '/Outlines', '/Names', '/OpenAction',
                     '/PageMode', '/ViewerPreferences', '/PageLayout'}

    for key in catalog.keys():
        if key not in standard_keys:
            custom_fields.append((key, catalog[key]))

    if custom_fields:
        print("Custom catalog entries:")
        for key, value in custom_fields:
            print(f"  {key}: {value}")
    else:
        print("No custom metadata fields")

    # 10. PRODUCER/TOOL HISTORY
    print(f"\n{'='*80}")
    print("10. PRODUCTION TOOL CHAIN")
    print(f"{'='*80}")
    producer = reader.metadata.get('/Producer', 'Unknown')
    creator = reader.metadata.get('/Creator', 'Unknown')

    print(f"Original Creator: {creator}")
    print(f"Producer: {producer}")

    # Parse iText modification
    if 'iText' in producer:
        print(f"\n[!] PDF MODIFIED WITH iText")
        print(f"    This is a PDF manipulation library")
        print(f"    Often used for: annotations, redactions, form filling")

        # Extract version
        itext_version = re.search(r'iText[^\d]*([\d.]+)', producer)
        if itext_version:
            print(f"    Version: {itext_version.group(1)}")

    print(f"\n{'='*80}")
    print("SCAN COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    filepath = r"C:\Users\tucan\Documents\stefano\hackaton\huggingface_gradio\codicecivileai\desktop\test_documents\sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex.pdf"
    deep_scan(filepath)
