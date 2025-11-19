"""
Entity-Specific Confidence Thresholds

Improves precision by using different thresholds per entity type and document type.

Key Features:
1. Different thresholds per entity type (CF needs 0.95, PERSON needs 0.70)
2. Document type detection (legal vs. medical vs. administrative)
3. Dynamic threshold adjustment based on document type
4. Depth level integration (fast/balanced/thorough/maximum)

Expected Impact: ≥10% precision improvement

Author: RedaxAI.app  Team
Date: 2025-11-14
"""

from typing import Dict, Optional
import re


class EntityThresholdManager:
    """
    Manages entity-specific and document-type specific confidence thresholds.
    """

    # ============================================================
    # BASE ENTITY THRESHOLDS
    # ============================================================

    BASE_THRESHOLDS = {
        # High-confidence entities (specific patterns with validation)
        "IT_FISCAL_CODE": 0.95,     # Checksum validation - very reliable
        "IBAN": 0.95,               # Checksum validation - very reliable
        "EMAIL_ADDRESS": 0.90,      # Regex pattern - reliable
        "PHONE_NUMBER": 0.85,       # Format validation - fairly reliable
        "CREDIT_CARD": 0.95,        # Luhn algorithm - very reliable

        # Medium-confidence entities (context-dependent)
        "ADDRESS": 0.80,            # Can be ambiguous (Via Roma, etc.)
        "LOCATION": 0.80,           # Can be generic (Milano, Roma)
        "ORGANIZATION": 0.75,       # Can be ambiguous
        "DATE_TIME": 0.75,          # Many formats, context-dependent

        # Lower-confidence entities (wide variation)
        "PERSON": 0.80,             # Increased to reduce false positives (job titles, etc.)
        "NRP": 0.75,                # Nationality/ethnicity - context-dependent

        # Default for unknown entity types
        "DEFAULT": 0.75,
    }

    # ============================================================
    # DOCUMENT TYPE DETECTION
    # ============================================================

    DOCUMENT_TYPE_KEYWORDS = {
        "legal": [
            # Court terms
            "tribunale", "corte", "giudice", "sentenza", "ricorso",
            "udienza", "causa", "processo", "parte civile",

            # Legal actions
            "diffida", "citazione", "decreto", "ordinanza",

            # Legal references
            "codice civile", "codice penale", "costituzione",
        ],

        "medical": [
            # Medical terms
            "diagnosi", "terapia", "paziente", "medico", "ospedale",
            "ricovero", "prescrizione", "farmaco", "cartella clinica",

            # Medical specialties
            "cardiologo", "oncologo", "chirurgo", "radiologia",
        ],

        "administrative": [
            # Administrative terms
            "domanda", "istanza", "certificato", "autocertificazione",
            "dichiarazione", "richiesta", "pratica", "protocollo",

            # Official documents
            "stato civile", "residenza", "cittadinanza",
        ],
    }

    # ============================================================
    # DOCUMENT-TYPE THRESHOLD MODIFIERS
    # ============================================================

    DOCUMENT_TYPE_MODIFIERS = {
        "legal": {
            # Legal documents: Expect many names, addresses, dates
            "PERSON": -0.10,        # Lower threshold (many party names + Italian compound surnames with articles)
            "ADDRESS": -0.05,       # Lower threshold (addresses common)
            "DATE_TIME": -0.05,     # Lower threshold (birth dates, hearing dates)
            "LOCATION": -0.05,      # Lower threshold (birthplaces)
        },

        "medical": {
            # Medical records: Patient names are CRITICAL
            "PERSON": -0.10,        # Much lower (can't miss patient names)
            "DATE_TIME": -0.05,     # Lower (birth dates, visit dates)
            "PHONE_NUMBER": -0.05,  # Lower (contact info critical)
        },

        "administrative": {
            # Administrative forms: Structured data, high confidence
            "EMAIL_ADDRESS": 0.00,  # No change (already high)
            "PHONE_NUMBER": 0.00,   # No change
            "ADDRESS": 0.05,        # Slightly higher (avoid generic streets)
        },

        "general": {},  # No modifiers for general documents
    }

    # ============================================================
    # DEPTH LEVEL MODIFIERS
    # ============================================================

    DEPTH_LEVEL_MODIFIERS = {
        "fast": 0.00,        # No change (base thresholds)
        "balanced": 0.00,    # No change (base thresholds)
        "thorough": -0.05,   # Lower all thresholds slightly
        "maximum": -0.10,    # Lower all thresholds significantly (catch everything)
    }

    # ============================================================
    # METHODS
    # ============================================================

    @classmethod
    def detect_document_type(cls, text: str) -> str:
        """
        Detect document type based on keyword analysis.

        Args:
            text: Document text (first 2000 chars recommended)

        Returns:
            "legal", "medical", "administrative", or "general"
        """
        text_lower = text.lower()

        # Count keyword matches for each document type
        scores = {}
        for doc_type, keywords in cls.DOCUMENT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[doc_type] = score

        # Return type with highest score (minimum 2 matches required)
        max_type = max(scores, key=scores.get)
        if scores[max_type] >= 2:
            return max_type

        return "general"

    @classmethod
    def get_threshold(
        cls,
        entity_type: str,
        document_type: Optional[str] = None,
        depth: str = "balanced"
    ) -> float:
        """
        Get confidence threshold for given entity type, document type, and depth.

        Args:
            entity_type: Entity type (e.g., "PERSON", "IT_FISCAL_CODE")
            document_type: Document type ("legal", "medical", etc.) - auto-detected if None
            depth: Depth level ("fast", "balanced", "thorough", "maximum")

        Returns:
            Confidence threshold (0.0-1.0)

        Example:
            >>> # Codice Fiscale in legal document, balanced mode
            >>> EntityThresholdManager.get_threshold("IT_FISCAL_CODE", "legal", "balanced")
            0.95  # No modifiers (already very high)

            >>> # Person name in medical document, thorough mode
            >>> EntityThresholdManager.get_threshold("PERSON", "medical", "thorough")
            0.55  # 0.70 (base) - 0.10 (medical) - 0.05 (thorough)
        """
        # Get base threshold
        base_threshold = cls.BASE_THRESHOLDS.get(entity_type, cls.BASE_THRESHOLDS["DEFAULT"])

        # Apply document type modifier
        doc_modifier = 0.0
        if document_type and document_type in cls.DOCUMENT_TYPE_MODIFIERS:
            doc_modifiers = cls.DOCUMENT_TYPE_MODIFIERS[document_type]
            doc_modifier = doc_modifiers.get(entity_type, 0.0)

        # Apply depth level modifier
        depth_modifier = cls.DEPTH_LEVEL_MODIFIERS.get(depth, 0.0)

        # Calculate final threshold
        final_threshold = base_threshold + doc_modifier + depth_modifier

        # Clamp to valid range [0.0, 1.0]
        final_threshold = max(0.0, min(1.0, final_threshold))

        return final_threshold

    @classmethod
    def get_all_thresholds(
        cls,
        document_type: str = "general",
        depth: str = "balanced"
    ) -> Dict[str, float]:
        """
        Get thresholds for all entity types.

        Returns:
            Dictionary mapping entity type to threshold
        """
        return {
            entity_type: cls.get_threshold(entity_type, document_type, depth)
            for entity_type in cls.BASE_THRESHOLDS.keys()
        }


# Testing/example usage
if __name__ == "__main__":
    print("Entity Threshold Manager - Test")
    print("="*60)

    # Test document type detection
    legal_text = "Il Tribunale di Milano ha emesso la seguente sentenza nel ricorso..."
    medical_text = "Il paziente è stato ricoverato con diagnosi di bronchite acuta..."
    admin_text = "Istanza di certificato di residenza per il cittadino..."

    print("\n1. Document Type Detection:")
    print(f"  Legal: {EntityThresholdManager.detect_document_type(legal_text)}")
    print(f"  Medical: {EntityThresholdManager.detect_document_type(medical_text)}")
    print(f"  Administrative: {EntityThresholdManager.detect_document_type(admin_text)}")

    # Test entity-specific thresholds
    print("\n2. Entity-Specific Thresholds (General document, Balanced mode):")
    for entity_type in ["IT_FISCAL_CODE", "PERSON", "EMAIL_ADDRESS", "ADDRESS"]:
        threshold = EntityThresholdManager.get_threshold(entity_type, "general", "balanced")
        print(f"  {entity_type}: {threshold:.2f}")

    # Test document type modifiers
    print("\n3. Document Type Impact on PERSON threshold:")
    for doc_type in ["general", "legal", "medical", "administrative"]:
        threshold = EntityThresholdManager.get_threshold("PERSON", doc_type, "balanced")
        print(f"  {doc_type}: {threshold:.2f}")

    # Test depth level modifiers
    print("\n4. Depth Level Impact on PERSON threshold (Legal document):")
    for depth in ["fast", "balanced", "thorough", "maximum"]:
        threshold = EntityThresholdManager.get_threshold("PERSON", "legal", depth)
        print(f"  {depth}: {threshold:.2f}")

    # Get all thresholds
    print("\n5. All Thresholds (Medical document, Thorough mode):")
    all_thresholds = EntityThresholdManager.get_all_thresholds("medical", "thorough")
    for entity_type, threshold in sorted(all_thresholds.items()):
        if entity_type != "DEFAULT":
            print(f"  {entity_type}: {threshold:.2f}")

    print(f"\n{'='*60}")
    print("Test complete")
