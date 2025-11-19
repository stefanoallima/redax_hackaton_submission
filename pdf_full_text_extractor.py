#!/usr/bin/env python3
"""
Extract all text and PII from entire PDF
"""
import sys
import re
from pathlib import Path
from pypdf import PdfReader

def extract_all_text(filepath):
    """Extract complete text from all pages"""
    print(f"\n{'='*80}")
    print("COMPLETE TEXT EXTRACTION")
    print(f"{'='*80}\n")

    reader = PdfReader(filepath)
    print(f"Total pages: {len(reader.pages)}\n")

    all_text = []
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        all_text.append(text)
        print(f"Page {page_num + 1}: {len(text)} chars")

    # Combine all text
    full_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text)

    # Save to file
    output_file = Path(filepath).stem + "_extracted_text.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"\n[+] Saved full text to: {output_file}")
    print(f"[+] Total text: {len(full_text)} characters\n")

    # PII Detection patterns
    print(f"\n{'='*80}")
    print("PII PATTERN DETECTION")
    print(f"{'='*80}\n")

    # Email addresses
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', full_text)
    if emails:
        print(f"EMAILS ({len(emails)}):")
        for email in set(emails):
            print(f"  - {email}")

    # Italian Codice Fiscale (16 chars)
    cf_pattern = r'\b[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]\b'
    codici_fiscali = re.findall(cf_pattern, full_text)
    if codici_fiscali:
        print(f"\nCODICE FISCALE ({len(codici_fiscali)}):")
        for cf in set(codici_fiscali):
            print(f"  - {cf}")

    # IBAN
    iban_pattern = r'\bIT[0-9]{2}[A-Z0-9]{23,27}\b'
    ibans = re.findall(iban_pattern, full_text)
    if ibans:
        print(f"\nIBAN ({len(ibans)}):")
        for iban in set(ibans):
            print(f"  - {iban}")

    # Phone numbers (Italian)
    phone_pattern = r'\b(?:\+39|0039)?[\s]?[0-9]{2,4}[\s]?[0-9]{6,8}\b'
    phones = re.findall(phone_pattern, full_text)
    if phones:
        print(f"\nPHONE NUMBERS ({len(phones)}):")
        for phone in set(phones):
            print(f"  - {phone}")

    # Addresses (via/piazza/corso + street name)
    address_pattern = r'(?:via|Via|piazza|Piazza|corso|Corso)\s+[A-Za-z\s]+(?:\d+|n\.\s*\d+)'
    addresses = re.findall(address_pattern, full_text)
    if addresses:
        print(f"\nADDRESSES ({len(addresses)}):")
        for addr in set(addresses):
            print(f"  - {addr}")

    # Full names (capital initials, 2-4 words)
    name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b'
    names = re.findall(name_pattern, full_text)
    # Filter common words
    common_words = {'Repubblica', 'Italiana', 'Nome', 'Del', 'Popolo', 'Italiano',
                    'Corte', 'Suprema', 'Cassazione', 'Sezioni', 'Unite', 'Civili',
                    'Roma', 'Appello', 'Pubblico', 'Ministero', 'Sostituto',
                    'Procuratore', 'Consigliere', 'Presidente', 'Sezione'}
    filtered_names = [n for n in names if n not in common_words and len(n) > 5]
    if filtered_names:
        print(f"\nPOTENTIAL NAMES ({len(set(filtered_names))}):")
        for name in sorted(set(filtered_names))[:50]:  # Top 50
            count = full_text.count(name)
            print(f"  - {name} (appears {count}x)")

    # Date of birth patterns
    dob_pattern = r'\b(?:nat[oa] il|born on|d\.?n\.?)\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b'
    dobs = re.findall(dob_pattern, full_text, re.IGNORECASE)
    if dobs:
        print(f"\nDATES OF BIRTH ({len(dobs)}):")
        for dob in set(dobs):
            print(f"  - {dob}")

    # Medical terms
    medical_terms = ['infarto', 'diabete', 'tumore', 'cancro', 'malattia', 'patologia',
                     'disabilità', 'handicap', 'terapia', 'ospedale', 'ricovero']
    found_medical = []
    for term in medical_terms:
        if re.search(r'\b' + term + r'\b', full_text, re.IGNORECASE):
            count = len(re.findall(r'\b' + term + r'\b', full_text, re.IGNORECASE))
            found_medical.append((term, count))

    if found_medical:
        print(f"\nMEDICAL TERMS:")
        for term, count in found_medical:
            print(f"  - {term} (appears {count}x)")

    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    filepath = r"C:\Users\tucan\Documents\stefano\hackaton\huggingface_gradio\codicecivileai\desktop\test_documents\sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex.pdf"
    extract_all_text(filepath)
