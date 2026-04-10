"""
Spatial Context-Aware PII Detector
Extends integrated PII detector with field type inference from spatial context
"""
from typing import List, Dict, Optional, Any
import logging
import time
from pathlib import Path

# Import base integrated detector
from pii_detector_integrated import IntegratedPIIDetector

# Import spatial analysis modules
from spatial_context_analyzer import (
    SpatialContextAnalyzer,
    TextElement,
    BoundingBox as SpatialBBox,
    FieldLabel,
    RedactionContext
)
from pdf_text_extractor import PDFTextExtractor, BoundingBox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpatialPIIDetector(IntegratedPIIDetector):
    """
    PII detector enhanced with spatial context awareness.

    Combines standard PII detection with field type inference based on
    nearby form labels (e.g., "Name:", "Address:", etc.)

    Features:
    - All capabilities of IntegratedPIIDetector
    - Spatial context analysis for form-based documents
    - Field type inference from labels
    - Enhanced redaction metadata with field context
    """

    def __init__(
        self,
        enable_gliner: bool = True,
        use_multi_model: bool = False,
        enable_prefilter: bool = True,
        enable_italian_context: bool = True,
        enable_entity_thresholds: bool = True,
        enable_spatial_context: bool = True,
        proximity_threshold: float = 100
    ):
        """
        Initialize spatial PII detector.

        Args:
            enable_spatial_context: Enable spatial context analysis
            proximity_threshold: Max distance (PDF units) for label-to-value association
            ... (other args inherited from IntegratedPIIDetector)
        """
        # Initialize base detector
        super().__init__(
            enable_gliner=enable_gliner,
            use_multi_model=use_multi_model,
            enable_prefilter=enable_prefilter,
            enable_italian_context=enable_italian_context,
            enable_entity_thresholds=enable_entity_thresholds
        )

        self.enable_spatial_context = enable_spatial_context

        # Initialize spatial analyzer
        if self.enable_spatial_context:
            self.spatial_analyzer = SpatialContextAnalyzer(
                proximity_threshold=proximity_threshold
            )
            self.pdf_extractor = PDFTextExtractor(min_text_length=2)
            logger.info("Spatial context analysis enabled")
        else:
            self.spatial_analyzer = None
            self.pdf_extractor = None
            logger.info("Spatial context analysis disabled")

    def detect_pii_from_pdf(
        self,
        pdf_path: str,
        depth: str = "balanced",
        language: str = "it",
        pages: Optional[List[int]] = None
    ) -> Dict:
        """
        Detect PII in PDF with spatial context analysis.

        Args:
            pdf_path: Path to PDF file
            depth: Detection depth ("fast", "balanced", "thorough", "maximum")
            language: Language code (default: "it")
            pages: List of page numbers to process (0-indexed), None for all

        Returns:
            {
                "entities": List of detected entities with field context,
                "stats": Detection statistics,
                "performance": Performance metrics,
                "metadata": {
                    ... (base metadata)
                    "spatial_context": {
                        "labels_found": int,
                        "entities_with_context": int,
                        "field_type_distribution": dict
                    }
                }
            }
        """
        start_time = time.time()

        # Step 1: Extract text for standard PII detection
        from document_processor import DocumentProcessor
        doc_result = DocumentProcessor.process_pdf(pdf_path)

        if doc_result["status"] == "error":
            return {
                "status": "error",
                "error": doc_result.get("error", "Unknown error"),
                "entities": []
            }

        text = doc_result["full_text"]

        # Step 2: Run standard PII detection
        detection_result = self.detect_pii(text, depth=depth, language=language)

        # Step 3: Add spatial context if enabled
        if self.enable_spatial_context and self.spatial_analyzer:
            spatial_start = time.time()

            # Extract text with bounding boxes
            text_elements = self.pdf_extractor.extract_text_with_boxes(pdf_path, pages=pages)

            # Convert to spatial analyzer format
            spatial_text_elements = [
                TextElement(
                    text=elem.text,
                    bbox=SpatialBBox(
                        x=elem.bbox.x,
                        y=elem.bbox.y,
                        width=elem.bbox.width,
                        height=elem.bbox.height,
                        page=elem.bbox.page
                    ),
                    confidence=elem.confidence
                )
                for elem in text_elements
            ]

            # Find field labels
            labels = self.spatial_analyzer.find_labels_in_document(spatial_text_elements)

            # Enrich entities with spatial context
            enriched_entities = self._enrich_entities_with_context(
                entities=detection_result["entities"],
                text=text,
                labels=labels
            )

            # Update entities
            detection_result["entities"] = enriched_entities

            # Add spatial metadata
            spatial_time = time.time() - spatial_start

            field_type_dist = {}
            entities_with_context = 0

            for entity in enriched_entities:
                if entity.get("field_context"):
                    entities_with_context += 1
                    field_type = entity["field_context"].get("inferred_field_type")
                    if field_type:
                        field_type_dist[field_type] = field_type_dist.get(field_type, 0) + 1

            detection_result["metadata"]["spatial_context"] = {
                "labels_found": len(labels),
                "entities_with_context": entities_with_context,
                "field_type_distribution": field_type_dist,
                "spatial_analysis_time_ms": round(spatial_time * 1000, 2)
            }

            logger.info(
                f"Spatial analysis: Found {len(labels)} labels, "
                f"enriched {entities_with_context}/{len(enriched_entities)} entities"
            )

        # Update total time
        total_time = time.time() - start_time
        detection_result["performance"]["total_time_ms"] = round(total_time * 1000, 2)

        return detection_result

    def _enrich_entities_with_context(
        self,
        entities: List[Dict],
        text: str,
        labels: List[FieldLabel]
    ) -> List[Dict]:
        """
        Enrich detected entities with spatial field context.

        Args:
            entities: List of detected PII entities
            text: Full document text
            labels: List of detected field labels

        Returns:
            Enriched entities with field_context added
        """
        enriched = []

        for entity in entities:
            enriched_entity = entity.copy()

            # Try to find position in text
            entity_text = entity.get("text", "")
            start_pos = entity.get("start")
            end_pos = entity.get("end")

            if start_pos is None or end_pos is None:
                # Try to find in text
                start_pos = text.find(entity_text)
                if start_pos != -1:
                    end_pos = start_pos + len(entity_text)

            # Create approximate bounding box (we don't have exact position from text-only detection)
            # This is a simplified approach - for exact positions we'd need to track them during extraction
            if start_pos is not None and end_pos is not None:
                # Estimate line number and position
                lines_before = text[:start_pos].count('\n')

                # Create synthetic bounding box for matching
                # Note: This is an approximation. For production, you'd want to track
                # exact positions during text extraction
                estimated_bbox = SpatialBBox(
                    x=0,  # Unknown
                    y=lines_before * 15,  # Approximate line height
                    width=len(entity_text) * 7,  # Approximate char width
                    height=15,  # Approximate line height
                    page=0  # Default to first page
                )

                # Find nearby label
                nearby_label = self.spatial_analyzer.find_nearby_label(
                    target_bbox=estimated_bbox,
                    labels=labels
                )

                if nearby_label:
                    # Add field context
                    enriched_entity["field_context"] = {
                        "inferred_field_type": nearby_label.field_type,
                        "nearby_label": nearby_label.label_text,
                        "confidence": nearby_label.confidence,
                        "reasoning": f"Found '{nearby_label.label_text}' label nearby"
                    }

                    logger.debug(
                        f"Entity '{entity_text}' enriched with field type: "
                        f"{nearby_label.field_type} (label: {nearby_label.label_text})"
                    )
                else:
                    enriched_entity["field_context"] = None

            enriched.append(enriched_entity)

        return enriched

    def generate_redaction_report(
        self,
        entities: List[Dict],
        pdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed redaction report with field context.

        Args:
            entities: List of detected entities (with field_context)
            pdf_path: Optional path to PDF for additional analysis

        Returns:
            Detailed redaction report
        """
        report = {
            "total_entities": len(entities),
            "by_entity_type": {},
            "by_field_type": {},
            "entities_with_context": 0,
            "entities_without_context": 0,
            "high_confidence_redactions": 0,
            "field_type_matches": 0,
            "field_type_mismatches": 0,
            "details": []
        }

        for entity in entities:
            # Count by entity type (PERSON, EMAIL, etc.)
            entity_type = entity.get("entity_type", "UNKNOWN")
            report["by_entity_type"][entity_type] = \
                report["by_entity_type"].get(entity_type, 0) + 1

            # Count by field type (from spatial context)
            field_context = entity.get("field_context")

            if field_context:
                report["entities_with_context"] += 1

                field_type = field_context.get("inferred_field_type")
                if field_type:
                    report["by_field_type"][field_type] = \
                        report["by_field_type"].get(field_type, 0) + 1

                    # Check if entity type matches field type
                    if entity_type == field_type:
                        report["field_type_matches"] += 1
                    else:
                        report["field_type_mismatches"] += 1

                # High confidence (both entity detection and field inference)
                entity_score = entity.get("score", 0)
                field_confidence = field_context.get("confidence", 0)

                if entity_score >= 0.8 and field_confidence >= 0.8:
                    report["high_confidence_redactions"] += 1

                # Add detail
                report["details"].append({
                    "text": entity.get("text", ""),
                    "entity_type": entity_type,
                    "field_type": field_type,
                    "label": field_context.get("nearby_label"),
                    "entity_confidence": entity_score,
                    "field_confidence": field_confidence
                })
            else:
                report["entities_without_context"] += 1

        return report

    def get_detailed_report(self, result: Dict) -> str:
        """
        Generate detailed detection report with spatial context.

        Extends base report with spatial analysis information.
        """
        # Get base report
        base_report = super().get_detailed_report(result)

        # Add spatial context section
        if "spatial_context" in result.get("metadata", {}):
            spatial_meta = result["metadata"]["spatial_context"]

            lines = []
            lines.append("\nSPATIAL CONTEXT ANALYSIS:")
            lines.append(f"  Labels found: {spatial_meta['labels_found']}")
            lines.append(f"  Entities enriched: {spatial_meta['entities_with_context']} / {len(result['entities'])}")

            if spatial_meta["field_type_distribution"]:
                lines.append(f"\n  Field Types Detected:")
                for field_type, count in sorted(spatial_meta["field_type_distribution"].items()):
                    lines.append(f"    - {field_type}: {count}")

            lines.append(f"\n  Analysis time: {spatial_meta['spatial_analysis_time_ms']:.2f}ms")

            # Insert spatial section before final separator
            report_parts = base_report.rsplit("\n" + "=" * 70, 1)
            if len(report_parts) == 2:
                return report_parts[0] + "\n".join(lines) + "\n\n" + "=" * 70
            else:
                return base_report + "\n" + "\n".join(lines)

        return base_report


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pii_detector_spatial.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    print("=" * 80)
    print("SPATIAL CONTEXT-AWARE PII DETECTION")
    print("=" * 80)

    # Initialize detector
    detector = SpatialPIIDetector(
        enable_gliner=True,
        enable_prefilter=True,
        enable_italian_context=True,
        enable_entity_thresholds=True,
        enable_spatial_context=True
    )

    # Detect PII with spatial context
    print(f"\nAnalyzing: {pdf_path}\n")

    result = detector.detect_pii_from_pdf(pdf_path, depth="balanced")

    # Print report
    if result.get("status") == "error":
        print(f"Error: {result.get('error')}")
    else:
        report = detector.get_detailed_report(result)
        print(report)

        # Generate redaction report
        print("\n" + "=" * 80)
        print("REDACTION REPORT (Field Context)")
        print("=" * 80)

        redaction_report = detector.generate_redaction_report(result["entities"], pdf_path)

        print(f"\nTotal entities: {redaction_report['total_entities']}")
        print(f"With field context: {redaction_report['entities_with_context']}")
        print(f"Without context: {redaction_report['entities_without_context']}")
        print(f"High confidence: {redaction_report['high_confidence_redactions']}")

        if redaction_report["by_field_type"]:
            print(f"\nField Types:")
            for field_type, count in sorted(redaction_report["by_field_type"].items()):
                print(f"  {field_type}: {count}")

        print(f"\nField type matches: {redaction_report['field_type_matches']}")
        print(f"Field type mismatches: {redaction_report['field_type_mismatches']}")

        # Show sample details
        if redaction_report["details"]:
            print(f"\nSample Detections (first 5):")
            for i, detail in enumerate(redaction_report["details"][:5], 1):
                print(f"\n{i}. \"{detail['text']}\"")
                print(f"   Entity type: {detail['entity_type']}")
                print(f"   Field type: {detail['field_type']}")
                print(f"   Label: {detail['label']}")
                print(f"   Confidences: entity={detail['entity_confidence']:.2f}, field={detail['field_confidence']:.2f}")
