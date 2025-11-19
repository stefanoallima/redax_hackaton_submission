"""
Learned Entities Database - Simple JSON storage for PII learned from Gemini scans
This enables the "learning loop" where Gemini teaches local ML
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class LearnedEntitiesDB:
    """
    Simple JSON-based storage for entities confirmed by users from Gemini scans
    Provides O(1) exact string matching for fast lookups during Standard Scans
    """

    DEFAULT_DB_PATH = Path.home() / ".oscuratesti" / "learned_entities.json"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize learned entities database

        Args:
            db_path: Path to JSON file (creates if doesn't exist)
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Data structure:
        # {
        #   "entities": {
        #     "mario rossi": {  # normalized_text (lowercase)
        #       "original_text": "Mario Rossi",
        #       "entity_type": "PERSON",
        #       "learned_from": "gemini_scan",
        #       "learned_at": "2025-01-15T14:30:00",
        #       "count": 3,  # number of times confirmed
        #       "variations": ["Mario Rossi", "MARIO ROSSI", "Mario  Rossi"]
        #     }
        #   },
        #   "denied": {
        #     "giudice": {  # entities user explicitly rejected
        #       "text": "giudice",
        #       "entity_type": "PERSON",
        #       "denied_at": "2025-01-15T14:35:00",
        #       "reason": "user_rejected"
        #     }
        #   },
        #   "metadata": {
        #     "total_learned": 45,
        #     "total_denied": 3,
        #     "last_updated": "2025-01-15T14:30:00",
        #     "version": "1.0"
        #   }
        # }
        self.data = self._load_db()

    def _load_db(self) -> Dict:
        """Load database from JSON file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Recalculate metadata counts to fix any inconsistencies from manual edits
                actual_learned = len(data.get('entities', {}))
                actual_denied = len(data.get('denied', {}))

                if data['metadata']['total_learned'] != actual_learned:
                    logger.warning(f"Metadata mismatch detected! Stored: {data['metadata']['total_learned']}, Actual: {actual_learned}. Fixing...")
                    data['metadata']['total_learned'] = actual_learned

                if data['metadata']['total_denied'] != actual_denied:
                    logger.warning(f"Denied metadata mismatch! Stored: {data['metadata']['total_denied']}, Actual: {actual_denied}. Fixing...")
                    data['metadata']['total_denied'] = actual_denied

                logger.info(f"Loaded learned entities database: {data['metadata']['total_learned']} entities")
                return data
            except Exception as e:
                logger.error(f"Failed to load database, creating new: {e}")
                return self._create_empty_db()
        else:
            logger.info("No existing database found, creating new")
            return self._create_empty_db()

    def _create_empty_db(self) -> Dict:
        """Create empty database structure"""
        return {
            "entities": {},
            "denied": {},
            "metadata": {
                "total_learned": 0,
                "total_denied": 0,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

    def _save_db(self):
        """Save database to JSON file"""
        try:
            # Recalculate counts to ensure consistency
            self.data['metadata']['total_learned'] = len(self.data.get('entities', {}))
            self.data['metadata']['total_denied'] = len(self.data.get('denied', {}))
            self.data['metadata']['last_updated'] = datetime.now().isoformat()

            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Database saved: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to save database: {e}")
            raise

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for consistent matching

        Args:
            text: Original text

        Returns:
            Normalized text (lowercase, single spaces)
        """
        # Convert to lowercase
        normalized = text.lower()

        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)

        # Strip leading/trailing whitespace
        normalized = normalized.strip()

        return normalized

    def add_learned_entity(
        self,
        entity: Dict[str, Any],
        source: str = "gemini_scan"
    ) -> bool:
        """
        Add a learned entity (confirmed by user)

        Args:
            entity: Entity dict with keys: text, entity_type, page (optional), confidence (optional)
            source: Source of learning (gemini_scan, manual_add, etc.)

        Returns:
            True if added/updated, False if denied or invalid
        """
        text = entity.get('text', '').strip()
        entity_type = entity.get('entity_type', 'UNKNOWN')

        if not text:
            logger.warning("Attempted to add empty entity")
            return False

        normalized = self.normalize_text(text)

        # Check if entity was previously denied
        if normalized in self.data['denied']:
            logger.info(f"Entity '{text}' was previously denied, skipping")
            return False

        # Add or update entity
        if normalized in self.data['entities']:
            # Increment count and add variation
            self.data['entities'][normalized]['count'] += 1

            variations = self.data['entities'][normalized].setdefault('variations', [])
            if text not in variations:
                variations.append(text)

            logger.info(f"Updated existing entity '{text}' (count: {self.data['entities'][normalized]['count']})")
        else:
            # New entity
            self.data['entities'][normalized] = {
                "original_text": text,
                "entity_type": entity_type,
                "learned_from": source,
                "learned_at": datetime.now().isoformat(),
                "count": 1,
                "variations": [text]
            }

            logger.info(f"Learned new entity '{text}' ({entity_type})")

        self._save_db()
        return True

    def add_denied_entity(
        self,
        entity: Dict[str, Any],
        reason: str = "user_rejected"
    ) -> bool:
        """
        Mark entity as denied (user explicitly rejected)

        Args:
            entity: Entity dict with text and entity_type
            reason: Reason for denial

        Returns:
            True if denied, False if invalid
        """
        text = entity.get('text', '').strip()
        entity_type = entity.get('entity_type', 'UNKNOWN')

        if not text:
            logger.warning("Attempted to deny empty entity")
            return False

        normalized = self.normalize_text(text)

        # Remove from learned entities if present
        if normalized in self.data['entities']:
            del self.data['entities'][normalized]
            logger.info(f"Removed '{text}' from learned entities")

        # Add to denied list
        if normalized not in self.data['denied']:
            self.data['denied'][normalized] = {
                "text": text,
                "entity_type": entity_type,
                "denied_at": datetime.now().isoformat(),
                "reason": reason
            }

            logger.info(f"Denied entity '{text}' ({reason})")

        self._save_db()
        return True

    def find_matches(self, text: str) -> List[Dict[str, Any]]:
        """
        Find all learned entities in the given text

        Args:
            text: Text to search

        Returns:
            List of matches with structure:
            [
                {
                    "text": "Mario Rossi",  # exact match from input text
                    "entity_type": "PERSON",
                    "source": "learned_from_gemini",
                    "score": 1.0,
                    "start": 10,  # character offset
                    "end": 21,
                    "learned_count": 3  # times user confirmed this entity
                },
                ...
            ]
        """
        if not text:
            return []

        text_lower = text.lower()
        matches = []

        for normalized_key, entity_data in self.data['entities'].items():
            # Find all occurrences of this entity in the text
            start_pos = 0
            while True:
                pos = text_lower.find(normalized_key, start_pos)
                if pos == -1:
                    break

                # Extract exact text from original (preserves case)
                matched_text = text[pos:pos + len(normalized_key)]

                matches.append({
                    "text": matched_text,
                    "entity_type": entity_data['entity_type'],
                    "source": "learned_from_gemini",
                    "score": 1.0,  # Exact match = 100% confidence
                    "start": pos,
                    "end": pos + len(normalized_key),
                    "learned_count": entity_data['count'],
                    "learned_at": entity_data.get('learned_at')
                })

                start_pos = pos + 1  # Continue searching for overlapping matches

        logger.debug(f"Found {len(matches)} learned entity matches in text")
        return matches

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics

        Returns:
            Dict with stats:
            {
                "total_learned": 45,
                "total_denied": 3,
                "by_type": {"PERSON": 20, "EMAIL_ADDRESS": 5, ...},
                "most_common": [("mario rossi", 15), ("email@example.com", 8), ...],
                "last_updated": "2025-01-15T14:30:00"
            }
        """
        by_type = {}
        entity_counts = []

        for normalized_key, entity_data in self.data['entities'].items():
            entity_type = entity_data['entity_type']
            by_type[entity_type] = by_type.get(entity_type, 0) + 1

            entity_counts.append((
                entity_data['original_text'],
                entity_data['count']
            ))

        # Sort by count descending
        most_common = sorted(entity_counts, key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_learned": self.data['metadata']['total_learned'],
            "total_denied": self.data['metadata']['total_denied'],
            "by_type": by_type,
            "most_common": most_common,
            "last_updated": self.data['metadata']['last_updated'],
            "db_path": str(self.db_path)
        }

    def export_to_list(self) -> List[Dict[str, Any]]:
        """
        Export all learned entities as a list (for UI display)

        Returns:
            List of entities with all metadata
        """
        entities = []
        for normalized_key, entity_data in self.data['entities'].items():
            entities.append({
                "normalized_text": normalized_key,
                **entity_data
            })

        # Sort by count descending
        entities.sort(key=lambda x: x['count'], reverse=True)
        return entities

    def clear_all(self, confirm: bool = False):
        """
        Clear all learned entities (DANGEROUS)

        Args:
            confirm: Must be True to actually clear
        """
        if not confirm:
            raise ValueError("Must pass confirm=True to clear database")

        logger.warning("Clearing all learned entities!")
        self.data = self._create_empty_db()
        self._save_db()


# Singleton instance
_learned_db_instance: Optional[LearnedEntitiesDB] = None


def get_learned_db(db_path: Optional[Path] = None) -> LearnedEntitiesDB:
    """
    Get or create singleton learned entities database

    Args:
        db_path: Optional custom path (only used on first call)

    Returns:
        LearnedEntitiesDB instance
    """
    global _learned_db_instance

    if _learned_db_instance is None:
        _learned_db_instance = LearnedEntitiesDB(db_path=db_path)

    return _learned_db_instance
