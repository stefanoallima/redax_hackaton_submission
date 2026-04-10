"""
Spatial Context Analyzer
Identifies field types by analyzing text labels near redacted regions

Example Use Case:
  Form shows: "Name: ___Mario___"
  After redaction: "Name: ████████"
  This analyzer infers: "Redacted text was a PERSON name based on 'Name:' label"
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
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


@dataclass
class TextElement:
    """Text found in document with position"""
    text: str
    bbox: BoundingBox
    confidence: float = 1.0


@dataclass
class FieldLabel:
    """Detected form field label"""
    label_text: str
    field_type: str
    bbox: BoundingBox
    pattern_matched: str
    confidence: float


@dataclass
class RedactionContext:
    """Metadata about what was redacted"""
    redacted_text: str
    bbox: BoundingBox
    inferred_field_type: Optional[str] = None
    nearby_label: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""


class SpatialContextAnalyzer:
    """
    Analyze spatial relationships between labels and values in forms
    to infer what type of data was redacted
    """

    # Field label patterns (Italian and English)
    FIELD_PATTERNS = {
        'PERSON': [
            # Italian
            r'^\s*Nome\s*[:\-]?\s*$',
            r'^\s*Cognome\s*[:\-]?\s*$',
            r'^\s*Nome\s+e\s+Cognome\s*[:\-]?\s*$',
            r'^\s*Nominativo\s*[:\-]?\s*$',
            r'^\s*Intestatario\s*[:\-]?\s*$',
            # English
            r'^\s*Name\s*[:\-]?\s*$',
            r'^\s*Full\s+Name\s*[:\-]?\s*$',
            r'^\s*First\s+Name\s*[:\-]?\s*$',
            r'^\s*Last\s+Name\s*[:\-]?\s*$',
            r'^\s*Surname\s*[:\-]?\s*$',
        ],
        'ADDRESS': [
            # Italian
            r'^\s*Indirizzo\s*[:\-]?\s*$',
            r'^\s*Via\s*[:\-]?\s*$',
            r'^\s*Domicilio\s*[:\-]?\s*$',
            r'^\s*Residenza\s*[:\-]?\s*$',
            r'^\s*Città\s*[:\-]?\s*$',
            r'^\s*CAP\s*[:\-]?\s*$',
            # English
            r'^\s*Address\s*[:\-]?\s*$',
            r'^\s*Street\s*[:\-]?\s*$',
            r'^\s*City\s*[:\-]?\s*$',
            r'^\s*Zip\s*Code\s*[:\-]?\s*$',
            r'^\s*Postal\s+Code\s*[:\-]?\s*$',
        ],
        'DATE': [
            # Italian
            r'^\s*Data\s*[:\-]?\s*$',
            r'^\s*Data\s+di\s+nascita\s*[:\-]?\s*$',
            r'^\s*Nato\s+il\s*[:\-]?\s*$',
            r'^\s*Luogo\s+e\s+data\s*[:\-]?\s*$',
            # English
            r'^\s*Date\s*[:\-]?\s*$',
            r'^\s*Date\s+of\s+Birth\s*[:\-]?\s*$',
            r'^\s*DOB\s*[:\-]?\s*$',
            r'^\s*Birth\s+Date\s*[:\-]?\s*$',
        ],
        'PHONE': [
            # Italian
            r'^\s*Telefono\s*[:\-]?\s*$',
            r'^\s*Tel\.?\s*[:\-]?\s*$',
            r'^\s*Cellulare\s*[:\-]?\s*$',
            r'^\s*Mobile\s*[:\-]?\s*$',
            # English
            r'^\s*Phone\s*[:\-]?\s*$',
            r'^\s*Mobile\s*[:\-]?\s*$',
            r'^\s*Cell\s*[:\-]?\s*$',
        ],
        'EMAIL': [
            # Italian
            r'^\s*Email\s*[:\-]?\s*$',
            r'^\s*E-mail\s*[:\-]?\s*$',
            r'^\s*Posta\s+elettronica\s*[:\-]?\s*$',
            # English
            r'^\s*Email\s*[:\-]?\s*$',
            r'^\s*E-mail\s*[:\-]?\s*$',
        ],
        'TAX_ID': [
            # Italian
            r'^\s*Codice\s+Fiscale\s*[:\-]?\s*$',
            r'^\s*CF\s*[:\-]?\s*$',
            r'^\s*C\.F\.\s*[:\-]?\s*$',
            r'^\s*Partita\s+IVA\s*[:\-]?\s*$',
            r'^\s*P\.IVA\s*[:\-]?\s*$',
            # English
            r'^\s*Tax\s+ID\s*[:\-]?\s*$',
            r'^\s*SSN\s*[:\-]?\s*$',
        ],
        'AMOUNT': [
            # Italian
            r'^\s*Importo\s*[:\-]?\s*$',
            r'^\s*Totale\s*[:\-]?\s*$',
            r'^\s*Prezzo\s*[:\-]?\s*$',
            # English
            r'^\s*Amount\s*[:\-]?\s*$',
            r'^\s*Total\s*[:\-]?\s*$',
            r'^\s*Price\s*[:\-]?\s*$',
        ],
    }

    def __init__(self, proximity_threshold: float = 100):
        """
        Initialize analyzer

        Args:
            proximity_threshold: Max distance (in PDF units) to consider text as "nearby"
        """
        self.proximity_threshold = proximity_threshold
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for faster matching"""
        self.compiled_patterns = {}
        for field_type, patterns in self.FIELD_PATTERNS.items():
            self.compiled_patterns[field_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def identify_label_type(self, text: str) -> Optional[Tuple[str, str, float]]:
        """
        Identify if text is a form field label

        Args:
            text: Text to check

        Returns:
            (field_type, pattern_matched, confidence) or None
        """
        text_normalized = text.strip()

        for field_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.match(text_normalized):
                    return (field_type, pattern.pattern, 0.95)

        return None

    def find_labels_in_document(
        self, text_elements: List[TextElement]
    ) -> List[FieldLabel]:
        """
        Find all form field labels in document

        Args:
            text_elements: All text extracted from PDF with positions

        Returns:
            List of detected field labels
        """
        labels = []

        for element in text_elements:
            label_info = self.identify_label_type(element.text)
            if label_info:
                field_type, pattern, confidence = label_info
                labels.append(
                    FieldLabel(
                        label_text=element.text,
                        field_type=field_type,
                        bbox=element.bbox,
                        pattern_matched=pattern,
                        confidence=confidence
                    )
                )

        logger.info(f"Found {len(labels)} field labels in document")
        return labels

    def find_value_region_for_label(
        self,
        label: FieldLabel,
        search_direction: str = 'auto'
    ) -> BoundingBox:
        """
        Predict where the value should be relative to label

        Args:
            label: The field label
            search_direction: 'right', 'below', or 'auto'

        Returns:
            Predicted bounding box for field value
        """
        if search_direction == 'auto':
            # Heuristic: If label ends with ":", value is usually to the right
            # Otherwise, value might be below
            if label.label_text.strip().endswith(':'):
                search_direction = 'right'
            else:
                search_direction = 'below'

        if search_direction == 'right':
            # Value is to the right of label
            return BoundingBox(
                x=label.bbox.right + 5,  # Small gap
                y=label.bbox.y,
                width=200,  # Typical field width
                height=label.bbox.height,
                page=label.bbox.page
            )
        else:  # below
            # Value is below label
            return BoundingBox(
                x=label.bbox.x,
                y=label.bbox.bottom + 5,  # Small gap
                width=label.bbox.width,
                height=20,  # Typical line height
                page=label.bbox.page
            )

    def find_nearby_label(
        self,
        target_bbox: BoundingBox,
        labels: List[FieldLabel]
    ) -> Optional[FieldLabel]:
        """
        Find the closest label to a target region (e.g., redacted box)

        Args:
            target_bbox: Region to search near (e.g., redacted text)
            labels: All detected labels in document

        Returns:
            Closest label or None
        """
        closest_label = None
        min_distance = float('inf')

        for label in labels:
            # Only consider labels on same page
            if label.bbox.page != target_bbox.page:
                continue

            # Calculate distance between regions
            distance = self._calculate_distance(label.bbox, target_bbox)

            if distance < min_distance and distance < self.proximity_threshold:
                min_distance = distance
                closest_label = label

        return closest_label

    def _calculate_distance(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """
        Calculate distance between two bounding boxes
        Uses center-to-center Euclidean distance
        """
        dx = bbox1.center_x - bbox2.center_x
        dy = bbox1.center_y - bbox2.center_y
        return (dx**2 + dy**2) ** 0.5

    def analyze_redaction_context(
        self,
        redacted_bbox: BoundingBox,
        redacted_text: str,
        all_labels: List[FieldLabel]
    ) -> RedactionContext:
        """
        Infer what type of data was redacted based on nearby labels

        Args:
            redacted_bbox: Location of redacted region
            redacted_text: The text that was redacted (if known)
            all_labels: All field labels in document

        Returns:
            Context information about the redaction
        """
        nearby_label = self.find_nearby_label(redacted_bbox, all_labels)

        if nearby_label:
            return RedactionContext(
                redacted_text=redacted_text,
                bbox=redacted_bbox,
                inferred_field_type=nearby_label.field_type,
                nearby_label=nearby_label.label_text,
                confidence=nearby_label.confidence,
                reasoning=f"Found '{nearby_label.label_text}' label nearby"
            )
        else:
            return RedactionContext(
                redacted_text=redacted_text,
                bbox=redacted_bbox,
                inferred_field_type=None,
                nearby_label=None,
                confidence=0.0,
                reasoning="No nearby label found"
            )

    def generate_redaction_summary(
        self, redaction_contexts: List[RedactionContext]
    ) -> Dict[str, any]:
        """
        Generate summary statistics about redactions

        Args:
            redaction_contexts: All redactions with their contexts

        Returns:
            Summary dictionary
        """
        summary = {
            'total_redactions': len(redaction_contexts),
            'by_field_type': {},
            'high_confidence': 0,
            'low_confidence': 0,
            'unknown_type': 0,
        }

        for ctx in redaction_contexts:
            # Count by field type
            field_type = ctx.inferred_field_type or 'UNKNOWN'
            summary['by_field_type'][field_type] = \
                summary['by_field_type'].get(field_type, 0) + 1

            # Count confidence levels
            if ctx.confidence >= 0.8:
                summary['high_confidence'] += 1
            elif ctx.confidence >= 0.5:
                pass  # Medium confidence
            else:
                summary['low_confidence'] += 1

            if ctx.inferred_field_type is None:
                summary['unknown_type'] += 1

        return summary


# Example usage
if __name__ == "__main__":
    # Simulated document text elements
    text_elements = [
        TextElement("Nome:", BoundingBox(50, 100, 40, 15)),
        TextElement("Mario Rossi", BoundingBox(100, 100, 80, 15)),
        TextElement("Indirizzo:", BoundingBox(50, 150, 60, 15)),
        TextElement("Via Roma 15", BoundingBox(120, 150, 100, 15)),
    ]

    # Initialize analyzer
    analyzer = SpatialContextAnalyzer()

    # Find labels
    labels = analyzer.find_labels_in_document(text_elements)
    print(f"\nFound {len(labels)} labels:")
    for label in labels:
        print(f"  - {label.label_text} → {label.field_type}")

    # Simulate redaction
    redacted_bbox = BoundingBox(100, 100, 80, 15)  # "Mario Rossi" location
    context = analyzer.analyze_redaction_context(
        redacted_bbox=redacted_bbox,
        redacted_text="Mario Rossi",
        all_labels=labels
    )

    print(f"\nRedaction Analysis:")
    print(f"  Redacted: {context.redacted_text}")
    print(f"  Inferred Type: {context.inferred_field_type}")
    print(f"  Nearby Label: {context.nearby_label}")
    print(f"  Confidence: {context.confidence:.2%}")
    print(f"  Reasoning: {context.reasoning}")
