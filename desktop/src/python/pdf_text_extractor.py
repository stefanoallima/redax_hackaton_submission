"""
PDF Text Extractor with Bounding Boxes
Extracts text from PDFs with position information for spatial context analysis
"""
import fitz  # PyMuPDF
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Rectangle coordinates in PDF"""
    x: float
    y: float
    width: float
    height: float
    page: int = 0

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def center_x(self):
        return self.x + self.width / 2

    @property
    def center_y(self):
        return self.y + self.height / 2

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class TextElement:
    """Text found in document with position"""
    text: str
    bbox: BoundingBox
    confidence: float = 1.0

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'text': self.text,
            'bbox': self.bbox.to_dict(),
            'confidence': self.confidence
        }


class PDFTextExtractor:
    """
    Extract text from PDFs with bounding box information
    Uses PyMuPDF for precise text positioning
    """

    def __init__(self, min_text_length: int = 1):
        """
        Initialize extractor

        Args:
            min_text_length: Minimum text length to include (filters out noise)
        """
        self.min_text_length = min_text_length

    def extract_text_with_boxes(
        self,
        pdf_path: str,
        pages: Optional[List[int]] = None
    ) -> List[TextElement]:
        """
        Extract text elements with bounding boxes from PDF

        Args:
            pdf_path: Path to PDF file
            pages: List of page numbers to extract (0-indexed), None for all pages

        Returns:
            List of TextElement objects with text and position
        """
        try:
            doc = fitz.open(pdf_path)
            text_elements = []

            # Determine which pages to process
            page_nums = pages if pages is not None else range(len(doc))

            for page_num in page_nums:
                if page_num >= len(doc):
                    logger.warning(f"Page {page_num} out of range (document has {len(doc)} pages)")
                    continue

                page = doc[page_num]
                page_elements = self._extract_page_text(page, page_num)
                text_elements.extend(page_elements)

                logger.debug(f"Extracted {len(page_elements)} text elements from page {page_num + 1}")

            doc.close()
            logger.info(f"Extracted {len(text_elements)} text elements from {len(page_nums)} pages")

            return text_elements

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return []

    def _extract_page_text(self, page: fitz.Page, page_num: int) -> List[TextElement]:
        """
        Extract text elements from a single page

        Args:
            page: PyMuPDF Page object
            page_num: Page number (0-indexed)

        Returns:
            List of TextElement objects
        """
        text_elements = []

        # Extract text as dictionary with detailed information
        # flags: 0 = default, 1 = preserve ligatures, 2 = preserve whitespace
        text_dict = page.get_text("dict", flags=0)

        # Iterate through text blocks
        for block in text_dict.get("blocks", []):
            # Only process text blocks (type 0), not image blocks (type 1)
            if block.get("type") != 0:
                continue

            # Iterate through lines in block
            for line in block.get("lines", []):
                # Iterate through spans (text segments with same formatting)
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()

                    # Filter out empty or too short text
                    if len(text) < self.min_text_length:
                        continue

                    # Get bounding box (x0, y0, x1, y1)
                    bbox_tuple = span.get("bbox", (0, 0, 0, 0))
                    x0, y0, x1, y1 = bbox_tuple

                    # Convert to BoundingBox object
                    bbox = BoundingBox(
                        x=x0,
                        y=y0,
                        width=x1 - x0,
                        height=y1 - y0,
                        page=page_num
                    )

                    # Create TextElement
                    element = TextElement(
                        text=text,
                        bbox=bbox,
                        confidence=1.0  # PyMuPDF extraction is reliable
                    )

                    text_elements.append(element)

        return text_elements

    def extract_text_only(self, pdf_path: str, pages: Optional[List[int]] = None) -> str:
        """
        Extract plain text from PDF (no bounding boxes)

        Args:
            pdf_path: Path to PDF file
            pages: List of page numbers to extract (0-indexed), None for all pages

        Returns:
            Extracted text as string
        """
        try:
            doc = fitz.open(pdf_path)
            text_parts = []

            # Determine which pages to process
            page_nums = pages if pages is not None else range(len(doc))

            for page_num in page_nums:
                if page_num >= len(doc):
                    logger.warning(f"Page {page_num} out of range")
                    continue

                page = doc[page_num]
                text = page.get_text()
                text_parts.append(text)

            doc.close()
            full_text = "\n\n".join(text_parts)

            logger.info(f"Extracted {len(full_text)} characters from {len(page_nums)} pages")
            return full_text

        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""

    def get_page_dimensions(self, pdf_path: str) -> List[Dict]:
        """
        Get dimensions of all pages in PDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of dicts with page dimensions: [{"page": 0, "width": 612, "height": 792}, ...]
        """
        try:
            doc = fitz.open(pdf_path)
            dimensions = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                rect = page.rect

                dimensions.append({
                    "page": page_num,
                    "width": rect.width,
                    "height": rect.height
                })

            doc.close()
            return dimensions

        except Exception as e:
            logger.error(f"Error getting page dimensions: {e}")
            return []


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_text_extractor.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Initialize extractor
    extractor = PDFTextExtractor(min_text_length=2)

    # Extract text with bounding boxes
    print(f"\nExtracting text from: {pdf_path}\n")

    text_elements = extractor.extract_text_with_boxes(pdf_path)

    print(f"Found {len(text_elements)} text elements\n")

    # Show first 10 elements
    print("First 10 text elements:")
    print("=" * 80)

    for i, element in enumerate(text_elements[:10], 1):
        print(f"{i}. \"{element.text}\"")
        print(f"   Page: {element.bbox.page + 1}")
        print(f"   Position: ({element.bbox.x:.1f}, {element.bbox.y:.1f})")
        print(f"   Size: {element.bbox.width:.1f} x {element.bbox.height:.1f}")
        print()

    if len(text_elements) > 10:
        print(f"... and {len(text_elements) - 10} more")

    # Show page dimensions
    print("\n" + "=" * 80)
    print("Page Dimensions:")
    print("=" * 80)

    dimensions = extractor.get_page_dimensions(pdf_path)
    for dim in dimensions:
        print(f"Page {dim['page'] + 1}: {dim['width']:.1f} x {dim['height']:.1f}")
