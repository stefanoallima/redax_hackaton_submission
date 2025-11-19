"""
PII Detection using Microsoft Presidio
Italian legal document support with multi-layer detection

ARCHITECTURAL NOTE - Presidio Usage:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Presidio Analyzer: Used for PII DETECTION (this file)
❌ Presidio Anonymizer: NOT used for PDF redaction

PDF Redaction: Uses custom RedactionExporter class (redaction_exporter.py)
  - Preserves document layout with same-length placeholders
  - Visual black-box redaction using PyMuPDF
  - Safety checks for invisible text and already-redacted content
  - Generates mapping table CSV for audit trail

Text Anonymization: anonymize_text() method (line 361) uses Presidio Anonymizer
  - Only for .txt file export (optional feature)
  - Not used in main PDF workflow

See: PRESIDIO_ANONYMIZATION_ANALYSIS.md for detailed comparison
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import (
    ItFiscalCodeRecognizer,
    ItDriverLicenseRecognizer,
    ItIdentityCardRecognizer,
    ItPassportRecognizer,
    ItVatCodeRecognizer
)
from presidio_anonymizer import AnonymizerEngine
from typing import List, Dict, Optional
import re
import logging

logger = logging.getLogger(__name__)


class IBANRecognizer(PatternRecognizer):
    """
    Recognizer for Italian IBAN
    Format: IT + 2 check digits + 23 alphanumeric characters
    Handles spaces, dashes, and continuous formats
    Examples:
    - IT60 X054 2811 1010 0000 0123 456
    - IT60X0542811101000000123456
    - IT60-X054-2811-1010-0000-0123-456
    """
    
    PATTERNS = [
        # IBAN with spaces (most common format)
        Pattern(
            name="iban_italy_spaced",
            regex=r"\bIT\s?[0-9]{2}\s?[A-Z0-9\s-]{23,30}\b",
            score=0.90
        ),
        # IBAN continuous (no spaces)
        Pattern(
            name="iban_italy_continuous",
            regex=r"\bIT[0-9]{2}[A-Z0-9]{23}\b",
            score=0.95
        )
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="IBAN",
            patterns=self.PATTERNS,
            context=["iban", "conto", "bancario", "banca"],
            supported_language="it"
        )


class ItalianPhoneRecognizer(PatternRecognizer):
    """
    Recognizer for Italian phone numbers
    Matches various formats: +39, 0039, landline, mobile
    """
    
    PATTERNS = [
        # Mobile: +39 3xx xxx xxxx
        Pattern(
            name="mobile_intl",
            regex=r"\+39\s?3[0-9]{2}\s?[0-9]{3}\s?[0-9]{4}",
            score=0.85
        ),
        # Mobile without +39
        Pattern(
            name="mobile_local",
            regex=r"\b3[0-9]{2}\s?[0-9]{3}\s?[0-9]{4}\b",
            score=0.75
        ),
        # Landline: 0x(x)
        Pattern(
            name="landline",
            regex=r"\b0[0-9]{1,3}\s?[0-9]{6,7}\b",
            score=0.70
        )
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="PHONE_NUMBER",
            patterns=self.PATTERNS,
            context=["telefono", "tel", "cell", "cellulare", "mobile"],
            supported_language="it"
        )


class ItalianAddressRecognizer(PatternRecognizer):
    """
    Recognizer for Italian addresses
    Matches street patterns common in Italy with various formats
    """

    PATTERNS = [
        # Format: "22 Via Mura Anteo Zamboni, 40126" (number BEFORE street name)
        Pattern(
            name="via_pattern_number_first",
            regex=r"\b\d{1,4}\s+(Via|Viale|Piazza|Corso|Largo|Vicolo|V\.le|P\.za|C\.so)\s+[A-Za-z][A-Za-z\s,\.'-]{3,50}(?:,?\s*\d{5})?",
            score=0.85
        ),
        # Format: "Via Roma 123" (street name first, number after)
        Pattern(
            name="via_pattern_number_after",
            regex=r"\b(Via|Viale|Piazza|Corso|Largo|Vicolo|V\.le|P\.za|C\.so)\s+[A-Za-z][A-Za-z\s,\.'-]{2,40}\s+\d{1,4}[a-zA-Z]?",
            score=0.82
        ),
        # Format: "Via Roma, 123" (with comma)
        Pattern(
            name="via_pattern_comma",
            regex=r"\b(Via|Viale|Piazza|Corso|Largo|Vicolo|V\.le|P\.za|C\.so)\s+[A-Za-z][A-Za-z\s\.'-]{2,40},\s*\d{1,4}[a-zA-Z]?",
            score=0.82
        ),
        # Format: "40126 Bologna (BO)" or "00100 Roma (RM)" (CAP + City)
        Pattern(
            name="cap_city_pattern",
            regex=r"\b[0-9]{5}\s+[A-Z][a-zA-Z\s]{2,30}\s*\([A-Z]{2}\)",
            score=0.80
        ),
        # Full address with CAP: "Via Roma 123, 00100 Roma"
        Pattern(
            name="full_address_with_cap",
            regex=r"\b(Via|Viale|Piazza|Corso|Largo|Vicolo)\s+[A-Za-z][A-Za-z\s\.'-]{2,40}\s+\d{1,4}[a-zA-Z]?,\s*\d{5}",
            score=0.88
        )
    ]

    def __init__(self):
        super().__init__(
            supported_entity="IT_ADDRESS",
            patterns=self.PATTERNS,
            context=["residente", "indirizzo", "domicilio", "via", "piazza", "sede", "nato", "nata"],
            supported_language="it"
        )


class USSocialSecurityRecognizer(PatternRecognizer):
    """
    Recognizer for US Social Security Numbers (SSN)
    Format: XXX-XX-XXXX or XXXXXXXXX
    Examples:
    - 123-45-6789
    - 123456789
    - 987-65-4321
    """

    PATTERNS = [
        # SSN with dashes (most common format)
        Pattern(
            name="ssn_dashed",
            regex=r"\b\d{3}-\d{2}-\d{4}\b",
            score=0.95
        ),
        # SSN continuous (no dashes)
        Pattern(
            name="ssn_continuous",
            regex=r"\b\d{9}\b",
            score=0.70  # Lower score as 9 digits could be other things
        )
    ]

    def __init__(self):
        super().__init__(
            supported_entity="US_SSN",
            patterns=self.PATTERNS,
            context=["ssn", "social security", "social security number", "ss#"],
            supported_language="en"
        )


class PIIDetector:
    """
    Main PII Detection Engine with Italian support
    """

    # Common false-positive words that are often detected as PERSON
    PERSON_BLACKLIST = {
        # Document types
        'PDF', 'DOC', 'DOCX', 'TXT', 'CV', 'CURRICULUM', 'VITAE',
        # Titles and sections
        'TITOLO', 'OGGETTO', 'DATA', 'LUOGO', 'FIRMA', 'ALLEGATO', 'ALLEGATI',
        'COMPETENZE', 'ESPERIENZE', 'FORMAZIONE', 'OBIETTIVI', 'PROFILO',
        'LAVORO', 'ISTRUZIONE', 'CERTIFICAZIONI', 'LINGUE', 'PROGETTI',
        'RIFERIMENTI', 'CONTATTI', 'SKILLS', 'EDUCATION', 'EXPERIENCE',
        'SUMMARY', 'OBJECTIVE', 'PROFILE', 'LANGUAGES', 'REFERENCES',
        # Professional terms
        'IT', 'HR', 'CEO', 'CFO', 'CTO', 'COO', 'CIO', 'PM', 'BA', 'QA',
        'MANAGER', 'SENIOR', 'JUNIOR', 'LEAD', 'TEAM', 'HEAD', 'DIRECTOR',
        # Legal terms
        'ART', 'ARTT', 'DPR', 'DLGS', 'DECRETO', 'LEGGE',
        # Common abbreviations
        'ECC', 'ECO', 'SIG', 'DOTT', 'AVV', 'ING', 'PROF', 'GEOM', 'ARCH',
        'DR', 'MR', 'MS', 'MRS', 'ING', 'DOTT', 'DOTTOR', 'DOTTORE',
        # Time/dates
        'ANNO', 'MESE', 'GIORNO', 'OGGI', 'IERI', 'DOMANI',
        # Misc
        'SI', 'NO', 'OK', 'KO', 'MAIL', 'FAX', 'TEL', 'CAP',
        'INFO', 'NOTE', 'NB', 'PS', 'REF', 'ATT', 'ATTN',
        # Common proper case words (not names)
        'ITALIA', 'ROMA', 'MILANO', 'TORINO',  # Cities (these should be LOCATION not PERSON)
        'INGLESE', 'ITALIANO', 'SPAGNOLO', 'FRANCESE', 'TEDESCO'  # Languages
    }

    def __init__(self):
        """Initialize Presidio with Italian recognizers (built-in + custom)"""

        # Set up NLP engine with Italian support
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "it", "model_name": "it_core_news_lg"}]
        }

        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()

        # Create registry and load default recognizers
        # Load recognizers from nlp_engine without specifying languages to avoid mismatch
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)

        # Add Presidio's Italian recognizers explicitly
        # (These have checksum validation for better accuracy)
        registry.add_recognizer(ItFiscalCodeRecognizer())
        registry.add_recognizer(ItDriverLicenseRecognizer())
        registry.add_recognizer(ItIdentityCardRecognizer())
        registry.add_recognizer(ItPassportRecognizer())
        registry.add_recognizer(ItVatCodeRecognizer())

        # Add custom recognizers (not in Presidio)
        registry.add_recognizer(IBANRecognizer())
        registry.add_recognizer(ItalianPhoneRecognizer())
        registry.add_recognizer(ItalianAddressRecognizer())
        registry.add_recognizer(USSocialSecurityRecognizer())

        # Initialize analyzer
        # Let the analyzer auto-detect supported languages from registry and nlp_engine
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry
        )

        # Initialize anonymizer
        self.anonymizer = AnonymizerEngine()

        logger.info("PII Detector initialized with Italian support (Presidio + custom recognizers)")

    def _is_likely_name(self, text: str) -> bool:
        """
        Check if text is likely a real person name

        Args:
            text: Text to check

        Returns:
            True if likely a name, False otherwise
        """
        words = text.split()

        # Multi-word names in all-caps are likely real names (e.g., "MARIO ROSSI")
        if len(words) >= 2 and text.isupper():
            # Check if each word is at least 2 chars and alphabetic
            return all(len(w) >= 2 and w.isalpha() for w in words)

        # Single word: check if it looks like a surname or given name
        if len(words) == 1:
            # All-caps single words > 4 chars might be names (e.g., "ROSSI", "MARIO")
            if text.isupper() and len(text) > 4 and text.isalpha():
                return True

            # Proper case names are likely valid (e.g., "Mario", "Rossi")
            if text[0].isupper() and text[1:].islower() and len(text) >= 3:
                return True

        return False

    def _filter_person_false_positives(self, entity: Dict) -> bool:
        """
        Filter out common false positives for PERSON entities

        Args:
            entity: Entity dict with entity_type, text, start, end, score

        Returns:
            True if entity should be kept, False if it's a false positive
        """
        if entity["entity_type"] != "PERSON":
            return True  # Keep non-PERSON entities

        text = entity["text"].strip()

        # Rule 1: Filter blacklisted words (document terms, abbreviations, etc.)
        if text.upper() in self.PERSON_BLACKLIST:
            logger.debug(f"Filtered blacklisted word: {text}")
            return False

        # Rule 2: Filter very short all-caps words (3 chars or less - likely acronyms)
        if text.isupper() and len(text) <= 3:
            logger.debug(f"Filtered short all-caps word (acronym): {text}")
            return False

        # Rule 3: Check if it's a likely name
        if self._is_likely_name(text):
            # It's likely a real name, keep it
            logger.debug(f"Keeping likely name: {text}")
            return True

        # Rule 4: Filter single all-caps words that are short and not name-like
        words = text.split()
        if len(words) == 1 and text.isupper() and len(text) <= 4:
            logger.debug(f"Filtered short single all-caps word: {text}")
            return False

        # Rule 5: Check for common proper-case false positives
        # Words that start with uppercase but aren't likely names
        if len(words) == 1 and len(text) >= 3:
            # Check against common section headers and terms
            common_terms = {
                'Competenze', 'Esperienze', 'Formazione', 'Obiettivi', 'Profilo',
                'Lavoro', 'Istruzione', 'Certificazioni', 'Lingue', 'Progetti',
                'Curriculum', 'Riferimenti', 'Contatti', 'Skills', 'Education',
                'Experience', 'Summary', 'Objective', 'Profile', 'Languages'
            }
            if text in common_terms:
                logger.debug(f"Filtered common header term: {text}")
                return False

        return True
    
    def detect_pii(self, text: str, language: str = "it") -> List[Dict]:
        """
        Detect PII entities in text
        
        Args:
            text: Input text
            language: Language code (default: 'it')
            
        Returns:
            List of detected PII entities with scores
        """
        try:
            # Analyze text with all Italian entity types
            results = self.analyzer.analyze(
                text=text,
                language=language,
                entities=[
                    # Standard entities
                    "PERSON",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "DATE_TIME",
                    "LOCATION",

                    # Italian-specific (Presidio built-in with checksum validation)
                    "IT_FISCAL_CODE",      # Codice Fiscale (replaces CODICE_FISCALE)
                    "IT_DRIVER_LICENSE",   # Patente di guida
                    "IT_IDENTITY_CARD",    # Carta d'identità
                    "IT_PASSPORT",         # Passaporto
                    "IT_VAT_CODE",         # Partita IVA (with checksum)

                    # Custom recognizers
                    "IBAN",                # Italian IBAN
                    "IT_ADDRESS"           # Italian addresses
                ]
            )
            
            # Convert to serializable format
            entities = []
            for result in results:
                entity = {
                    "entity_type": result.entity_type,
                    "text": text[result.start:result.end],
                    "start": result.start,
                    "end": result.end,
                    "score": result.score
                }
                entities.append(entity)

            # Filter false positives (especially for PERSON entities)
            filtered_entities = [e for e in entities if self._filter_person_false_positives(e)]

            filtered_count = len(entities) - len(filtered_entities)
            if filtered_count > 0:
                logger.info(f"Filtered {filtered_count} false positive entities")

            logger.info(f"Detected {len(filtered_entities)} PII entities")
            return filtered_entities
            
        except Exception as e:
            logger.error(f"Error detecting PII: {e}")
            return []
    
    def anonymize_text(self, text: str, entities: List[Dict]) -> Dict:
        """
        Anonymize text by replacing PII with placeholders
        
        Args:
            text: Original text
            entities: List of PII entities from detect_pii()
            
        Returns:
            dict with status and anonymized_text
        """
        try:
            # Convert entities back to Presidio format
            from presidio_analyzer import RecognizerResult
            
            recognizer_results = [
                RecognizerResult(
                    entity_type=e["entity_type"],
                    start=e["start"],
                    end=e["end"],
                    score=e["score"]
                )
                for e in entities
            ]
            
            # Anonymize
            result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=recognizer_results
            )
            
            return {
                "status": "success",
                "anonymized_text": result.text,
                "entities_anonymized": len(entities)
            }
            
        except Exception as e:
            logger.error(f"Error anonymizing text: {e}")
            return {
                "status": "error",
                "error": str(e),
                "anonymized_text": text
            }
    
    def detect_and_anonymize(self, text: str) -> Dict:
        """
        Detect PII and return both entities and anonymized text
        
        Args:
            text: Input text
            
        Returns:
            dict with entities and anonymized_text
        """
        entities = self.detect_pii(text)
        anonymized = self.anonymize_text(text, entities)
        
        return {
            "original_text": text,
            "entities": entities,
            "anonymized_text": anonymized,
            "entity_count": len(entities)
        }
    
    def get_entity_locations(self, file_path: str, entities: List[Dict]) -> List[Dict]:
        """
        Find PDF page coordinates for each entity with improved fuzzy matching

        Args:
            file_path: Path to PDF file
            entities: List of detected entities

        Returns:
            Same entities with added 'locations' field containing page coordinates
        """
        try:
            import fitz  # PyMuPDF
            import re

            logger.info(f"Finding entity locations in PDF: {file_path}")
            doc = fitz.open(file_path)

            # For each entity, find its location on PDF pages
            for entity in entities:
                entity['locations'] = []
                entity_text = entity['text']

                # Search all pages for this entity text
                for page_num in range(len(doc)):
                    page = doc[page_num]

                    # Strategy 1: Exact match
                    text_instances = page.search_for(entity_text)

                    # Strategy 2: If no exact match, try normalized search
                    if not text_instances:
                        # Normalize: remove extra whitespace and newlines
                        normalized_text = re.sub(r'\s+', ' ', entity_text).strip()
                        if normalized_text != entity_text:
                            text_instances = page.search_for(normalized_text)

                    # Strategy 3: If still no match, try case-insensitive
                    if not text_instances:
                        # Try all variations: lowercase, uppercase, title case
                        for variant in [entity_text.lower(), entity_text.upper(), entity_text.title()]:
                            text_instances = page.search_for(variant)
                            if text_instances:
                                break

                    # Strategy 4: Try searching for first/last words if multi-word
                    if not text_instances and ' ' in normalized_text:
                        words = normalized_text.split()
                        if len(words) >= 2:
                            # Try first word + last word pattern
                            first_word_instances = page.search_for(words[0])
                            last_word_instances = page.search_for(words[-1])

                            # If we find both words on same line, approximate the rect
                            if first_word_instances and last_word_instances:
                                for first_rect in first_word_instances:
                                    for last_rect in last_word_instances:
                                        # Check if on same approximate vertical position (same line)
                                        if abs(first_rect.y0 - last_rect.y0) < 5:
                                            # Combine rects
                                            combined_rect = fitz.Rect(
                                                min(first_rect.x0, last_rect.x0),
                                                min(first_rect.y0, last_rect.y0),
                                                max(first_rect.x1, last_rect.x1),
                                                max(first_rect.y1, last_rect.y1)
                                            )
                                            text_instances = [combined_rect]
                                            logger.debug(f"Found '{entity_text}' using word boundary matching")
                                            break

                    for rect in text_instances:
                        entity['locations'].append({
                            'page': page_num + 1,  # Store as 1-based page number for consistency with redaction_exporter
                            'rect': {
                                'x0': float(rect.x0),
                                'y0': float(rect.y0),
                                'x1': float(rect.x1),
                                'y1': float(rect.y1)
                            }
                        })

                # Log if entity not found on any page
                if not entity['locations']:
                    logger.warning(f"Entity '{entity['text'][:50]}...' not found on any PDF page (may need better fuzzy matching)")

            doc.close()

            # Filter out entities without valid locations (hidden/invisible text)
            entities_with_locations = [e for e in entities if e['locations']]
            filtered_count = len(entities) - len(entities_with_locations)

            if filtered_count > 0:
                logger.info(f"Filtered {filtered_count} entities without visible locations (hidden text)")

            logger.info(f"Found locations for {len(entities_with_locations)} visible entities")
            return entities_with_locations

        except Exception as e:
            logger.error(f"Error getting entity locations: {e}")
            # Return entities without locations (fallback to text preview)
            for entity in entities:
                entity['locations'] = []
            return entities

    def process_document(self, document_data: Dict, config: Optional['DetectionConfig'] = None) -> Dict:
        """
        Process document with configurable detection layers

        Args:
            document_data: Output from DocumentProcessor
            config: Detection configuration (depth, LLM, visual settings)

        Returns:
            Document with PII entities detected according to config
        """
        try:
            # Import here to avoid circular dependency
            from detection_config import DetectionConfig

            if config is None:
                config = DetectionConfig()  # Use default (balanced)
                logger.info("No config provided, using default (balanced)")

            full_text = document_data.get("full_text", "")

            # Layer 1: ALWAYS run regex detection (baseline - never skip!)
            logger.info(f"Layer 1: Running Presidio/regex detection (depth={config.depth})")
            entities = self.detect_pii(full_text)
            logger.info(f"Layer 1 complete: Found {len(entities)} entities")

            # Layer 2: LLM validation (if enabled and conditions met)
            if config.enable_llm and config.depth != 'fast':
                # Check if we should use LLM based on config
                should_use_llm = config.should_use_llm(full_text, is_priority_page=True)

                if should_use_llm:
                    logger.info("Layer 2: LLM validation would run here (not yet implemented)")
                    # TODO: Implement LLM validation
                    # entities = self._enhance_with_llm(entities, full_text, config)
                else:
                    logger.info("Layer 2: Skipping LLM (no keywords/priority indicators)")
            else:
                logger.info(f"Layer 2: LLM disabled (enable_llm={config.enable_llm}, depth={config.depth})")

            # Layer 3: Visual detection (if enabled and conditions met)
            if config.enable_visual and config.depth in ['thorough', 'maximum']:
                logger.info("Layer 3: Visual detection would run here (not yet implemented)")
                # TODO: Implement visual detection
                # entities = self._enhance_with_visual(entities, document_data, config)
            else:
                logger.info(f"Layer 3: Visual disabled (enable_visual={config.enable_visual}, depth={config.depth})")

            # Group entities by type
            entity_summary = {}
            for entity in entities:
                entity_type = entity["entity_type"]
                entity_summary[entity_type] = entity_summary.get(entity_type, 0) + 1

            return {
                "status": "success",
                "entities": entities,
                "entity_summary": entity_summary,
                "total_entities": len(entities),
                "document_data": document_data,
                "detection_config": {
                    "depth": config.depth,
                    "llm_enabled": config.enable_llm,
                    "visual_enabled": config.enable_visual
                }
            }

        except Exception as e:
            logger.error(f"Error processing document for PII: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Example usage
if __name__ == "__main__":
    detector = PIIDetector()
    
    # Test text
    text = """
    Il signor Mario Rossi, nato il 15/03/1985, residente in Via Roma 123, 00100 Roma (RM).
    Codice Fiscale: RSSMRA85C15H501X
    Telefono: +39 333 1234567
    Email: mario.rossi@example.com
    IBAN: IT60X0542811101000000123456
    """
    
    result = detector.detect_and_anonymize(text)
    print(f"Detected {result['entity_count']} entities")
    print(f"Anonymized: {result['anonymized_text']}")
