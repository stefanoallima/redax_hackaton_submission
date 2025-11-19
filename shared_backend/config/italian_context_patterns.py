"""
Italian Legal Context Patterns

Provides context-aware boost/suppress patterns for Italian legal documents.
Improves detection accuracy by using surrounding text context.

Key Features:
- Boost patterns: Increase confidence when entity appears in typical PII context
- Suppress patterns: Decrease confidence when entity appears in non-PII context
- Italian legal-specific patterns

Expected Impact: 10-15% reduction in false positives

Author: RedaxAI.app  Team
Date: 2025-11-14
"""

import re
from typing import List, Dict, Optional
from italian_legal_context import is_denied_pattern, is_allowed_entity


# ============================================================
# BOOST PATTERNS - Increase confidence for entities in these contexts
# ============================================================

ITALIAN_BOOST_PATTERNS = {
    "person_name": [
        # Legal document signatures
        r"Il sottoscritto\s+(\w+\s+\w+)",  # "The undersigned [NAME]"
        r"sottoscritt[oa]\s+(\w+\s+\w+)",

        # Professional titles
        r"(?:Sig\.|Sig\.ra|Dott\.|Dott\.ssa|Avv\.|Ing\.|Arch\.)\s+(\w+\s+\w+)",

        # Legal representation
        r"rappresentato e difeso da[ll']?[Aa]vv\.?\s+(\w+\s+\w+)",
        r"in persona di\s+(\w+\s+\w+)",
        r"nella persona di\s+(\w+\s+\w+)",

        # Birth/identity contexts
        r"nat[oa] a\s+\w+\s+il\s+[\d/]+,?\s+(\w+\s+\w+)",
        r"(\w+\s+\w+),?\s+nat[oa]",

        # Legal parties
        r"(?:ricorrente|convenuto|attore|imputato|parte civile)\s+(\w+\s+\w+)",

        # Employment contexts
        r"dipendente\s+(\w+\s+\w+)",
        r"lavoratore\s+(\w+\s+\w+)",
        r"assunto\s+(\w+\s+\w+)",
    ],

    "fiscal_code": [
        # Explicit mentions
        r"codice fiscale[:\s]+([A-Z]{6}[\d]{2}[A-Z][\d]{2}[A-Z][\d]{3}[A-Z])",
        r"C\.F\.[:\s]+([A-Z]{6}[\d]{2}[A-Z][\d]{2}[A-Z][\d]{3}[A-Z])",
        r"CF[:\s]+([A-Z]{6}[\d]{2}[A-Z][\d]{2}[A-Z][\d]{3}[A-Z])",
    ],

    "contact_info": [
        # Phone contexts
        r"telefono[:\s]+([\d\s\-\+\(\)]+)",
        r"cellulare[:\s]+([\d\s\-\+\(\)]+)",
        r"tel\.[:\s]+([\d\s\-\+\(\)]+)",

        # Email contexts
        r"email[:\s]+([^\s]+@[^\s]+)",
        r"pec[:\s]+([^\s]+@[^\s]+)",
        r"e-mail[:\s]+([^\s]+@[^\s]+)",
    ],

    "address": [
        # Address markers
        r"residente in\s+(via|viale|piazza|corso)[\s\w]+\d+",
        r"domiciliat[oa] in\s+(via|viale|piazza|corso)[\s\w]+\d+",
        r"indirizzo[:\s]+(via|viale|piazza|corso)[\s\w]+\d+",
        r"sede in\s+(via|viale|piazza|corso)[\s\w]+\d+",
    ],
}


# ============================================================
# SUPPRESS PATTERNS - Decrease confidence for entities in these contexts
# ============================================================

ITALIAN_SUPPRESS_PATTERNS = {
    "legal_references": [
        # Article references
        r"articolo\s+\d+",
        r"art\.\s+\d+",
        r"comma\s+\d+",

        # Code references
        r"codice\s+(?:civile|penale|procedura)",
        r"c\.c\.|c\.p\.|c\.p\.c\.|c\.p\.p\.",

        # Law references
        r"legge\s+n\.\s*\d+",
        r"decreto\s+legislativo\s+n\.\s*\d+",
        r"d\.lgs\.\s+n\.\s*\d+",
        r"d\.l\.\s+n\.\s*\d+",
    ],

    "case_references": [
        # Court decision references
        r"sentenza\s+n\.\s*\d+",
        r"ordinanza\s+n\.\s*\d+",
        r"decreto\s+n\.\s*\d+",
        r"ricorso\s+n\.\s*\d+",

        # Case numbers
        r"R\.G\.\s+n\.\s*\d+",
        r"ruolo\s+generale\s+n\.\s*\d+",
    ],

    "document_sections": [
        # Headers and sections
        r"(?:^|\n)\s*INDICE\s*(?:\n|$)",
        r"(?:^|\n)\s*BIBLIOGRAFIA\s*(?:\n|$)",
        r"(?:^|\n)\s*RIFERIMENTI\s+NORMATIVI\s*(?:\n|$)",
        r"(?:^|\n)\s*ALLEGAT[OI]\s+[A-Z0-9]+\s*(?:\n|$)",

        # Page numbers
        r"Pagina\s+\d+\s+di\s+\d+",
        r"pag\.\s+\d+",
    ],

    "generic_terms": [
        # Generic party references (should NOT be treated as PII)
        r"\b(?:ricorrente|convenuto|attore|imputato)\b(?!\s+[A-Z][a-z]+)",

        # Court names (already in allow list, but extra safety)
        r"Tribunale\s+di\s+\w+",
        r"Corte\s+d[i']Appello",
        r"Corte\s+di\s+Cassazione",
        r"TAR\s+\w+",
    ],
}


# ============================================================
# CONTEXT FILTER FUNCTION
# ============================================================

def apply_context_filter(
    entities: List[Dict],
    text: str,
    boost_multiplier: float = 1.2,
    suppress_multiplier: float = 0.7
) -> List[Dict]:
    """
    Apply context-aware filtering to detected entities.

    Filters entities using deny/allow lists and context patterns:
    - Deny list: Remove entities matching denied patterns (false positives)
    - Allow list: Remove entities that should never be redacted (institutions)
    - Boost: Entities in typical PII contexts get higher confidence
    - Suppress: Entities in non-PII contexts get lower confidence

    Args:
        entities: List of detected entities with scores
        text: Original text
        boost_multiplier: Multiplier for boost patterns (default: 1.2)
        suppress_multiplier: Multiplier for suppress patterns (default: 0.7)

    Returns:
        List of entities with adjusted scores (denied/allowed entities removed)
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Context filter: Processing {len(entities)} entities")
    for e in entities[:5]:  # Log first 5 for debugging
        logger.debug(f"  Entity: '{e['text']}' (type={e['entity_type']}, score={e['score']:.3f})")

    filtered_entities = []

    # Track filtering stats
    denied_count = 0
    allowed_count = 0
    boosted_count = 0
    suppressed_count = 0

    for entity in entities:
        entity_text = entity['text']
        entity_start = entity['start']
        entity_end = entity['end']
        entity_type = entity['entity_type']
        original_score = entity['score']

        # STEP 1: Check deny list FIRST (remove false positives)
        # These are patterns that should NEVER be treated as PII
        if is_denied_pattern(entity_text):
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"DENIED: '{entity_text}' matched deny list")
            denied_count += 1
            continue  # Skip this entity completely

        # STEP 2: Check allow list (remove protected entities)
        # These are institutions/courts that should NEVER be redacted
        if is_allowed_entity(entity_text):
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"ALLOWED: '{entity_text}' matched allow list")
            allowed_count += 1
            continue  # Skip this entity completely

        # STEP 3: Apply context-based boost/suppress patterns
        # Get surrounding context (100 chars before and after)
        context_start = max(0, entity_start - 100)
        context_end = min(len(text), entity_end + 100)
        context = text[context_start:context_end]

        # Check for boost patterns
        boosted = False
        for pattern_category, patterns in ITALIAN_BOOST_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    entity['score'] = min(1.0, original_score * boost_multiplier)
                    entity['context_boost'] = True
                    boosted = True
                    boosted_count += 1
                    break
            if boosted:
                break

        # Check for suppress patterns (only if not already boosted)
        if not boosted:
            suppressed = False
            for pattern_category, patterns in ITALIAN_SUPPRESS_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, context, re.IGNORECASE):
                        entity['score'] = original_score * suppress_multiplier
                        entity['context_suppress'] = True
                        suppressed = True
                        suppressed_count += 1
                        break
                if suppressed:
                    break

        filtered_entities.append(entity)

    # Log filtering statistics (will appear in detector logs)
    if denied_count > 0 or allowed_count > 0 or boosted_count > 0 or suppressed_count > 0:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Context filter: {boosted_count} boosted, {suppressed_count} suppressed, {denied_count} denied, {allowed_count} allowed (removed)")

    return filtered_entities


def check_entity_in_boost_context(entity_text: str, context: str) -> bool:
    """
    Check if entity appears in a boost context.

    Args:
        entity_text: The entity text to check
        context: Surrounding context

    Returns:
        True if entity is in boost context
    """
    for pattern_category, patterns in ITALIAN_BOOST_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern.replace(r"(\w+\s+\w+)", re.escape(entity_text)), context, re.IGNORECASE):
                return True
    return False


def check_entity_in_suppress_context(entity_text: str, context: str) -> bool:
    """
    Check if entity appears in a suppress context.

    Args:
        entity_text: The entity text to check
        context: Surrounding context

    Returns:
        True if entity is in suppress context
    """
    for pattern_category, patterns in ITALIAN_SUPPRESS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return True
    return False


# ============================================================
# TESTING/EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    print("Italian Context Patterns - Test")
    print("="*60)

    # Test boost patterns
    test_entities_boost = [
        {
            "entity_type": "PERSON",
            "text": "Mario Rossi",
            "start": 20,
            "end": 31,
            "score": 0.75
        }
    ]

    test_text_boost = "Il sottoscritto Mario Rossi, nato a Roma il 15/03/1985..."

    print("\nTest 1: Boost Pattern")
    print(f"Original score: {test_entities_boost[0]['score']}")
    filtered = apply_context_filter(test_entities_boost, test_text_boost)
    print(f"After boost: {filtered[0]['score']}")
    print(f"Boosted: {filtered[0].get('context_boost', False)}")

    # Test suppress patterns
    test_entities_suppress = [
        {
            "entity_type": "LOCATION",
            "text": "Milano",
            "start": 30,
            "end": 36,
            "score": 0.80
        }
    ]

    test_text_suppress = "Come previsto dall'articolo 123 del codice civile..."

    print("\nTest 2: Suppress Pattern")
    print(f"Original score: {test_entities_suppress[0]['score']}")
    filtered = apply_context_filter(test_entities_suppress, test_text_suppress)
    print(f"After suppress: {filtered[0]['score']}")
    print(f"Suppressed: {filtered[0].get('context_suppress', False)}")

    print(f"\n{'='*60}")
    print("Context patterns ready for integration")
