"""
Redaction Safety Module
Comprehensive checks to prevent redacting invisible or already-redacted text
"""
import fitz  # PyMuPDF
from typing import List, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class RedactionSafetyChecker:
    """
    Provides safety checks for PDF redaction operations to prevent:
    - Redacting already-redacted areas
    - Redacting invisible/hidden text
    - Redacting text that doesn't match expected content
    """

    def __init__(self):
        """Initialize safety checker"""
        self.stats = {
            'already_redacted': 0,
            'invisible_text': 0,
            'text_mismatch': 0,
            'safe_redactions': 0
        }

    def detect_existing_redactions(self, page: fitz.Page) -> List[fitz.Rect]:
        """
        Detect areas that are already redacted (black/dark boxes)

        Args:
            page: PyMuPDF page object

        Returns:
            List of rectangles representing already-redacted areas
        """
        redacted_areas = []

        # Method 1: Check for black rectangles in drawings
        try:
            drawings = page.get_drawings()
            for drawing in drawings:
                if 'fill' in drawing and drawing['fill']:
                    # Check if fill color is black or very dark
                    fill_color = drawing['fill']
                    if isinstance(fill_color, (list, tuple)) and len(fill_color) >= 3:
                        r, g, b = fill_color[0], fill_color[1], fill_color[2]
                        if r < 0.1 and g < 0.1 and b < 0.1:  # Nearly black
                            redacted_areas.append(fitz.Rect(drawing['rect']))
        except Exception as e:
            logger.debug(f"Could not check drawings for redactions: {e}")

        # Method 2: Check for redaction annotations
        try:
            annots = page.annots()
            if annots:
                for annot in annots:
                    if annot.type[0] == 12:  # Redaction annotation type
                        redacted_areas.append(annot.rect)
        except Exception as e:
            logger.debug(f"Could not check annotations for redactions: {e}")

        # Method 3: Check for filled shapes with black or very dark colors
        try:
            # Get page content and look for filled rectangles
            for drawing in page.get_drawings():
                if drawing.get('type') == 'f' or drawing.get('type') == 'fs':  # Fill operations
                    # Check if it's a dark fill
                    if 'color' in drawing:
                        color = drawing['color']
                        if isinstance(color, (list, tuple)) and len(color) >= 3:
                            r, g, b = color[0], color[1], color[2]
                            # Dark colors (common for redaction)
                            if r < 0.15 and g < 0.15 and b < 0.15:
                                redacted_areas.append(fitz.Rect(drawing['rect']))
        except Exception as e:
            logger.debug(f"Could not check filled shapes: {e}")

        if redacted_areas:
            logger.info(f"Found {len(redacted_areas)} potentially redacted areas on page")

        return redacted_areas

    def is_already_redacted(self, rect: fitz.Rect, existing_redactions: List[fitz.Rect]) -> bool:
        """
        Check if this area overlaps with existing redactions

        Args:
            rect: Rectangle to check
            existing_redactions: List of already-redacted rectangles

        Returns:
            True if area is already redacted
        """
        for redacted_rect in existing_redactions:
            if rect.intersects(redacted_rect):
                # Calculate overlap percentage
                intersection = rect & redacted_rect  # Intersection
                if intersection:
                    overlap_ratio = intersection.get_area() / rect.get_area()
                    if overlap_ratio > 0.5:  # More than 50% overlap
                        self.stats['already_redacted'] += 1
                        return True
        return False

    def is_text_visible(self, page: fitz.Page, rect: fitz.Rect,
                       white_threshold: int = 250,
                       visibility_threshold: float = 0.70) -> bool:
        """
        Check if text is actually visible by analyzing rendered pixels
        Returns False if area is mostly white/blank (invisible text)

        Args:
            page: PyMuPDF page object
            rect: Rectangle to check
            white_threshold: RGB value threshold for considering a pixel white (0-255)
            visibility_threshold: Percentage of white pixels that indicates invisible text

        Returns:
            True if text appears to be visible, False if invisible
        """
        try:
            # Render area to image at 2x resolution for better accuracy
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat, clip=rect)

            # Get pixel data
            samples = pix.samples
            width, height = pix.width, pix.height
            total_pixels = width * height

            if total_pixels == 0:
                logger.debug("Empty rectangle - considering invisible")
                return False

            # Count white/near-white pixels
            white_count = 0

            # Determine pixel format (RGB or RGBA)
            n = pix.n  # Number of components per pixel (3 for RGB, 4 for RGBA)

            # Check every n bytes (RGB or RGBA)
            for i in range(0, len(samples), n):
                r = samples[i]
                g = samples[i + 1] if i + 1 < len(samples) else 255
                b = samples[i + 2] if i + 2 < len(samples) else 255

                if r >= white_threshold and g >= white_threshold and b >= white_threshold:
                    white_count += 1

            white_ratio = white_count / total_pixels

            # If area is >95% white, consider text invisible
            if white_ratio > 0.95:
                logger.debug(f"Area is {white_ratio*100:.1f}% white - considering invisible")
                self.stats['invisible_text'] += 1
                return False

            # If area is >threshold white, it's likely very faint or invisible
            if white_ratio > visibility_threshold:
                logger.debug(f"Area is {white_ratio*100:.1f}% white - considering invisible")
                self.stats['invisible_text'] += 1
                return False

            # Text appears to be visible
            return True

        except Exception as e:
            logger.warning(f"Could not check visibility: {e}")
            # Default to visible if we can't check (conservative approach)
            return True

    def texts_match(self, expected: str, found: str, similarity_threshold: float = 0.85) -> bool:
        """
        Check if two text strings match (fuzzy comparison)
        Handles case, whitespace, and minor differences

        Args:
            expected: Expected text (from PII detection)
            found: Text found at location (from PDF)
            similarity_threshold: Minimum similarity ratio (0-1)

        Returns:
            True if texts match sufficiently
        """
        def normalize(text):
            """Remove extra whitespace and lowercase"""
            if not text:
                return ""
            return ' '.join(text.lower().split())

        expected_norm = normalize(expected)
        found_norm = normalize(found)

        # Exact match after normalization
        if expected_norm == found_norm:
            return True

        # Contains match (for partial extractions)
        if expected_norm in found_norm or found_norm in expected_norm:
            return True

        # Fuzzy match using edit distance (for OCR differences, typos)
        if len(expected_norm) > 5:
            ratio = SequenceMatcher(None, expected_norm, found_norm).ratio()
            if ratio >= similarity_threshold:
                logger.debug(f"Fuzzy match: '{expected}' ~ '{found}' (similarity: {ratio*100:.1f}%)")
                return True
            else:
                logger.debug(f"Text mismatch: '{expected}' vs '{found}' (similarity: {ratio*100:.1f}%)")
                self.stats['text_mismatch'] += 1
                return False

        # For short strings, require exact match
        self.stats['text_mismatch'] += 1
        return False

    def is_safe_to_redact(self,
                         page: fitz.Page,
                         rect: fitz.Rect,
                         expected_text: str,
                         existing_redactions: List[fitz.Rect],
                         check_visibility: bool = True,
                         check_text_match: bool = True) -> Tuple[bool, str]:
        """
        Comprehensive safety check before redacting

        Args:
            page: PyMuPDF page object
            rect: Rectangle to redact
            expected_text: Expected text at this location
            existing_redactions: List of already-redacted areas
            check_visibility: Whether to perform pixel-based visibility check
            check_text_match: Whether to verify text content matches

        Returns:
            Tuple of (is_safe, reason)
            - is_safe: True if safe to redact
            - reason: Human-readable reason if not safe
        """
        # Check 1: Is this area already redacted?
        if self.is_already_redacted(rect, existing_redactions):
            return False, "Already redacted"

        # Check 2: Is the text actually visible? (pixel-based check)
        if check_visibility:
            if not self.is_text_visible(page, rect):
                return False, "Invisible text (white-on-white or hidden)"

        # Check 3: Does the text match what we expect?
        if check_text_match and expected_text:
            text_at_location = page.get_textbox(rect).strip()
            if not self.texts_match(expected_text, text_at_location):
                return False, f"Text mismatch (expected: '{expected_text}', found: '{text_at_location}')"

        # All checks passed
        self.stats['safe_redactions'] += 1
        return True, "Safe to redact"

    def get_stats(self) -> dict:
        """
        Get statistics on safety checks performed

        Returns:
            Dictionary with check statistics
        """
        return {
            'already_redacted_blocked': self.stats['already_redacted'],
            'invisible_text_blocked': self.stats['invisible_text'],
            'text_mismatch_blocked': self.stats['text_mismatch'],
            'safe_redactions': self.stats['safe_redactions'],
            'total_checks': sum(self.stats.values())
        }

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            'already_redacted': 0,
            'invisible_text': 0,
            'text_mismatch': 0,
            'safe_redactions': 0
        }


# Example usage
if __name__ == "__main__":
    # Test the safety checker
    checker = RedactionSafetyChecker()

    # Open a test PDF
    doc = fitz.open("test.pdf")
    page = doc[0]

    # Detect existing redactions
    existing_redactions = checker.detect_existing_redactions(page)
    print(f"Found {len(existing_redactions)} existing redactions")

    # Test a rectangle
    test_rect = fitz.Rect(100, 100, 200, 120)
    is_safe, reason = checker.is_safe_to_redact(
        page,
        test_rect,
        "Test Text",
        existing_redactions
    )

    print(f"Safe to redact: {is_safe} - {reason}")
    print(f"Statistics: {checker.get_stats()}")

    doc.close()
