GitHub Entity Lists: Structure & Implementation
Repository Structure
Recommended Organization
your-org/presidio-italian-entities/
│
├── README.md
├── VERSION
├── .github/
│   └── workflows/
│       └── validate.yml  # CI/CD validation
│
├── entities/
│   ├── allow_lists/
│   │   ├── courts.txt
│   │   ├── government_agencies.csv
│   │   ├── legal_roles.json
│   │   └── public_institutions.txt
│   │
│   ├── deny_lists/
│   │   ├── common_names.txt
│   │   ├── historical_figures.csv
│   │   ├── legal_scholars.txt
│   │   └── generic_terms.json
│   │
│   └── context_patterns/
│       ├── boost_patterns.json
│       └── suppress_patterns.json
│
├── schemas/
│   ├── csv_schema.json
│   └── json_schema.json
│
└── scripts/
    ├── validate.py
    └── merge_duplicates.py
File Format Options
1. Simple Text Files (.txt) - For Basic Lists
txt# courts.txt
# Italian Courts - One per line
# Comments start with #
# Last updated: 2025-01-15

Tribunale di Milano
Tribunale di Roma
Tribunale di Napoli
Corte di Cassazione
Corte d'Appello di Milano
Corte d'Appello di Roma
TAR Lazio
TAR Lombardia
Consiglio di Stato
2. CSV Files - For Structured Data
csv# government_agencies.csv
entity_name,entity_type,region,confidence_boost,notes
Agenzia delle Entrate,TAX_AUTHORITY,National,0.95,National tax agency
INPS,SOCIAL_SECURITY,National,0.95,Pension institute
INAIL,INSURANCE,National,0.95,Work insurance
Ministero della Giustizia,MINISTRY,National,1.0,Justice ministry
Comune di Milano,MUNICIPALITY,Lombardia,0.9,Milan municipality
Regione Lombardia,REGION,Lombardia,0.9,Regional government
3. JSON Files - For Complex Structures
json{
  "version": "1.0.0",
  "last_updated": "2025-01-15",
  "legal_roles": {
    "high_confidence": {
      "entities": ["Giudice", "Pubblico Ministero", "Cancelliere"],
      "confidence_boost": 0.95,
      "context_required": false
    },
    "medium_confidence": {
      "entities": ["Avvocato", "Notaio", "Consulente"],
      "confidence_boost": 0.7,
      "context_required": true,
      "context_patterns": ["dello studio", "iscritto all'albo"]
    }
  }
}
4. YAML Files - For Hierarchical Data
yaml# legal_entities.yml
version: 1.0.0
entities:
  courts:
    supreme:
      - name: Corte di Cassazione
        confidence: 1.0
        aliases: ["Cassazione", "Suprema Corte"]
    
    appeal:
      - name: Corte d'Appello di Milano
        region: Lombardia
        confidence: 0.95
      - name: Corte d'Appello di Roma
        region: Lazio
        confidence: 0.95
Integration Code
Fetching from GitHub
pythonimport requests
import json
import csv
from typing import Dict, List, Set
from pathlib import Path
import hashlib

class GitHubEntityListManager:
    def __init__(self, repo_url: str, branch: str = "main", cache_dir: str = "./entity_cache"):
        """
        repo_url: e.g., "https://github.com/your-org/presidio-italian-entities"
        """
        self.repo_url = repo_url.rstrip('/')
        self.raw_url = repo_url.replace('github.com', 'raw.githubusercontent.com')
        self.branch = branch
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def fetch_text_list(self, path: str) -> Set[str]:
        """Fetch simple text file list"""
        url = f"{self.raw_url}/{self.branch}/{path}"
        
        # Check cache first
        cached_file = self.cache_dir / path.replace('/', '_')
        if self._is_cache_valid(cached_file):
            return self._load_cached_text(cached_file)
        
        # Fetch from GitHub
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse lines, skip comments and empty
        entities = set()
        for line in response.text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                entities.add(line)
        
        # Cache the result
        self._save_cache(cached_file, entities)
        return entities
    
    def fetch_csv_list(self, path: str) -> List[Dict]:
        """Fetch CSV with metadata"""
        url = f"{self.raw_url}/{self.branch}/{path}"
        
        cached_file = self.cache_dir / path.replace('/', '_')
        if self._is_cache_valid(cached_file):
            return self._load_cached_json(cached_file)
        
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse CSV
        entities = []
        reader = csv.DictReader(response.text.splitlines())
        for row in reader:
            if not row.get('entity_name', '').startswith('#'):
                entities.append(row)
        
        self._save_cache(cached_file, entities)
        return entities
    
    def fetch_json_config(self, path: str) -> Dict:
        """Fetch JSON configuration"""
        url = f"{self.raw_url}/{self.branch}/{path}"
        
        cached_file = self.cache_dir / path.replace('/', '_')
        if self._is_cache_valid(cached_file):
            return self._load_cached_json(cached_file)
        
        response = requests.get(url)
        response.raise_for_status()
        
        config = json.loads(response.text)
        self._save_cache(cached_file, config)
        return config
Presidio Integration
Using the Lists in Presidio
pythonfrom presidio_analyzer import RecognizerRegistry, PatternRecognizer

class ItalianEntityManager:
    def __init__(self):
        self.github_manager = GitHubEntityListManager(
            "https://github.com/your-org/presidio-italian-entities"
        )
        self.allow_lists = {}
        self.deny_lists = {}
        
    def load_entity_lists(self):
        """Load all entity lists from GitHub"""
        # Load allow lists
        self.allow_lists['courts'] = self.github_manager.fetch_text_list(
            "entities/allow_lists/courts.txt"
        )
        self.allow_lists['agencies'] = self.github_manager.fetch_csv_list(
            "entities/allow_lists/government_agencies.csv"
        )
        
        # Load deny lists  
        self.deny_lists['common'] = self.github_manager.fetch_text_list(
            "entities/deny_lists/common_names.txt"
        )
        
    def create_allow_list_recognizer(self, entity_type: str, entities: Set[str]):
        """Create recognizer for allowed entities"""
        # These should NOT be anonymized
        return PatternRecognizer(
            supported_entity=entity_type,
            deny_list=entities,  # Using as deny_list to NOT detect
            context=[".*"],  # Any context
            deny_list_score=0.01  # Very low score
        )
    
    def apply_to_analyzer(self, analyzer):
        """Apply lists to Presidio analyzer"""
        # Create recognizers for allow lists
        for list_name, entities in self.allow_lists.items():
            if isinstance(entities, set):
                recognizer = self.create_allow_list_recognizer(
                    f"ALLOWED_{list_name.upper()}", 
                    entities
                )
                analyzer.registry.add_recognizer(recognizer)
CI/CD Validation
GitHub Actions Workflow (.github/workflows/validate.yml)
yamlname: Validate Entity Lists

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install jsonschema pyyaml
    
    - name: Validate file formats
      run: python scripts/validate.py
    
    - name: Check for duplicates
      run: python scripts/merge_duplicates.py --check
    
    - name: Test entity loading
      run: |
        python -c "
        from scripts.validate import validate_all_lists
        assert validate_all_lists(), 'Validation failed'
        "
Update Strategy
Manual Updates

Edit files directly on GitHub
Create pull request
CI validates format
Merge to main
Applications fetch updated lists

Automated Updates
python# Scheduled job to fetch updates
import schedule
import time

def update_entity_lists():
    """Fetch latest entity lists from GitHub"""
    manager = ItalianEntityManager()
    manager.load_entity_lists()
    print(f"Updated {len(manager.allow_lists)} allow lists")
    print(f"Updated {len(manager.deny_lists)} deny lists")
    
# Schedule daily updates
schedule.every().day.at("02:00").do(update_entity_lists)

# Or use webhook for immediate updates
from flask import Flask, request
app = Flask(__name__)

@app.route('/webhook/entity-update', methods=['POST'])
def handle_github_webhook():
    """Handle GitHub webhook for entity list updates"""
    if verify_github_signature(request):
        update_entity_lists()
    return "OK"