"""
Test context filter with problematic entities
"""

import logging
from italian_context_patterns import apply_context_filter
from italian_legal_context import is_denied_pattern

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

print("="*60)
print("CONTEXT FILTER TEST")
print("="*60)

# Test 1: Check if deny list function works
print("\n[1] Testing is_denied_pattern function:")
test_terms = [
    "Chief Technology Officer",
    "Chief Executive Officer",
    "Intergovernativi",
    "Firmato Da",
    "firmato da",
    "Mario Rossi"  # Should NOT be denied
]

for term in test_terms:
    result = is_denied_pattern(term)
    print(f"  '{term}': {'DENIED' if result else 'NOT DENIED'}")

# Test 2: Test the context filter
print("\n[2] Testing context filter with entities:")

test_entities = [
    {
        "entity_type": "ORGANIZATION",
        "text": "Chief Technology Officer",
        "start": 0,
        "end": 24,
        "score": 0.85,
        "source": "spacy"
    },
    {
        "entity_type": "ORGANIZATION",
        "text": "Intergovernativi",
        "start": 30,
        "end": 46,
        "score": 0.80,
        "source": "spacy"
    },
    {
        "entity_type": "PERSON",
        "text": "Firmato Da",
        "start": 50,
        "end": 60,
        "score": 0.75,
        "source": "spacy"
    },
    {
        "entity_type": "PERSON",
        "text": "Mario Rossi",
        "start": 70,
        "end": 81,
        "score": 0.90,
        "source": "spacy"
    }
]

test_text = "Chief Technology Officer and Intergovernativi at Firmato Da wrote Mario Rossi about the project."

print(f"\nOriginal entities: {len(test_entities)}")
for e in test_entities:
    print(f"  - '{e['text']}' (type={e['entity_type']}, score={e['score']})")

filtered = apply_context_filter(test_entities, test_text)

print(f"\nFiltered entities: {len(filtered)}")
for e in filtered:
    print(f"  - '{e['text']}' (type={e['entity_type']}, score={e['score']})")

print("\nExpected: Only 'Mario Rossi' should remain (others are in deny list)")
print(f"Result: {'PASS' if len(filtered) == 1 and filtered[0]['text'] == 'Mario Rossi' else 'FAIL'}")

print("="*60)