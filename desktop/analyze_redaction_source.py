"""
Analyze where the REPUBBLICA redaction came from by reverse-engineering
the redacted PDF to find all black rectangles and what caused them
"""
import fitz

# Open redacted PDF
doc = fitz.open('test_documents/sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban_REDACTED.pdf')
page = doc[0]

print("=== ANALYZING REDACTED PDF ===")
print()

# REPUBBLICA ITALIANA known position in original
repubblica_rect = fitz.Rect(212, 121, 383, 137)
print(f"REPUBBLICA ITALIANA original position: x=212-383, y=121-137")
print()

# Method 1: Check for vector graphics (black rectangles drawn)
print("Method 1: Looking for black rectangle graphics...")
print()

# Get page content stream
try:
    cont = page.read_contents().decode('latin-1', errors='ignore')
except:
    cont = ""

# Look for rectangle drawing commands
import re
rect_pattern = r'(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+re'
matches = re.findall(rect_pattern, cont)

if matches:
    print(f"Found {len(matches)} rectangle draw commands")

    # Convert to coordinates and check for REPUBBLICA overlap
    for i, match in enumerate(matches):
        x = float(match[0])
        y = float(match[1])
        width = float(match[2])
        height = float(match[3])

        # PDF coordinates are bottom-left origin
        # Convert to top-left (PyMuPDF style)
        page_height = page.rect.height
        rect = fitz.Rect(x, page_height - y - height, x + width, page_height - y)

        if rect.intersects(repubblica_rect):
            overlap = rect & repubblica_rect
            coverage = (overlap.width * overlap.height) / (repubblica_rect.width * repubblica_rect.height) * 100
            print(f"  Rectangle {i}: x={rect.x0:.1f}-{rect.x1:.1f}, y={rect.y0:.1f}-{rect.y1:.1f}")
            print(f"    *** OVERLAPS REPUBBLICA! Coverage: {coverage:.1f}% ***")
else:
    print("No rectangle commands found (might be using different method)")

print()

# Method 2: Render page and analyze pixels
print("Method 2: Analyzing rendered page pixels...")
print()

# Render the REPUBBLICA area
mat = fitz.Matrix(3, 3)  # 3x zoom for better analysis
pix = page.get_pixmap(matrix=mat, clip=repubblica_rect)

# Count black pixels
black_pixels = 0
total_pixels = pix.width * pix.height

# Sample pixels (PyMuPDF pixmap format: RGB or RGBA)
for y in range(pix.height):
    for x in range(pix.width):
        # Get pixel color
        pixel_start = (y * pix.width + x) * pix.n
        pixel_data = pix.samples[pixel_start:pixel_start + pix.n]

        # Check if black (RGB close to 0)
        if len(pixel_data) >= 3:
            r, g, b = pixel_data[0], pixel_data[1], pixel_data[2]
            if r < 30 and g < 30 and b < 30:  # Near black
                black_pixels += 1

black_ratio = black_pixels / total_pixels
print(f"Black pixels in REPUBBLICA area: {black_pixels}/{total_pixels} ({black_ratio*100:.1f}%)")

# Check what text is actually visible
text_in_area = page.get_textbox(repubblica_rect)
print(f"Visible text in area: '{text_in_area.strip()}'")

print()

# Method 3: Search entire page for all black rectangles
print("Method 3: Finding all text that was redacted on page...")
print()

# Extract all text with position
blocks = page.get_text("dict")["blocks"]

redacted_text = []
visible_text = []

for block in blocks:
    if "lines" in block:
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue

                # Get bbox
                bbox = fitz.Rect(span["bbox"])

                # Check if this text area is mostly black (redacted)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=bbox)

                # Quick black pixel check
                total = pix.width * pix.height
                if total == 0:
                    continue

                black_count = 0
                for y in range(pix.height):
                    for x in range(pix.width):
                        pixel_start = (y * pix.width + x) * pix.n
                        pixel_data = pix.samples[pixel_start:pixel_start + pix.n]
                        if len(pixel_data) >= 3:
                            r, g, b = pixel_data[0], pixel_data[1], pixel_data[2]
                            if r < 30 and g < 30 and b < 30:
                                black_count += 1

                black_ratio = black_count / total

                if black_ratio > 0.5:  # More than 50% black = likely redacted
                    redacted_text.append({
                        'text': text,
                        'bbox': bbox,
                        'black_ratio': black_ratio
                    })
                else:
                    visible_text.append(text)

if redacted_text:
    print(f"Found {len(redacted_text)} redacted text spans:")
    for item in redacted_text:
        print(f"  - '{item['text']}' at x={item['bbox'].x0:.1f}-{item['bbox'].x1:.1f}, y={item['bbox'].y0:.1f}-{item['bbox'].y1:.1f} ({item['black_ratio']*100:.0f}% black)")

doc.close()

print()
print("="*60)
print("CONCLUSION")
print("="*60)
print("The redaction system is creating black rectangles that don't")
print("correspond to any of the 13 detected entities. This indicates")
print("a bug in either:")
print("1. Entity location detection (finding wrong positions)")
print("2. Additional entities being added silently")
print("3. Coordinate transformation error between text extraction and PDF rendering")
