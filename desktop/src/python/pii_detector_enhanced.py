"""
Enhanced PII Detection with GLiNER Multi-Model Support
Dual-model strategy: Italian-specific + Multilingual PII detection

⚠️ DEPRECATED: This is the old detector. Use IntegratedPIIDetector for better accuracy and performance.
📌 Set USE_NEW_PII_DETECTOR=true or use pii_detector_integrated.py for critical false positive fixes.
"""
from typing import List, Dict, Optional
import logging
from pii_detector import PIIDetector

logger = logging.getLogger(__name__)


class EnhancedPIIDetector:
    """
    Multi-layer PII detector with GLiNER models for Italian + multilingual support

    Detection Layers:
    - Layer 1: Presidio + spaCy (baseline, always active)
    - Layer 2: GLiNER Italian model (high precision for Italian entities)
    - Layer 3: GLiNER multilingual PII model (broad coverage + fallback)
    - Layer 4: Entity merging & deduplication

    Configuration via slider (detection depth):
    - fast: Presidio only (80-85% coverage)
    - balanced: Presidio + GLiNER Italian (88-92% coverage)
    - thorough: Presidio + both GLiNER models (92-96% coverage)
    - maximum: All models with lower thresholds (95-98% coverage)
    """

    # Italian PII entity labels for GLiNER
    ITALIAN_LABELS = [
        # Identity documents
        "persona", "person", "nome", "cognome",
        "codice fiscale", "fiscal code", "cf",
        "partita iva", "vat number", "p.iva",
        "carta identità", "identity card",
        "passaporto", "passport",
        "patente", "driver license",

        # Contact info
        "email", "posta elettronica", "pec",
        "telefono", "phone number", "cellulare", "tel",
        "indirizzo", "address", "via", "residenza",

        # Financial
        "iban", "conto bancario", "bank account",
        "carta credito", "credit card",
        "codice bancario", "bic", "swift",

        # Dates and locations
        "data nascita", "date of birth", "nato",
        "luogo nascita", "place of birth",
        "città", "city", "comune", "provincia",

        # Professional
        "datore lavoro", "employer", "azienda", "società",
        "stipendio", "salary", "retribuzione",

        # Medical (sensitive)
        "diagnosi", "diagnosis", "terapia", "treatment",
        "paziente", "patient", "medico", "doctor",

        # Legal
        "avvocato", "lawyer", "giudice", "judge",
        "sentenza", "verdict", "tribunale", "court"
    ]

    # Multilingual PII labels (universal)
    MULTILINGUAL_LABELS = [
        "person", "email", "phone number", "address",
        "date", "organization", "location",
        "passport number", "driver license", "national id",
        "bank account", "credit card", "iban",
        "social security number", "tax id"
    ]

    def __init__(self, enable_gliner: bool = True):
        """
        Initialize enhanced detector

        Args:
            enable_gliner: If False, falls back to Presidio-only detection
        """
        # Layer 1: Presidio baseline (always active)
        self.presidio_detector = PIIDetector()
        logger.info("Layer 1: Presidio detector initialized")

        # Layers 2 & 3: GLiNER models (lazy loading)
        self.gliner_italian = None
        self.gliner_multilingual = None
        self.enable_gliner = enable_gliner

        if enable_gliner:
            try:
                self._initialize_gliner_models()
            except Exception as e:
                logger.error(f"GLiNER initialization failed: {e}")
                logger.warning("Falling back to Presidio-only detection")
                self.enable_gliner = False

    def _initialize_gliner_models(self):
        """
        Lazy-load GLiNER models (only when enabled)

        Models:
        - Italian-specific: DeepMount00/universal_ner_ita
        - Multilingual PII: urchade/gliner_multi_pii-v1
        """
        try:
            from gliner import GLiNER

            # Layer 2: Italian-specific model
            logger.info("Loading GLiNER Italian model...")
            self.gliner_italian = GLiNER.from_pretrained("DeepMount00/universal_ner_ita")
            logger.info("✓ GLiNER Italian model loaded")

            # Layer 3: Multilingual PII model
            logger.info("Loading GLiNER multilingual PII model...")
            self.gliner_multilingual = GLiNER.from_pretrained("urchade/gliner_multi_pii-v1")
            logger.info("✓ GLiNER multilingual PII model loaded")

            logger.info("All GLiNER models initialized successfully")

        except ImportError:
            raise ImportError(
                "GLiNER not installed. Install with: pip install gliner psutil onnxruntime"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load GLiNER models: {e}")

    def _get_threshold_for_depth(self, depth: str, model_type: str) -> float:
        """
        Map detection depth to confidence threshold

        Args:
            depth: Detection depth level (fast/balanced/thorough/maximum)
            model_type: 'italian' or 'multilingual'

        Returns:
            Confidence threshold (0.0-1.0)
        """
        # Threshold matrix: depth × model type
        thresholds = {
            'fast': {
                'italian': None,      # Not used in fast mode
                'multilingual': None  # Not used in fast mode
            },
            'balanced': {
                'italian': 0.6,       # High precision
                'multilingual': None  # Not used in balanced mode
            },
            'thorough': {
                'italian': 0.5,       # Balanced
                'multilingual': 0.6   # Selective coverage
            },
            'maximum': {
                'italian': 0.4,       # High recall
                'multilingual': 0.5   # Broad coverage
            }
        }

        return thresholds.get(depth, {}).get(model_type)

    def _should_use_model(self, depth: str, model_type: str) -> bool:
        """
        Determine if a specific GLiNER model should be used based on depth

        Args:
            depth: Detection depth level
            model_type: 'italian' or 'multilingual'

        Returns:
            True if model should be active
        """
        if not self.enable_gliner:
            return False

        threshold = self._get_threshold_for_depth(depth, model_type)
        return threshold is not None

    def _detect_with_gliner(
        self,
        text: str,
        model,
        labels: List[str],
        threshold: float,
        source: str
    ) -> List[Dict]:
        """
        Run GLiNER detection on text

        Args:
            text: Input text
            model: GLiNER model instance
            labels: Entity labels to detect
            threshold: Confidence threshold
            source: Model identifier (for tracking)

        Returns:
            List of detected entities
        """
        try:
            # Run GLiNER prediction
            gliner_entities = model.predict_entities(text, labels, threshold=threshold)

            # Convert to our standard format
            entities = []
            for entity in gliner_entities:
                # Find entity position in text (GLiNER doesn't return indices)
                start_idx = text.find(entity['text'])
                if start_idx == -1:
                    continue  # Entity not found in text (shouldn't happen)

                entities.append({
                    "entity_type": self._normalize_entity_type(entity['label']),
                    "text": entity['text'],
                    "start": start_idx,
                    "end": start_idx + len(entity['text']),
                    "score": entity['score'],
                    "source": source  # Track which model detected it
                })

            logger.info(f"{source}: Detected {len(entities)} entities (threshold={threshold})")
            return entities

        except Exception as e:
            logger.error(f"Error in {source} detection: {e}")
            return []

    def _normalize_entity_type(self, label: str) -> str:
        """
        Normalize GLiNER labels to match Presidio entity types

        Args:
            label: GLiNER entity label

        Returns:
            Normalized entity type
        """
        # Mapping: GLiNER label → Presidio entity type
        label_lower = label.lower()

        mappings = {
            # Italian → Standard
            'persona': 'PERSON',
            'nome': 'PERSON',
            'cognome': 'PERSON',
            'codice fiscale': 'IT_FISCAL_CODE',
            'fiscal code': 'IT_FISCAL_CODE',
            'cf': 'IT_FISCAL_CODE',
            'partita iva': 'IT_VAT_CODE',
            'p.iva': 'IT_VAT_CODE',
            'vat number': 'IT_VAT_CODE',
            'telefono': 'PHONE_NUMBER',
            'cellulare': 'PHONE_NUMBER',
            'tel': 'PHONE_NUMBER',
            'indirizzo': 'IT_ADDRESS',
            'via': 'IT_ADDRESS',
            'residenza': 'IT_ADDRESS',
            'email': 'EMAIL_ADDRESS',
            'posta elettronica': 'EMAIL_ADDRESS',
            'pec': 'EMAIL_ADDRESS',
            'iban': 'IBAN',
            'conto bancario': 'IBAN',
            'bank account': 'IBAN',
            'passaporto': 'IT_PASSPORT',
            'patente': 'IT_DRIVER_LICENSE',
            'carta identità': 'IT_IDENTITY_CARD',

            # Universal
            'person': 'PERSON',
            'phone number': 'PHONE_NUMBER',
            'address': 'IT_ADDRESS',
            'date': 'DATE_TIME',
            'location': 'LOCATION',
            'organization': 'ORGANIZATION',
            'date of birth': 'DATE_TIME'
        }

        # Return mapped type or original (prefixed with GLINER_)
        return mappings.get(label_lower, f"GLINER_{label.upper().replace(' ', '_')}")

    def _merge_entities(self, *entity_lists: List[Dict]) -> List[Dict]:
        """
        Merge entities from multiple detectors and remove duplicates

        Strategy:
        1. Keep all entities from all sources
        2. Remove exact duplicates (same text + position)
        3. For overlapping entities, keep higher confidence score

        Args:
            *entity_lists: Variable number of entity lists

        Returns:
            Merged and deduplicated entity list
        """
        # Flatten all entity lists
        all_entities = []
        for entities in entity_lists:
            all_entities.extend(entities)

        if not all_entities:
            return []

        # Sort by start position for easier overlap detection
        all_entities.sort(key=lambda e: e['start'])

        # Remove duplicates and overlaps
        merged = []
        for entity in all_entities:
            # Check if this entity overlaps with any already-merged entity
            overlaps = False
            for i, existing in enumerate(merged):
                # Check for overlap
                if self._entities_overlap(entity, existing):
                    overlaps = True
                    # Keep entity with higher confidence
                    if entity['score'] > existing['score']:
                        merged[i] = entity
                    break

            if not overlaps:
                merged.append(entity)

        # Sort by position again
        merged.sort(key=lambda e: e['start'])

        logger.info(f"Merged {len(all_entities)} entities → {len(merged)} unique entities")
        return merged

    def _entities_overlap(self, entity1: Dict, entity2: Dict) -> bool:
        """
        Check if two entities overlap

        Args:
            entity1, entity2: Entity dicts with start/end positions

        Returns:
            True if entities overlap
        """
        # Check if ranges overlap
        return not (entity1['end'] <= entity2['start'] or entity2['end'] <= entity1['start'])

    def detect_pii(
        self,
        text: str,
        depth: str = 'balanced',
        language: str = 'it'
    ) -> List[Dict]:
        """
        Detect PII using multi-model strategy

        Args:
            text: Input text
            depth: Detection depth (fast/balanced/thorough/maximum)
            language: Language code (default: 'it')

        Returns:
            List of detected PII entities
        """
        logger.info(f"Starting PII detection (depth={depth}, language={language})")

        # Layer 1: ALWAYS run Presidio (baseline)
        logger.info("Layer 1: Running Presidio detection...")
        presidio_entities = self.presidio_detector.detect_pii(text, language=language)
        logger.info(f"Layer 1: Found {len(presidio_entities)} entities")

        # Initialize entity lists
        entity_lists = [presidio_entities]

        # Layer 2: GLiNER Italian model (if enabled for this depth)
        if self._should_use_model(depth, 'italian'):
            threshold = self._get_threshold_for_depth(depth, 'italian')
            logger.info(f"Layer 2: Running GLiNER Italian detection (threshold={threshold})...")

            italian_entities = self._detect_with_gliner(
                text=text,
                model=self.gliner_italian,
                labels=self.ITALIAN_LABELS,
                threshold=threshold,
                source="gliner_italian"
            )
            entity_lists.append(italian_entities)
        else:
            logger.info("Layer 2: GLiNER Italian disabled for this depth")

        # Layer 3: GLiNER multilingual PII model (if enabled for this depth)
        if self._should_use_model(depth, 'multilingual'):
            threshold = self._get_threshold_for_depth(depth, 'multilingual')
            logger.info(f"Layer 3: Running GLiNER multilingual detection (threshold={threshold})...")

            multilingual_entities = self._detect_with_gliner(
                text=text,
                model=self.gliner_multilingual,
                labels=self.MULTILINGUAL_LABELS,
                threshold=threshold,
                source="gliner_multilingual"
            )
            entity_lists.append(multilingual_entities)
        else:
            logger.info("Layer 3: GLiNER multilingual disabled for this depth")

        # Layer 4: Merge and deduplicate
        logger.info("Layer 4: Merging entities from all sources...")
        merged_entities = self._merge_entities(*entity_lists)

        # Generate detection summary
        summary = self._generate_summary(merged_entities)
        logger.info(f"Detection complete: {len(merged_entities)} total entities")
        logger.info(f"Summary by source: {summary}")

        return merged_entities

    def _generate_summary(self, entities: List[Dict]) -> Dict:
        """
        Generate summary of detected entities by source

        Args:
            entities: List of detected entities

        Returns:
            Summary dict with counts by source
        """
        summary = {}
        for entity in entities:
            source = entity.get('source', 'unknown')
            summary[source] = summary.get(source, 0) + 1
        return summary

    def process_document(self, document_data: Dict, config = None) -> Dict:
        """
        Process document with enhanced multi-model detection

        Args:
            document_data: Output from DocumentProcessor
            config: Detection configuration (dict with 'depth' or DetectionConfig object)

        Returns:
            Document with PII entities detected
        """
        try:
            # Handle both dict and DetectionConfig object
            if config is None:
                depth = 'balanced'
            elif isinstance(config, dict):
                depth = config.get('depth', 'balanced')
            else:
                # Assume it's a DetectionConfig object with .depth attribute
                depth = getattr(config, 'depth', 'balanced')
            full_text = document_data.get("full_text", "")

            # Run enhanced detection
            entities = self.detect_pii(full_text, depth=depth)

            # Group entities by type
            entity_summary = {}
            for entity in entities:
                entity_type = entity["entity_type"]
                entity_summary[entity_type] = entity_summary.get(entity_type, 0) + 1

            # Group entities by source
            source_summary = self._generate_summary(entities)

            return {
                "status": "success",
                "entities": entities,
                "entity_summary": entity_summary,
                "source_summary": source_summary,
                "total_entities": len(entities),
                "document_data": document_data,
                "detection_config": {
                    "depth": depth,
                    "gliner_enabled": self.enable_gliner,
                    "models_used": list(source_summary.keys())
                }
            }

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def get_entity_locations(self, file_path: str, entities: List[Dict]) -> List[Dict]:
        """
        Find PDF page coordinates for each entity

        This method delegates to the base PIIDetector's implementation

        Args:
            file_path: Path to PDF file
            entities: List of detected entities

        Returns:
            Same entities with added 'locations' field containing page coordinates
        """
        # Delegate to base PIIDetector implementation
        return self.presidio_detector.get_entity_locations(file_path, entities)


# Example usage
if __name__ == "__main__":
    # Initialize enhanced detector
    detector = EnhancedPIIDetector(enable_gliner=True)

    # Test text (Italian legal document excerpt)
    text = """
    CONTRATTO DI LAVORO

    Il signor Mario Rossi, nato il 15/03/1985 a Roma, residente in Via Mura Anteo Zamboni 22, 40126 Bologna (BO).
    Codice Fiscale: RSSMRA85C15H501X
    Partita IVA: 12345678901

    Contatti:
    Telefono: +39 333 1234567
    Email: mario.rossi@example.com
    PEC: mario.rossi@pec.example.it

    Dati bancari:
    IBAN: IT60 X054 2811 1010 0000 0123 456
    """

    # Test with different depth levels
    for depth in ['fast', 'balanced', 'thorough', 'maximum']:
        print(f"\n{'='*60}")
        print(f"Testing depth: {depth}")
        print('='*60)

        entities = detector.detect_pii(text, depth=depth)

        print(f"\nDetected {len(entities)} entities:")
        for entity in entities:
            print(f"  [{entity['entity_type']}] {entity['text']} "
                  f"(score: {entity['score']:.2f}, source: {entity.get('source', 'N/A')})")
