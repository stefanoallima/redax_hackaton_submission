"""
Text Normalizer for ALL CAPS Detection

Handles ALL CAPS text that causes NER models to fail detection.
Converts ALL CAPS names to Title Case while preserving original positions.

Problem:
- "MARIO ROSSI" (ALL CAPS) is not recognized as PERSON
- "MARIO.ROSSI@EMAIL.COM" (ALL CAPS) is not recognized as EMAIL

Solution:
- Detect ALL CAPS sequences
- Convert to Title Case for detection
- Map positions back to original text

Author: RedaxAI.app  Team
Date: 2025-11-14
"""

import re
from typing import List, Dict, Tuple


class TextNormalizer:
    """
    Normalizes text to improve NER detection on ALL CAPS text.
    """

    # Patterns for ALL CAPS detection
    # Updated to handle Italian names with apostrophes (D'ASCOLA, DELL'AQUILA, O'BRIEN)
    ALL_CAPS_NAME_PATTERN = re.compile(
        r'\b([A-Z]+(?:\'[A-Z]+)*)(?:\s+[A-Z]+(?:\'[A-Z]+)*)+\b'  # MARIO ROSSI, PASQUALE D'ASCOLA, MARIO ROSSI GIOVANNI
    )

    ALL_CAPS_EMAIL_PATTERN = re.compile(
        r'\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b'  # MARIO.ROSSI@EMAIL.COM
    )

    # Words that should stay ALL CAPS (acronyms, codes)
    PRESERVE_ALL_CAPS = {
        'INPS', 'INAIL', 'MEF', 'CONSOB', 'AGID', 'ANAC', 'CNF', 'CSM',
        'TAR', 'CF', 'IVA', 'IBAN', 'PEC', 'PM', 'CTU',
        'USA', 'UK', 'EU', 'NATO', 'ONU', 'UE'
    }

    def __init__(self, enable_normalization: bool = True):
        """
        Initialize text normalizer.

        Args:
            enable_normalization: Whether to enable ALL CAPS normalization
        """
        self.enable_normalization = enable_normalization
        self._normalization_map = []  # Maps normalized positions to original

    def normalize(self, text: str) -> Tuple[str, Dict[int, Tuple[str, str]]]:
        """
        Normalize ALL CAPS text to improve detection.

        Args:
            text: Original text with ALL CAPS sequences

        Returns:
            Tuple of (normalized_text, replacement_map)
            replacement_map: {start_pos: (original_text, normalized_text)}
        """
        if not self.enable_normalization:
            return text, {}

        normalized_text = text
        replacement_map = {}

        # Step 1: Normalize ALL CAPS names
        for match in self.ALL_CAPS_NAME_PATTERN.finditer(text):
            original = match.group(0)
            start = match.start()
            end = match.end()

            # Skip if it's a preserved acronym
            if original in self.PRESERVE_ALL_CAPS:
                continue

            # Skip if it's less than 4 characters (likely an acronym)
            if len(original.replace(' ', '')) < 4:
                continue

            # Convert to Title Case
            normalized = original.title()

            # Store in replacement map
            replacement_map[start] = (original, normalized)

            # Replace in text
            normalized_text = normalized_text[:start] + normalized + normalized_text[end:]

        # Step 2: Normalize ALL CAPS emails
        for match in self.ALL_CAPS_EMAIL_PATTERN.finditer(normalized_text):
            original = match.group(0)
            start = match.start()
            end = match.end()

            # Convert to lowercase (standard for emails)
            normalized = original.lower()

            # Store in replacement map
            replacement_map[start] = (original, normalized)

            # Replace in text
            normalized_text = normalized_text[:start] + normalized + normalized_text[end:]

        return normalized_text, replacement_map

    def denormalize_entities(
        self,
        entities: List[Dict],
        replacement_map: Dict[int, Tuple[str, str]],
        original_text: str
    ) -> List[Dict]:
        """
        Map entity positions back to original text and restore original casing.

        Args:
            entities: Entities detected in normalized text
            replacement_map: Map of replacements from normalize()
            original_text: Original text before normalization

        Returns:
            Entities with positions and text from original document
        """
        denormalized_entities = []

        for entity in entities:
            entity_start = entity['start']
            entity_end = entity['end']
            entity_text = entity['text']

            # Check if this entity overlaps with any replacement
            original_start = entity_start
            original_end = entity_end
            original_entity_text = entity_text

            for replace_start, (original, normalized) in replacement_map.items():
                replace_end = replace_start + len(normalized)

                # Check if entity is within or overlaps replacement
                if replace_start <= entity_start < replace_end:
                    # Entity starts in replacement zone
                    offset = entity_start - replace_start
                    original_start = replace_start + offset

                    # Calculate end position
                    if entity_end <= replace_end:
                        # Entity fully within replacement
                        original_end = replace_start + (entity_end - replace_start)
                        original_entity_text = original_text[original_start:original_end]
                    else:
                        # Entity extends beyond replacement
                        original_end = entity_end
                        original_entity_text = original_text[original_start:original_end]
                    break

            # Create denormalized entity
            denormalized_entity = entity.copy()
            denormalized_entity['start'] = original_start
            denormalized_entity['end'] = original_end
            denormalized_entity['text'] = original_entity_text

            denormalized_entities.append(denormalized_entity)

        return denormalized_entities

    def detect_all_caps_sequences(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Detect all ALL CAPS sequences in text for diagnostics.

        Args:
            text: Text to analyze

        Returns:
            List of (start, end, text) tuples for ALL CAPS sequences
        """
        sequences = []

        # Names
        for match in self.ALL_CAPS_NAME_PATTERN.finditer(text):
            if match.group(0) not in self.PRESERVE_ALL_CAPS:
                sequences.append((match.start(), match.end(), match.group(0)))

        # Emails
        for match in self.ALL_CAPS_EMAIL_PATTERN.finditer(text):
            sequences.append((match.start(), match.end(), match.group(0)))

        return sequences

    def get_stats(self, text: str, normalized_text: str, replacement_map: Dict) -> Dict:
        """
        Get normalization statistics.

        Args:
            text: Original text
            normalized_text: Normalized text
            replacement_map: Replacement map

        Returns:
            Statistics dictionary
        """
        all_caps_sequences = self.detect_all_caps_sequences(text)

        return {
            "original_length": len(text),
            "normalized_length": len(normalized_text),
            "replacements_count": len(replacement_map),
            "all_caps_sequences_found": len(all_caps_sequences),
            "all_caps_sequences": all_caps_sequences[:10]  # First 10 for display
        }


# Testing/example usage
if __name__ == "__main__":
    print("Text Normalizer - Test")
    print("="*60)

    # Test text with ALL CAPS names and emails
    test_text = """
CONTRATTO DI LAVORO

Il sottoscritto MARIO ROSSI, nato a Roma il 15/03/1985,
codice fiscale RSSMRA85C15H501X, email MARIO.ROSSI@EXAMPLE.COM,
rappresentato da GIOVANNI BIANCHI, avvocato.

Indirizzo: VIA GIUSEPPE GARIBALDI 123, MILANO (MI)
Telefono: +39 333 1234567
PEC: MARIO.ROSSI@PEC.IT

Riferimenti:
- INPS: codice ABCD1234
- INAIL: posizione XYZ789
"""

    normalizer = TextNormalizer(enable_normalization=True)

    # Normalize text
    print("\n1. Original text:")
    print("-"*60)
    print(test_text)

    normalized_text, replacement_map = normalizer.normalize(test_text)

    print("\n2. Normalized text:")
    print("-"*60)
    print(normalized_text)

    print("\n3. Replacement map:")
    print("-"*60)
    for start, (original, normalized) in sorted(replacement_map.items()):
        print(f"  Position {start}: '{original}' → '{normalized}'")

    # Get statistics
    stats = normalizer.get_stats(test_text, normalized_text, replacement_map)
    print("\n4. Normalization Statistics:")
    print("-"*60)
    print(f"  Replacements: {stats['replacements_count']}")
    print(f"  ALL CAPS sequences found: {stats['all_caps_sequences_found']}")
    print("\n  Detected ALL CAPS sequences:")
    for start, end, text in stats['all_caps_sequences']:
        print(f"    - Position {start}-{end}: '{text}'")

    # Test entity denormalization
    print("\n5. Entity Denormalization Test:")
    print("-"*60)

    # Simulate entities detected in normalized text
    test_entities = [
        {"entity_type": "PERSON", "text": "Mario Rossi", "start": 45, "end": 56, "score": 0.95},
        {"entity_type": "EMAIL_ADDRESS", "text": "mario.rossi@example.com", "start": 120, "end": 143, "score": 0.98}
    ]

    print("  Entities in normalized text:")
    for entity in test_entities:
        print(f"    - {entity['entity_type']}: '{entity['text']}' at {entity['start']}-{entity['end']}")

    denormalized = normalizer.denormalize_entities(test_entities, replacement_map, test_text)

    print("\n  Entities mapped to original text:")
    for entity in denormalized:
        print(f"    - {entity['entity_type']}: '{entity['text']}' at {entity['start']}-{entity['end']}")

    print(f"\n{'='*60}")
    print("Normalizer ready for integration")
