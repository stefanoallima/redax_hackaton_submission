"""
Redaction Configuration
Manages default entity types and user preferences
"""
from typing import List, Dict
import json
from pathlib import Path

class RedactionConfig:
    """
    Configuration for PII detection and redaction
    Manages which entity types are enabled by default
    """
    
    # Default entity types with settings
    # Note: Entity types match Presidio entity names from integrated detector
    DEFAULT_ENTITY_TYPES = {
        "PERSON": {
            "enabled": True,
            "label": "Person Names",
            "description": "Full names, first names, last names",
            "auto_accept": True,
            "priority": 1
        },
        "IT_FISCAL_CODE": {
            "enabled": True,
            "label": "Codice Fiscale",
            "description": "Italian tax identification numbers",
            "auto_accept": True,
            "priority": 1
        },
        "PHONE_NUMBER": {
            "enabled": True,
            "label": "Phone Numbers",
            "description": "Mobile and landline numbers",
            "auto_accept": True,
            "priority": 2
        },
        "EMAIL_ADDRESS": {
            "enabled": True,
            "label": "Email Addresses",
            "description": "Email contacts",
            "auto_accept": True,
            "priority": 2
        },
        "IBAN": {
            "enabled": True,
            "label": "Bank Accounts (IBAN)",
            "description": "Italian bank account numbers",
            "auto_accept": True,
            "priority": 1
        },
        "IT_VAT_CODE": {
            "enabled": True,
            "label": "Partita IVA",
            "description": "Italian VAT identification numbers",
            "auto_accept": True,
            "priority": 1
        },
        "IT_DRIVER_LICENSE": {
            "enabled": True,
            "label": "Driver License",
            "description": "Italian driver license numbers",
            "auto_accept": True,
            "priority": 2
        },
        "IT_IDENTITY_CARD": {
            "enabled": True,
            "label": "Identity Card",
            "description": "Italian identity card numbers",
            "auto_accept": True,
            "priority": 1
        },
        "IT_PASSPORT": {
            "enabled": True,
            "label": "Passport",
            "description": "Italian passport numbers",
            "auto_accept": True,
            "priority": 2
        },
        "ADDRESS": {
            "enabled": False,  # Disabled by default (often needed in context)
            "label": "Physical Addresses",
            "description": "Street addresses, cities, postal codes",
            "auto_accept": False,
            "priority": 3
        },
        "DATE_TIME": {
            "enabled": False,  # Often needed in legal documents
            "label": "Dates",
            "description": "Birth dates, contract dates",
            "auto_accept": False,
            "priority": 4
        },
        "LOCATION": {
            "enabled": False,
            "label": "Locations",
            "description": "Cities, regions, countries",
            "auto_accept": False,
            "priority": 4
        },
        "ORGANIZATION": {
            "enabled": False,
            "label": "Organizations",
            "description": "Companies, institutions",
            "auto_accept": False,
            "priority": 4
        },
        "MISC": {
            "enabled": False,
            "label": "Miscellaneous",
            "description": "Other entities",
            "auto_accept": False,
            "priority": 5
        }
    }
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to user config file (optional)
        """
        self.config_path = config_path or str(Path.home() / ".codicecivile" / "redaction_config.json")
        self.entity_types = self.DEFAULT_ENTITY_TYPES.copy()
        self.load_config()
    
    def load_config(self):
        """Load user configuration from file"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    for entity_type, settings in user_config.get('entity_types', {}).items():
                        if entity_type in self.entity_types:
                            self.entity_types[entity_type].update(settings)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'entity_types': self.entity_types
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get_enabled_types(self) -> List[str]:
        """Get list of enabled entity types"""
        return [
            entity_type 
            for entity_type, settings in self.entity_types.items() 
            if settings['enabled']
        ]
    
    def is_enabled(self, entity_type: str) -> bool:
        """Check if entity type is enabled"""
        return self.entity_types.get(entity_type, {}).get('enabled', False)
    
    def set_enabled(self, entity_type: str, enabled: bool):
        """Enable or disable an entity type"""
        if entity_type in self.entity_types:
            self.entity_types[entity_type]['enabled'] = enabled
            self.save_config()
    
    def should_auto_accept(self, entity_type: str) -> bool:
        """Check if entity type should be auto-accepted"""
        return self.entity_types.get(entity_type, {}).get('auto_accept', False)
    
    def filter_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Filter entities based on configuration
        
        Args:
            entities: List of detected entities
            
        Returns:
            Filtered and sorted list of entities
        """
        # Filter by enabled types
        filtered = [
            {**e, 'accepted': self.should_auto_accept(e['entity_type'])}
            for e in entities
            if self.is_enabled(e['entity_type'])
        ]
        
        # Sort by priority and confidence
        filtered.sort(
            key=lambda e: (
                -self.entity_types.get(e['entity_type'], {}).get('priority', 99),
                -e['score']
            )
        )
        
        return filtered
    
    def get_summary(self, entities: List[Dict]) -> Dict:
        """
        Generate summary statistics
        
        Args:
            entities: List of detected entities
            
        Returns:
            dict with summary statistics
        """
        summary = {
            'total': len(entities),
            'by_type': {},
            'auto_accepted': 0,
            'requires_review': 0,
            'avg_confidence': 0
        }
        
        for entity in entities:
            entity_type = entity['entity_type']
            
            # Count by type
            if entity_type not in summary['by_type']:
                summary['by_type'][entity_type] = {
                    'count': 0,
                    'label': self.entity_types.get(entity_type, {}).get('label', entity_type),
                    'enabled': self.is_enabled(entity_type),
                    'scores': []
                }
            
            summary['by_type'][entity_type]['count'] += 1
            summary['by_type'][entity_type]['scores'].append(entity['score'])
            
            # Count auto-accepted vs requires review
            if self.should_auto_accept(entity_type):
                summary['auto_accepted'] += 1
            else:
                summary['requires_review'] += 1
        
        # Calculate average confidence per type
        for type_stats in summary['by_type'].values():
            if type_stats['scores']:
                type_stats['avg_confidence'] = sum(type_stats['scores']) / len(type_stats['scores'])
        
        # Overall average confidence
        all_scores = [e['score'] for e in entities]
        summary['avg_confidence'] = sum(all_scores) / len(all_scores) if all_scores else 0
        
        return summary


# Singleton instance
_config_instance = None

def get_config() -> RedactionConfig:
    """Get or create singleton config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = RedactionConfig()
    return _config_instance


# Example usage
if __name__ == "__main__":
    config = RedactionConfig()
    
    # Example entities
    entities = [
        {"entity_type": "PERSON", "text": "Mario Rossi", "score": 0.95},
        {"entity_type": "IT_FISCAL_CODE", "text": "RSSMRA85C15H501X", "score": 0.98},
        {"entity_type": "ADDRESS", "text": "Via Roma 123", "score": 0.85},
        {"entity_type": "DATE_TIME", "text": "15/03/1985", "score": 0.90},
        {"entity_type": "IT_VAT_CODE", "text": "12345678901", "score": 0.97},
        {"entity_type": "IT_DRIVER_LICENSE", "text": "FI1234567A", "score": 0.92}
    ]
    
    # Filter based on config
    filtered = config.filter_entities(entities)
    print(f"Filtered: {len(filtered)} entities (from {len(entities)} detected)")
    
    # Get summary
    summary = config.get_summary(entities)
    print(f"Summary: {summary['auto_accepted']} auto-accepted, {summary['requires_review']} require review")
