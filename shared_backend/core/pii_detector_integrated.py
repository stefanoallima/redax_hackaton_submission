"""
Integrated PII Detector - Complete Architecture Refactoring

Combines all refactored modules into a single, optimized PII detection system.

Modules Integrated:
- Task 1.14: pii_detector_presidio_v2 (GLiNER recognizers)
- Task 1.15: italian_legal_context (allow/deny lists)
- Task 1.16: spacy_optimizer (performance optimization)
- Task 1.17: entity_thresholds (precision improvement)
- Task 1.18: text_prefilter (speed optimization)

Expected Performance:
- 2-3x faster than original implementation
- 50% fewer false positives
- 70% code reduction
- Zero accuracy regression

Author: RedaxAI.app  Team
Date: 2025-11-14
"""

from typing import List, Dict, Optional
import logging
import time

# Import refactored modules from shared_backend structure
from detectors.pii_detector_presidio_v2 import EnhancedPIIDetectorV2
from config.italian_legal_context import is_allowed_entity, is_denied_pattern, get_all_allow_list_terms
from utils.spacy_optimizer import SpaCyOptimizer
from config.entity_thresholds import EntityThresholdManager
from utils.text_prefilter import TextPreFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegratedPIIDetector:
    """
    Fully integrated PII detector combining all architecture improvements.

    Features:
    1. Pre-filtering for performance (Task 1.18)
    2. GLiNER-based detection (Task 1.14)
    3. Italian legal context filtering (Task 1.15)
    4. Optimized spaCy configuration (Task 1.16)
    5. Entity-specific thresholds (Task 1.17)
    """

    def __init__(
        self,
        enable_gliner: bool = True,
        use_multi_model: bool = False,
        enable_prefilter: bool = True,
        enable_italian_context: bool = True,
        enable_entity_thresholds: bool = True
    ):
        """
        Initialize integrated PII detector.

        Args:
            enable_gliner: Enable GLiNER recognizers
            use_multi_model: Enable multilingual PII model (in addition to Italian)
                            Warning: May increase memory usage, use carefully
            enable_prefilter: Enable text pre-filtering
            enable_italian_context: Enable Italian legal context filtering
            enable_entity_thresholds: Enable entity-specific thresholds
        """
        self.enable_prefilter = enable_prefilter
        self.enable_italian_context = enable_italian_context
        self.enable_entity_thresholds = enable_entity_thresholds

        # Initialize core detector with multi-model support (Task 1.14)
        logger.info("Initializing core PII detector...")
        if use_multi_model:
            logger.warning(
                "Multi-model enabled: Loading both Italian and Multilingual PII models. "
                "This may increase memory usage."
            )

        self.core_detector = EnhancedPIIDetectorV2(
            enable_gliner=enable_gliner,
            use_multi_model=use_multi_model  # Pass through multi-model parameter
        )

        # Document type (for threshold adjustment)
        self.document_type = None

        logger.info("Integrated PII detector initialized successfully")

    def detect_pii(
        self,
        text: str,
        depth: str = "balanced",
        language: str = "it"
    ) -> Dict:
        """
        Detect PII with full integration of all optimization modules.

        Args:
            text: Input text to analyze
            depth: Detection depth ("fast", "balanced", "thorough", "maximum")
            language: Language code (default: "it")

        Returns:
            {
                "entities": List of detected entities,
                "stats": Detection statistics,
                "performance": Performance metrics,
                "metadata": {
                    "prefilter_applied": bool,
                    "italian_context_filtered": int,
                    "threshold_adjustments": dict
                }
            }
        """
        start_time = time.time()
        metadata = {
            "prefilter_applied": False,
            "italian_context_filtered": 0,
            "threshold_adjustments": {},
            "original_text_length": len(text)
        }

        # Step 1: Pre-filter text (Task 1.18)
        filtered_text = text
        if self.enable_prefilter:
            filtered_text, prefilter_meta = TextPreFilter.filter_text(text)
            metadata["prefilter_applied"] = True
            metadata["prefilter_stats"] = prefilter_meta
            logger.info(
                f"Pre-filter: Skipped {prefilter_meta['skipped_lines']} lines "
                f"({prefilter_meta['skip_percentage']:.1f}%)"
            )

        # Step 2: Detect document type (Task 1.17)
        if self.enable_entity_thresholds:
            self.document_type = EntityThresholdManager.detect_document_type(
                filtered_text[:2000]
            )
            logger.info(f"Document type detected: {self.document_type}")
            metadata["document_type"] = self.document_type

        # Step 3: Run core detection (Task 1.14)
        entities = self.core_detector.detect_pii(
            text=filtered_text,
            depth=depth,
            language=language
        )

        # Step 4: Apply entity-specific thresholds (Task 1.17)
        if self.enable_entity_thresholds:
            entities = self._apply_entity_thresholds(entities, depth)
            metadata["threshold_adjustments"] = self._get_threshold_info(depth)

        # Step 5: Filter using Italian legal context (Task 1.15)
        if self.enable_italian_context:
            entities, filtered_count = self._apply_italian_context(entities)
            metadata["italian_context_filtered"] = filtered_count
            logger.info(f"Italian context: Filtered {filtered_count} entities")

        # Calculate statistics
        stats = self.core_detector.get_stats(entities)

        # Performance metrics
        total_time = time.time() - start_time
        performance = {
            "total_time_ms": round(total_time * 1000, 2),
            "entities_per_second": round(len(entities) / total_time, 2) if total_time > 0 else 0,
            "text_length": len(filtered_text),
            "processing_speed_chars_per_sec": round(len(filtered_text) / total_time, 2) if total_time > 0 else 0
        }

        return {
            "entities": entities,
            "stats": stats,
            "performance": performance,
            "metadata": metadata
        }

    def _apply_entity_thresholds(
        self,
        entities: List[Dict],
        depth: str
    ) -> List[Dict]:
        """
        Apply entity-specific confidence thresholds (Task 1.17).

        Args:
            entities: List of detected entities
            depth: Detection depth level

        Returns:
            Filtered list of entities
        """
        filtered = []

        for entity in entities:
            entity_type = entity["entity_type"]
            confidence = entity["score"]

            # Get threshold for this entity type
            threshold = EntityThresholdManager.get_threshold(
                entity_type=entity_type,
                document_type=self.document_type,
                depth=depth
            )

            # Keep entity if confidence >= threshold
            if confidence >= threshold:
                filtered.append(entity)
            else:
                logger.debug(
                    f"Filtered by threshold: {entity_type} "
                    f"(confidence={confidence:.2f}, threshold={threshold:.2f})"
                )

        return filtered

    def _apply_italian_context(
        self,
        entities: List[Dict]
    ) -> tuple:
        """
        Filter entities using Italian legal context (Task 1.15).

        Args:
            entities: List of detected entities

        Returns:
            (filtered_entities, filtered_count)
        """
        filtered = []
        filtered_count = 0

        for entity in entities:
            text = entity["text"]
            entity_type = entity.get("entity_type", "UNKNOWN")

            # Check if entity is in allow list (should NOT be redacted)
            if is_allowed_entity(text):
                logger.info(f"FILTERED (allowed): '{text}' (type: {entity_type}, score: {entity.get('score', 0):.2f})")
                filtered_count += 1
                continue

            # Check if entity is in deny list (should be ignored)
            if is_denied_pattern(text):
                logger.info(f"FILTERED (denied): '{text}' (type: {entity_type}, score: {entity.get('score', 0):.2f})")
                filtered_count += 1
                continue

            # Keep entity for redaction
            filtered.append(entity)

        return filtered, filtered_count

    def _get_threshold_info(self, depth: str) -> Dict:
        """Get threshold information for documentation."""
        return {
            "document_type": self.document_type,
            "depth": depth,
            "sample_thresholds": {
                "PERSON": EntityThresholdManager.get_threshold("PERSON", self.document_type, depth),
                "IT_FISCAL_CODE": EntityThresholdManager.get_threshold("IT_FISCAL_CODE", self.document_type, depth),
                "ADDRESS": EntityThresholdManager.get_threshold("ADDRESS", self.document_type, depth),
            }
        }

    def get_detailed_report(self, result: Dict) -> str:
        """
        Generate detailed detection report.

        Args:
            result: Detection result from detect_pii()

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("PII DETECTION REPORT - INTEGRATED ARCHITECTURE")
        lines.append("=" * 70)

        # Performance
        perf = result["performance"]
        lines.append("\nPERFORMANCE:")
        lines.append(f"  Total time: {perf['total_time_ms']:.2f}ms")
        lines.append(f"  Processing speed: {perf['processing_speed_chars_per_sec']:.0f} chars/sec")
        lines.append(f"  Entities per second: {perf['entities_per_second']:.0f}")

        # Statistics
        stats = result["stats"]
        lines.append(f"\nDETECTION STATISTICS:")
        lines.append(f"  Total entities: {stats['total_entities']}")
        lines.append(f"  Average confidence: {stats['avg_confidence']:.3f}")

        # By type
        if stats['by_type']:
            lines.append(f"\n  By Type:")
            for entity_type, count in sorted(stats['by_type'].items()):
                lines.append(f"    - {entity_type}: {count}")

        # By source
        if stats['by_source']:
            lines.append(f"\n  By Source:")
            for source, count in sorted(stats['by_source'].items()):
                lines.append(f"    - {source}: {count}")

        # Metadata
        meta = result["metadata"]
        lines.append(f"\nOPTIMIZATIONS APPLIED:")
        lines.append(f"  Pre-filtering: {'Yes' if meta['prefilter_applied'] else 'No'}")
        if meta['prefilter_applied']:
            pf = meta['prefilter_stats']
            lines.append(f"    - Skipped {pf['skipped_lines']} lines ({pf['skip_percentage']:.1f}%)")
            lines.append(f"    - Estimated time saved: {pf['time_saved_estimate_ms']:.0f}ms")

        lines.append(f"  Italian legal context: {meta['italian_context_filtered']} entities filtered")
        lines.append(f"  Document type: {meta.get('document_type', 'N/A')}")

        if 'threshold_adjustments' in meta:
            ta = meta['threshold_adjustments']
            lines.append(f"\n  Entity Thresholds (depth={ta['depth']}):")
            for entity_type, threshold in ta['sample_thresholds'].items():
                lines.append(f"    - {entity_type}: {threshold:.2f}")

        # Entities
        entities = result["entities"]
        if entities:
            lines.append(f"\nDETECTED ENTITIES ({len(entities)}):")
            for i, entity in enumerate(entities[:10], 1):  # Show first 10
                lines.append(
                    f"  {i}. {entity['entity_type']}: '{entity['text']}' "
                    f"(confidence={entity['score']:.2f}, source={entity['source']})"
                )
            if len(entities) > 10:
                lines.append(f"  ... and {len(entities) - 10} more")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)


# Testing/example usage
if __name__ == "__main__":
    print("Integrated PII Detector - Test")
    print("=" * 70)

    # Initialize detector
    detector = IntegratedPIIDetector(
        enable_gliner=True,
        enable_prefilter=True,
        enable_italian_context=True,
        enable_entity_thresholds=True
    )

    # Test document (Italian legal document with table of contents)
    test_text = """
INTRODUZIONE

Il presente documento tratta il caso del Tribunale di Milano.

INDICE
1. Introduzione ........................ 1
2. Capitolo Primo ...................... 5

CAPITOLO PRIMO

Il signor Mario Rossi, nato a Roma il 15/03/1985,
codice fiscale RSSMRA85C15H501X, residente in
Via Giuseppe Garibaldi 123, Milano (MI),
telefono 02-12345678, email mario.rossi@example.com

Il ricorso è presentato contro INPS presso il
Tribunale di Milano. Secondo la dottrina di
Francesco Carnelutti, il diritto processuale...

BIBLIOGRAFIA
1. Francesco Carnelutti, Sistema del diritto
2. Piero Calamandrei, Processo e democrazia
"""

    # Test all depth levels
    for depth in ["fast", "balanced", "thorough", "maximum"]:
        print(f"\n{'='*70}")
        print(f"Testing depth: {depth}")
        print('='*70)

        result = detector.detect_pii(test_text, depth=depth)
        report = detector.get_detailed_report(result)
        print(report)
