#!/usr/bin/env python3
"""
Create test PDF from Italian legal text for E2E testing

This script converts the test_italian_legal_text.txt to a PDF file
that can be used for Playwright E2E tests.

Usage:
    python create_test_pdf.py

Requires:
    pip install reportlab
"""

import os
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import simpleSplit
except ImportError:
    print("ERROR: reportlab not installed")
    print("Install with: pip install reportlab")
    exit(1)


def create_test_pdf():
    """Create test PDF from Italian legal text"""

    # File paths
    script_dir = Path(__file__).parent
    text_file = script_dir / "test_italian_legal_text.txt"
    pdf_file = script_dir / "test_italian_legal_doc.pdf"

    # Check if text file exists
    if not text_file.exists():
        print(f"ERROR: Text file not found: {text_file}")
        exit(1)

    # Read text content
    with open(text_file, 'r', encoding='utf-8') as f:
        text_content = f.read()

    # Create PDF
    print(f"Creating PDF: {pdf_file}")
    c = canvas.Canvas(str(pdf_file), pagesize=A4)
    width, height = A4

    # Set up fonts (using default sans-serif)
    c.setFont("Helvetica", 10)

    # Page settings
    margin = 50
    line_height = 14
    max_width = width - 2 * margin
    y_position = height - margin

    # Split text into lines
    lines = text_content.split('\n')

    for line in lines:
        # Handle empty lines
        if not line.strip():
            y_position -= line_height
            if y_position < margin:
                c.showPage()
                c.setFont("Helvetica", 10)
                y_position = height - margin
            continue

        # Check if line needs special formatting (headers)
        if line.strip().isupper() and len(line.strip()) < 100:
            # Header
            c.setFont("Helvetica-Bold", 12)
            wrapped_lines = simpleSplit(line, "Helvetica-Bold", 12, max_width)
        elif line.strip().startswith('ARTICOLO'):
            # Article title
            c.setFont("Helvetica-Bold", 10)
            wrapped_lines = simpleSplit(line, "Helvetica-Bold", 10, max_width)
        else:
            # Regular text
            c.setFont("Helvetica", 10)
            wrapped_lines = simpleSplit(line, "Helvetica", 10, max_width)

        # Draw each wrapped line
        for wrapped_line in wrapped_lines:
            if y_position < margin:
                # Start new page
                c.showPage()
                c.setFont("Helvetica", 10)
                y_position = height - margin

            c.drawString(margin, y_position, wrapped_line)
            y_position -= line_height

    # Save PDF
    c.save()

    # Verify PDF created
    if pdf_file.exists():
        file_size = pdf_file.stat().st_size / 1024  # KB
        print(f"[OK] PDF created successfully: {pdf_file.name}")
        print(f"  File size: {file_size:.1f} KB")
        print(f"  Full path: {pdf_file.absolute()}")

        # Count PII entities in text (rough estimate)
        pii_count = (
            text_content.count('Codice Fiscale:') +
            text_content.count('CF:') +
            text_content.count('IBAN:') +
            text_content.count('Email:') +
            text_content.count('Telefono:') +
            text_content.count('Tel:') +
            text_content.count('Partita IVA:') +
            text_content.count('@')
        )
        print(f"  Estimated PII entities: ~{pii_count}")
        return True
    else:
        print("[ERROR] Failed to create PDF")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Test PDF Generator for GLiNER E2E Tests")
    print("=" * 60)
    print()

    success = create_test_pdf()

    if success:
        print()
        print("Next steps:")
        print("  1. Run E2E tests: npm run test:e2e")
        print("  2. Or specific test: npx playwright test gliner-detection.e2e.ts")
        exit(0)
    else:
        exit(1)
