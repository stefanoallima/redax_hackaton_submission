"""
PII Detector Adapter - Backward Compatibility Wrapper

Provides backward compatibility between old and new detector APIs.
Allows main.py to work with both EnhancedPIIDetector (old) and IntegratedPIIDetector (new).

Author: RedaxAI.app  Team
Date: 2025-11-14
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class PIIDetectorAdapter:
    """
    Adapter to provide backward-compatible API for new integrated detector.

    Wraps IntegratedPIIDetector to match EnhancedPIIDetector API.
    """

    def __init__(self, detector):
        """
        Initialize adapter with either old or new detector.

        Args:
            detector: IntegratedPIIDetector or EnhancedPIIDetector instance
        """
        self.detector = detector
        self.is_integrated = hasattr(detector, '_is_integrated_detector')

        logger.info(f"Adapter initialized with {'integrated' if self.is_integrated else 'old'} detector")

    def process_document(self, document_data: Dict, config=None) -> Dict:
        """
        Process document with PII detection (backward-compatible API).

        Args:
            document_data: Output from DocumentProcessor with 'full_text'
            config: Detection configuration (dict with 'depth' or DetectionConfig object)

        Returns:
            Document with PII entities detected (old API format)
        """
        try:
            # Extract depth from config
            if config is None:
                depth = 'balanced'
            elif isinstance(config, dict):
                depth = config.get('depth', 'balanced')
            else:
                # Assume it's a DetectionConfig object
                depth = getattr(config, 'depth', 'balanced')

            full_text = document_data.get("full_text", "")

            # Call appropriate detector
            if self.is_integrated:
                # New integrated detector returns structured dict
                result = self.detector.detect_pii(full_text, depth=depth, language='it')
                entities = result["entities"]

                # Extract metadata for response
                metadata = result.get("metadata", {})
                performance = result.get("performance", {})

            else:
                # Old detector returns list of entities
                entities = self.detector.detect_pii(full_text, depth=depth)
                metadata = {}
                performance = {}

            # Group entities by type
            entity_summary = {}
            for entity in entities:
                entity_type = entity["entity_type"]
                entity_summary[entity_type] = entity_summary.get(entity_type, 0) + 1

            # Group entities by source
            source_summary = {}
            for entity in entities:
                source = entity.get('source', 'unknown')
                source_summary[source] = source_summary.get(source, 0) + 1

            # Return in old API format (for compatibility with main.py)
            response = {
                "status": "success",
                "entities": entities,
                "entity_summary": entity_summary,
                "source_summary": source_summary,
                "total_entities": len(entities),
                "document_data": document_data,
                "detection_config": {
                    "depth": depth,
                    "gliner_enabled": True,
                    "models_used": list(source_summary.keys())
                }
            }

            # Add new detector metadata if available
            if self.is_integrated:
                response["detection_config"]["architecture"] = "integrated"
                response["detection_config"]["metadata"] = metadata
                response["detection_config"]["performance"] = performance
            else:
                response["detection_config"]["architecture"] = "old"

            return response

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def get_entity_locations(self, file_path: str, entities: List[Dict]) -> List[Dict]:
        """
        Find PDF page coordinates for each entity.

        Args:
            file_path: Path to PDF file
            entities: List of detected entities

        Returns:
            Same entities with added 'locations' field
        """
        try:
            if self.is_integrated:
                # New detector doesn't have get_entity_locations yet
                # Fall back to PIIDetector implementation
                from pii_detector import PIIDetector
                base_detector = PIIDetector()
                return base_detector.get_entity_locations(file_path, entities)
            else:
                # Old detector has this method
                return self.detector.get_entity_locations(file_path, entities)

        except Exception as e:
            logger.error(f"Error getting entity locations: {e}")
            # Return entities without locations on error
            for entity in entities:
                if 'locations' not in entity:
                    entity['locations'] = []
            return entities


# Mark IntegratedPIIDetector instances so adapter can detect them
def mark_as_integrated(detector):
    """Add marker attribute to integrated detector instances."""
    detector._is_integrated_detector = True
    return detector
