"""
Spatial Context Integration Module
Provides easy integration of spatial context analysis into the detection pipeline
"""
import os
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SpatialIntegrationConfig:
    """
    Configuration for spatial context integration

    Can be enabled/disabled via environment variable or runtime config
    """

    # Environment variable to control spatial context
    ENV_VAR = "ENABLE_SPATIAL_CONTEXT"

    # Default setting
    DEFAULT_ENABLED = True  # Enable by default for better field identification

    @staticmethod
    def is_enabled() -> bool:
        """
        Check if spatial context analysis is enabled

        Checks:
        1. Environment variable ENABLE_SPATIAL_CONTEXT
        2. Falls back to default (True)

        Returns:
            True if enabled, False otherwise
        """
        env_value = os.getenv(SpatialIntegrationConfig.ENV_VAR)

        if env_value is not None:
            # Parse env var (1, true, yes = enabled)
            return env_value.lower() in ('1', 'true', 'yes', 'on')

        # Use default
        return SpatialIntegrationConfig.DEFAULT_ENABLED

    @staticmethod
    def get_proximity_threshold() -> float:
        """
        Get proximity threshold for label-to-value association

        Can be configured via SPATIAL_PROXIMITY_THRESHOLD env var

        Returns:
            Proximity threshold in PDF units (default: 100)
        """
        env_value = os.getenv("SPATIAL_PROXIMITY_THRESHOLD")

        if env_value:
            try:
                return float(env_value)
            except ValueError:
                logger.warning(f"Invalid SPATIAL_PROXIMITY_THRESHOLD: {env_value}, using default")

        return 100.0  # Default threshold


def create_detector(
    enable_spatial: Optional[bool] = None,
    enable_gliner: bool = True,
    use_multi_model: bool = False,
    enable_prefilter: bool = True,
    enable_italian_context: bool = True,
    enable_entity_thresholds: bool = True
):
    """
    Create PII detector with optional spatial context

    Args:
        enable_spatial: Enable spatial context (None = use config default)
        ... (other args for detector configuration)

    Returns:
        Detector instance (either IntegratedPIIDetector or SpatialPIIDetector)

    Example:
        # Auto-detect from environment
        detector = create_detector()

        # Explicitly enable spatial
        detector = create_detector(enable_spatial=True)

        # Explicitly disable spatial
        detector = create_detector(enable_spatial=False)
    """
    # Determine if spatial should be enabled
    if enable_spatial is None:
        enable_spatial = SpatialIntegrationConfig.is_enabled()

    if enable_spatial:
        # Use spatial detector
        try:
            from pii_detector_spatial import SpatialPIIDetector

            proximity_threshold = SpatialIntegrationConfig.get_proximity_threshold()

            detector = SpatialPIIDetector(
                enable_gliner=enable_gliner,
                use_multi_model=use_multi_model,
                enable_prefilter=enable_prefilter,
                enable_italian_context=enable_italian_context,
                enable_entity_thresholds=enable_entity_thresholds,
                enable_spatial_context=True,
                proximity_threshold=proximity_threshold
            )

            logger.info(f"Spatial context enabled (threshold: {proximity_threshold})")
            return detector

        except Exception as e:
            logger.warning(f"Failed to load spatial detector, falling back to standard: {e}")
            # Fall through to standard detector

    # Use standard integrated detector
    from pii_detector_integrated import IntegratedPIIDetector

    detector = IntegratedPIIDetector(
        enable_gliner=enable_gliner,
        use_multi_model=use_multi_model,
        enable_prefilter=enable_prefilter,
        enable_italian_context=enable_italian_context,
        enable_entity_thresholds=enable_entity_thresholds
    )

    logger.info("Using standard PII detector (spatial context disabled)")
    return detector


def detect_pii_with_spatial_support(
    file_path: str,
    depth: str = "balanced",
    language: str = "it",
    enable_spatial: Optional[bool] = None,
    **detector_kwargs
) -> Dict:
    """
    Detect PII with automatic spatial context support

    Automatically uses spatial detection for PDFs, standard detection for other formats

    Args:
        file_path: Path to document
        depth: Detection depth
        language: Language code
        enable_spatial: Override spatial detection (None = auto)
        **detector_kwargs: Additional detector configuration

    Returns:
        Detection result with entities and metadata
    """
    # Create detector
    detector = create_detector(enable_spatial=enable_spatial, **detector_kwargs)

    # Check file type
    file_ext = Path(file_path).suffix.lower()

    # For PDFs, use spatial detection if available
    if file_ext == '.pdf' and hasattr(detector, 'detect_pii_from_pdf'):
        logger.info("Using PDF spatial detection")
        return detector.detect_pii_from_pdf(
            pdf_path=file_path,
            depth=depth,
            language=language
        )
    else:
        # For other formats, extract text and use standard detection
        logger.info(f"Using standard text detection for {file_ext}")

        from document_processor import DocumentProcessor

        # Extract text
        doc_result = DocumentProcessor.process_document(file_path)

        if doc_result["status"] == "error":
            return doc_result

        text = doc_result.get("full_text", "")

        # Detect PII
        return detector.detect_pii(text, depth=depth, language=language)


# Example usage and testing
if __name__ == "__main__":
    import sys

    print("=" * 80)
    print("SPATIAL CONTEXT INTEGRATION TEST")
    print("=" * 80)

    # Show configuration
    print("\nConfiguration:")
    print(f"  Spatial context enabled: {SpatialIntegrationConfig.is_enabled()}")
    print(f"  Proximity threshold: {SpatialIntegrationConfig.get_proximity_threshold()}")

    # Test detector creation
    print("\nCreating detector...")

    detector = create_detector()
    detector_type = type(detector).__name__

    print(f"  Detector type: {detector_type}")
    print(f"  Spatial support: {hasattr(detector, 'detect_pii_from_pdf')}")

    # Test with file if provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

        print(f"\nProcessing: {file_path}")

        result = detect_pii_with_spatial_support(file_path, depth="balanced")

        if result.get("status") == "error":
            print(f"Error: {result.get('error')}")
        else:
            print(f"\nResults:")
            print(f"  Entities detected: {len(result.get('entities', []))}")

            # Show spatial metadata if available
            if "spatial_context" in result.get("metadata", {}):
                spatial = result["metadata"]["spatial_context"]
                print(f"\nSpatial Context:")
                print(f"  Labels found: {spatial['labels_found']}")
                print(f"  Entities enriched: {spatial['entities_with_context']}")
                print(f"  Field types: {spatial['field_type_distribution']}")

            # Show sample entities
            entities = result.get("entities", [])
            if entities:
                print(f"\nSample entities (first 3):")
                for i, entity in enumerate(entities[:3], 1):
                    print(f"\n  {i}. {entity.get('text', 'N/A')}")
                    print(f"     Type: {entity.get('entity_type', 'N/A')}")
                    print(f"     Score: {entity.get('score', 0):.2f}")

                    # Show field context if available
                    if entity.get("field_context"):
                        fc = entity["field_context"]
                        print(f"     Field type: {fc.get('inferred_field_type', 'N/A')}")
                        print(f"     Label: {fc.get('nearby_label', 'N/A')}")
                        print(f"     Confidence: {fc.get('confidence', 0):.2f}")

    else:
        print("\nNo file provided. Usage: python spatial_integration.py <file_path>")

    print("\n" + "=" * 80)
    print("Environment Variables:")
    print("  ENABLE_SPATIAL_CONTEXT=1     # Enable spatial context")
    print("  ENABLE_SPATIAL_CONTEXT=0     # Disable spatial context")
    print("  SPATIAL_PROXIMITY_THRESHOLD=150  # Set proximity threshold")
    print("=" * 80)
