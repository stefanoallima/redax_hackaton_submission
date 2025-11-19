#!/usr/bin/env python3
"""
Deep layer extraction - inspect Properties and XObjects
"""
import sys
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import IndirectObject

def extract_layers(filepath):
    """Extract hidden layer data from Properties"""
    print(f"\n{'='*80}")
    print("DEEP LAYER ANALYSIS")
    print(f"{'='*80}\n")

    reader = PdfReader(filepath)

    for page_num, page in enumerate(reader.pages):
        print(f"\n{'='*80}")
        print(f"PAGE {page_num + 1} - DETAILED PROPERTIES")
        print(f"{'='*80}\n")

        if "/Resources" not in page:
            print("No resources")
            continue

        resources = page["/Resources"]
        if isinstance(resources, IndirectObject):
            resources = reader.get_object(resources)

        # Extract Properties (OCG references)
        if "/Properties" in resources:
            props = resources["/Properties"]
            if isinstance(props, IndirectObject):
                props = reader.get_object(props)

            print(f"Found {len(props)} Properties:\n")

            # Sample first 10 and last 10 properties
            prop_items = list(props.items())
            samples = prop_items[:10] + prop_items[-10:] if len(prop_items) > 20 else prop_items

            for prop_name, prop_obj in samples:
                print(f"\n--- Property: {prop_name} ---")
                if isinstance(prop_obj, IndirectObject):
                    prop_obj = reader.get_object(prop_obj)

                # Print full property object
                prop_dict = dict(prop_obj) if hasattr(prop_obj, 'items') else prop_obj
                for key, value in (prop_dict.items() if isinstance(prop_dict, dict) else [(None, prop_dict)]):
                    if key:
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {value}")

            if len(prop_items) > 20:
                print(f"\n... ({len(prop_items) - 20} properties omitted) ...\n")

        # Extract XObjects in detail
        if "/XObject" in resources:
            xobjects = resources["/XObject"]
            if isinstance(xobjects, IndirectObject):
                xobjects = reader.get_object(xobjects)

            print(f"\n{'='*60}")
            print(f"XObjects Detail:")
            print(f"{'='*60}\n")

            for xobj_name, xobj in xobjects.items():
                print(f"\n--- XObject: {xobj_name} ---")
                if isinstance(xobj, IndirectObject):
                    xobj = reader.get_object(xobj)

                # Print XObject properties
                if hasattr(xobj, 'items'):
                    for key, value in xobj.items():
                        if key in ['/Type', '/Subtype', '/Width', '/Height', '/BBox', '/Matrix',
                                   '/Filter', '/ColorSpace', '/BitsPerComponent', '/Length']:
                            print(f"  {key}: {value}")
                        elif key == '/Resources':
                            # Check if Form XObject has its own resources
                            print(f"  {key}: Has nested resources")
                            if isinstance(value, IndirectObject):
                                value = reader.get_object(value)
                            if isinstance(value, dict):
                                if '/XObject' in value:
                                    print(f"    - Contains nested XObjects")
                                if '/Properties' in value:
                                    nested_props = value['/Properties']
                                    if isinstance(nested_props, IndirectObject):
                                        nested_props = reader.get_object(nested_props)
                                    print(f"    - Contains {len(nested_props)} properties")
                        elif key == '/OC':
                            # Optional Content reference
                            print(f"  {key}: Layer reference found!")
                            if isinstance(value, IndirectObject):
                                oc_obj = reader.get_object(value)
                                print(f"    {dict(oc_obj)}")

if __name__ == "__main__":
    filepath = r"C:\Users\tucan\Documents\stefano\hackaton\huggingface_gradio\codicecivileai\desktop\test_documents\sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf"
    extract_layers(filepath)
