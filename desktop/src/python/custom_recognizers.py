"""
Custom Presidio Recognizers
Provides pattern-based, allow-list, and deny-list recognizers for Italian legal documents.

Features:
- Pattern-based recognizers (regex patterns for structured data)
- Allow-list recognizers (force-detect specific terms)
- Deny-list support (exclude common false positives)
- User-configurable patterns with persistence

Author: RedaxAI.app  Team
Date: 2025-11-15
"""

from typing import List, Dict, Optional
from presidio_analyzer import Pattern, PatternRecognizer
from presidio_analyzer.predefined_recognizers import SpacyRecognizer
from presidio_analyzer import RecognizerResult
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomPatternRecognizer(PatternRecognizer):
    """
    Custom pattern-based recognizer for user-defined patterns.
    Useful for detecting structured data like case numbers, contract IDs, etc.
    """

    def __init__(
        self,
        entity_type: str,
        patterns: List[Dict[str, any]],
        name: str = "custom_pattern",
        supported_language: str = "it",
        context: Optional[List[str]] = None
    ):
        """
        Initialize custom pattern recognizer.

        Args:
            entity_type: Type of entity to detect (e.g., "IT_CASE_NUMBER")
            patterns: List of pattern dicts with 'name', 'regex', 'score'
            name: Recognizer name
            supported_language: Language code
            context: Optional context words that boost confidence
        """
        # Convert pattern dicts to Pattern objects
        pattern_objects = [
            Pattern(
                name=p['name'],
                regex=p['regex'],
                score=p.get('score', 0.85)
            )
            for p in patterns
        ]

        super().__init__(
            supported_entity=entity_type,
            patterns=pattern_objects,
            name=name,
            supported_language=supported_language,
            context=context or []
        )


class AllowListRecognizer(PatternRecognizer):
    """
    Recognizer that force-detects specific terms from an allow-list.
    Useful for ensuring certain sensitive terms are always redacted.

    Supports 'flag_for_review' mode where terms are detected but marked
    for manual review (context-dependent).
    """

    def __init__(
        self,
        entity_type: str,
        allow_list: List[str],
        name: str = "custom_allowlist",
        supported_language: str = "it",
        case_sensitive: bool = False,
        flag_for_review: bool = False
    ):
        """
        Initialize allow-list recognizer.

        Args:
            entity_type: Type of entity (e.g., "ORGANIZATION", "PERSON")
            allow_list: List of terms to always detect
            name: Recognizer name
            supported_language: Language code
            case_sensitive: Whether matching is case-sensitive
            flag_for_review: If True, marks entities for manual review (context-dependent)
        """
        self.flag_for_review = flag_for_review
        # Build regex pattern from allow list
        # Escape special regex characters
        escaped_terms = [re.escape(term) for term in allow_list]

        # Create pattern with word boundaries for whole-word matching
        regex_pattern = r'\b(' + '|'.join(escaped_terms) + r')\b'

        # Create Pattern object
        pattern = Pattern(
            name=f"{entity_type}_allowlist",
            regex=regex_pattern,
            score=0.95  # High confidence for user-defined terms
        )

        super().__init__(
            supported_entity=entity_type,
            patterns=[pattern],
            name=name,
            supported_language=supported_language,
            context=[]
        )

        self.case_sensitive = case_sensitive

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        """Override analyze to handle case sensitivity."""
        if not self.case_sensitive:
            # Case-insensitive: convert text to lowercase for matching
            # but preserve original positions
            original_text = text
            text = text.lower()

        results = super().analyze(text, entities, nlp_artifacts)

        return results


class DenyListFilter:
    """
    Post-processing filter that removes false positives from deny-list.
    Applied after all recognizers run.
    """

    def __init__(self, deny_list: Dict[str, List[str]]):
        """
        Initialize deny-list filter.

        Args:
            deny_list: Dict mapping entity types to lists of terms to ignore
                      e.g., {"PERSON": ["Giudice", "Tribunale"], "LOCATION": ["Italia"]}
        """
        self.deny_list = deny_list

        # Pre-compile patterns for efficiency
        self.deny_patterns = {}
        for entity_type, terms in deny_list.items():
            if terms:
                escaped_terms = [re.escape(term) for term in terms]
                pattern = r'\b(' + '|'.join(escaped_terms) + r')\b'
                self.deny_patterns[entity_type] = re.compile(pattern, re.IGNORECASE)

    def filter_results(self, results: List[Dict]) -> List[Dict]:
        """
        Filter out entities matching deny-list.

        Args:
            results: List of entity dicts from detector

        Returns:
            Filtered list with deny-list matches removed
        """
        filtered = []
        removed_count = 0

        for entity in results:
            entity_type = entity.get('entity_type')
            text = entity.get('text', '')

            # Check if entity type has deny list
            if entity_type in self.deny_patterns:
                pattern = self.deny_patterns[entity_type]
                if pattern.search(text):
                    logger.debug(f"Filtered out '{text}' ({entity_type}) - matches deny list")
                    removed_count += 1
                    continue

            filtered.append(entity)

        if removed_count > 0:
            logger.info(f"Deny list filtered out {removed_count} false positives")

        return filtered


# ============================================================================
# Pre-configured recognizers for Italian legal documents
# ============================================================================

def get_italian_case_number_recognizer() -> CustomPatternRecognizer:
    """
    Recognizer for Italian legal case numbers.
    Formats: "123/2024", "RG 456/2023", "n. 789/2022"
    """
    patterns = [
        {
            'name': 'case_number_basic',
            'regex': r'\b\d{1,6}/\d{4}\b',
            'score': 0.85
        },
        {
            'name': 'case_number_rg',
            'regex': r'\bRG\s*\d{1,6}/\d{4}\b',
            'score': 0.90
        },
        {
            'name': 'case_number_n',
            'regex': r'\bn\.\s*\d{1,6}/\d{4}\b',
            'score': 0.90
        }
    ]

    return CustomPatternRecognizer(
        entity_type="IT_CASE_NUMBER",
        patterns=patterns,
        name="italian_case_number",
        context=["sentenza", "procedimento", "causa", "ricorso"]
    )


def get_italian_contract_amount_recognizer() -> CustomPatternRecognizer:
    """
    Recognizer for monetary amounts in Italian legal documents.
    Formats: "€50,000", "EUR 1.000.000", "euro 500"
    """
    patterns = [
        {
            'name': 'euro_symbol',
            'regex': r'€\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?',
            'score': 0.80
        },
        {
            'name': 'eur_code',
            'regex': r'\bEUR\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?',
            'score': 0.80
        },
        {
            'name': 'euro_word',
            'regex': r'\beuro\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?',
            'score': 0.75
        }
    ]

    return CustomPatternRecognizer(
        entity_type="MONETARY_AMOUNT",
        patterns=patterns,
        name="italian_contract_amount",
        context=["importo", "somma", "prezzo", "valore", "compenso"]
    )


def get_default_deny_list() -> Dict[str, List[str]]:
    """
    Get default deny-list for Italian legal documents.
    These are common terms that should NOT be considered PII.
    """
    return {
        "PERSON": [
            # Legal roles and titles
            "Giudice",
            "Avvocato",
            "Procuratore",
            "Notaio",
            "Cancelliere",
            "Presidente",
            "Consigliere",
            # Generic references
            "Parte",
            "Attore",
            "Convenuto",
            "Ricorrente",
            "Resistente",
            "Imputato",
            "Testimone"
        ],
        "LOCATION": [
            # Generic locations that are not sensitive
            "Italia",
            "Repubblica Italiana",
            "Unione Europea",
            "UE"
        ],
        "ORGANIZATION": [
            # Government institutions (public info)
            "Tribunale",
            "Corte",
            "Procura",
            "Ministero"
        ]
    }


# ============================================================================
# User configuration management
# ============================================================================

class CustomRecognizerConfig:
    """
    Manages user-defined custom recognizers and deny-lists.
    Provides persistence and easy integration with PII detector.
    """

    def __init__(self, config_dict: Optional[Dict] = None):
        """
        Initialize from configuration dictionary.

        Args:
            config_dict: Configuration with 'patterns', 'allow_lists', 'deny_lists'
        """
        self.config = config_dict or self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            'patterns': [
                {
                    'entity_type': 'IT_CASE_NUMBER',
                    'enabled': True,
                    'patterns': [
                        {'name': 'case_basic', 'regex': r'\b\d{1,6}/\d{4}\b', 'score': 0.85}
                    ],
                    'context': ['sentenza', 'procedimento']
                }
            ],
            'allow_lists': [
                {
                    'entity_type': 'ORGANIZATION',
                    'enabled': False,
                    'terms': [],
                    'case_sensitive': False
                }
            ],
            'deny_lists': get_default_deny_list()
        }

    def get_recognizers(self) -> List:
        """
        Build recognizer instances from configuration.

        Returns:
            List of recognizer instances ready to add to Presidio registry
        """
        recognizers = []

        # Pattern recognizers
        for pattern_config in self.config.get('patterns', []):
            if not pattern_config.get('enabled', True):
                continue

            recognizer = CustomPatternRecognizer(
                entity_type=pattern_config['entity_type'],
                patterns=pattern_config['patterns'],
                context=pattern_config.get('context', [])
            )
            recognizers.append(recognizer)

        # Allow-list recognizers
        for allow_config in self.config.get('allow_lists', []):
            if not allow_config.get('enabled', False):
                continue

            if not allow_config.get('terms'):
                continue

            recognizer = AllowListRecognizer(
                entity_type=allow_config['entity_type'],
                allow_list=allow_config['terms'],
                case_sensitive=allow_config.get('case_sensitive', False)
            )
            recognizers.append(recognizer)

        return recognizers

    def get_deny_list_filter(self) -> Optional[DenyListFilter]:
        """
        Build deny-list filter from configuration.

        Returns:
            DenyListFilter instance or None if no deny lists configured
        """
        deny_lists = self.config.get('deny_lists', {})
        if not deny_lists:
            return None

        return DenyListFilter(deny_lists)

    def add_pattern(self, entity_type: str, name: str, regex: str, score: float = 0.85, context: List[str] = None):
        """Add a new pattern recognizer."""
        pattern_entry = {
            'entity_type': entity_type,
            'enabled': True,
            'patterns': [{'name': name, 'regex': regex, 'score': score}],
            'context': context or []
        }
        self.config.setdefault('patterns', []).append(pattern_entry)

    def add_allow_list_term(self, entity_type: str, term: str):
        """Add a term to allow-list."""
        # Find existing allow-list for this entity type
        for allow_config in self.config.get('allow_lists', []):
            if allow_config['entity_type'] == entity_type:
                if term not in allow_config['terms']:
                    allow_config['terms'].append(term)
                return

        # Create new allow-list
        self.config.setdefault('allow_lists', []).append({
            'entity_type': entity_type,
            'enabled': True,
            'terms': [term],
            'case_sensitive': False
        })

    def add_deny_list_term(self, entity_type: str, term: str):
        """Add a term to deny-list."""
        deny_lists = self.config.setdefault('deny_lists', {})
        deny_lists.setdefault(entity_type, []).append(term)

    def to_dict(self) -> Dict:
        """Export configuration as dictionary for persistence."""
        return self.config

    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'CustomRecognizerConfig':
        """Load configuration from dictionary."""
        return cls(config_dict)


# Testing/example usage
if __name__ == "__main__":
    # Test pattern recognizers
    print("=" * 60)
    print("Testing Custom Recognizers")
    print("=" * 60)

    # Create configuration
    config = CustomRecognizerConfig()

    # Add custom allow-list
    config.add_allow_list_term("ORGANIZATION", "ABC Legal Services")
    config.add_allow_list_term("ORGANIZATION", "Studio Legale XYZ")

    # Add deny-list term
    config.add_deny_list_term("PERSON", "Dott.")

    # Get recognizers
    recognizers = config.get_recognizers()
    print(f"\nCreated {len(recognizers)} custom recognizers")
    for rec in recognizers:
        print(f"  - {rec.name}: {rec.supported_entities}")

    # Get deny-list filter
    deny_filter = config.get_deny_list_filter()
    if deny_filter:
        print(f"\nDeny-list filter configured with {len(deny_filter.deny_list)} entity types")

    # Test filtering
    test_entities = [
        {'entity_type': 'PERSON', 'text': 'Giudice', 'score': 0.9},
        {'entity_type': 'PERSON', 'text': 'Mario Rossi', 'score': 0.95},
        {'entity_type': 'LOCATION', 'text': 'Italia', 'score': 0.8},
        {'entity_type': 'LOCATION', 'text': 'Milano', 'score': 0.9}
    ]

    print(f"\nTest entities: {len(test_entities)}")
    filtered = deny_filter.filter_results(test_entities)
    print(f"After filtering: {len(filtered)} (removed {len(test_entities) - len(filtered)})")
    for entity in filtered:
        print(f"  ✓ {entity['entity_type']}: {entity['text']}")
