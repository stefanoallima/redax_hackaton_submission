"""
LLM Validation Module (Optional Enhancement - Task 1.11)
Uses local LLM (llama.cpp) to validate Presidio PII detections
Reduces false positives by analyzing context
"""
import logging
from typing import List, Dict
import subprocess
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMValidator:
    """
    Validate PII detections using local LLM
    Uses llama.cpp with Llama 3.2 1B (GGUF 4-bit quantization)
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize LLM validator
        
        Args:
            model_path: Path to GGUF model file (default: models/llama-3.2-1b-q4.gguf)
        """
        self.model_path = model_path or str(Path(__file__).parent.parent.parent / "models" / "llama-3.2-1b-q4.gguf")
        self.llama_cpp_path = "llama-cli"  # Assumes llama.cpp installed in PATH
        
        logger.info(f"LLM Validator initialized with model: {self.model_path}")
    
    def validate_entity(self, entity: Dict, context: str, window: int = 50) -> Dict:
        """
        Validate a single PII entity using LLM
        
        Args:
            entity: Entity dict with type, text, start, end, score
            context: Full document text
            window: Characters of context to include (default: 50 chars each side)
            
        Returns:
            dict with validation result and updated confidence
        """
        try:
            # Extract context window around entity
            start = max(0, entity['start'] - window)
            end = min(len(context), entity['end'] + window)
            context_window = context[start:end]
            
            # Construct validation prompt
            prompt = self._build_validation_prompt(
                entity_type=entity['entity_type'],
                entity_text=entity['text'],
                context=context_window
            )
            
            # Run LLM inference
            llm_response = self._run_llm(prompt)
            
            # Parse LLM response
            is_valid, confidence_adjustment, reason = self._parse_llm_response(llm_response)
            
            # Adjust confidence score
            original_score = entity['score']
            adjusted_score = original_score * confidence_adjustment
            
            return {
                "original_score": original_score,
                "adjusted_score": adjusted_score,
                "is_valid": is_valid,
                "reason": reason,
                "llm_validated": True
            }
            
        except Exception as e:
            logger.error(f"LLM validation error: {e}")
            return {
                "original_score": entity['score'],
                "adjusted_score": entity['score'],
                "is_valid": True,  # Default to accepting if LLM fails
                "reason": f"LLM validation failed: {e}",
                "llm_validated": False
            }
    
    def _build_validation_prompt(self, entity_type: str, entity_text: str, context: str) -> str:
        """Build prompt for LLM validation"""
        
        prompts = {
            "PERSON": f"""Is "{entity_text}" a person's name in this context?

Context: {context}

Answer ONLY with:
- YES if it's clearly a person's name
- NO if it's a place, organization, or not a name
- UNCERTAIN if you're not sure

Reason: <brief explanation>""",

            "IT_ADDRESS": f"""Is "{entity_text}" a physical address in this context?

Context: {context}

Answer ONLY with:
- YES if it's a street address
- NO if it's just a city/country name or generic location
- UNCERTAIN if you're not sure

Reason: <brief explanation>""",

            "DATE_TIME": f"""Should the date "{entity_text}" be redacted in this legal context?

Context: {context}

Answer ONLY with:
- YES if it's a sensitive date (birth date, personal event)
- NO if it's a contract date, filing date, or legal reference
- UNCERTAIN if you're not sure

Reason: <brief explanation>""",
        }
        
        # Generic prompt for other types
        default_prompt = f"""Should "{entity_text}" ({entity_type}) be redacted as PII?

Context: {context}

Answer ONLY with:
- YES if it should be redacted
- NO if it's not sensitive in this context
- UNCERTAIN if you're not sure

Reason: <brief explanation>"""
        
        return prompts.get(entity_type, default_prompt)
    
    def detect_pii_from_context(self, context: str, hint: str = None) -> List[Dict]:
        """
        Use LLM to detect PII based on context clues
        Useful when regex fails due to irregular formatting
        
        Args:
            context: Text context (e.g., paragraph mentioning IBAN)
            hint: Optional hint about what to look for (e.g., "IBAN", "Codice Fiscale")
            
        Returns:
            List of potential PII entities detected by LLM
        """
        try:
            if hint:
                prompt = f"""Read this Italian legal text and identify any {hint} mentioned, even if formatted irregularly (with spaces, dashes, or unusual formatting).

Text: {context}

Extract the exact characters that form the {hint}, ignoring spaces and formatting.

Format your response as:
FOUND: <yes/no>
VALUE: <extracted value without spaces/dashes>
CONFIDENCE: <0.0-1.0>
ORIGINAL: <original text as written>

Example:
Text: "IBAN: IT60 - X054 2811"
FOUND: yes
VALUE: IT60X0542811
CONFIDENCE: 0.85
ORIGINAL: IT60 - X054 2811"""
            else:
                prompt = f"""Read this Italian legal text and identify ANY personal information (PII) that should be redacted, even if formatted irregularly.

Look for:
- Names (person, company)
- Codice Fiscale (16 characters)
- IBAN (IT + 25 characters)
- Phone numbers
- Email addresses
- Addresses

Text: {context}

List each PII found:
TYPE: <type>
VALUE: <normalized value>
CONFIDENCE: <0.0-1.0>
ORIGINAL: <as written in text>"""
            
            # Run LLM
            response = self._run_llm(prompt, max_tokens=200)
            
            # Parse response
            entities = self._parse_detection_response(response)
            
            return entities
            
        except Exception as e:
            logger.error(f"LLM detection error: {e}")
            return []
    
    def _parse_detection_response(self, response: str) -> List[Dict]:
        """
        Parse LLM response for detected entities
        
        Returns:
            List of detected entities
        """
        entities = []
        
        try:
            lines = response.strip().split('\n')
            current_entity = {}
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('FOUND:'):
                    found = 'yes' in line.lower()
                    if not found:
                        break
                        
                elif line.startswith('TYPE:'):
                    current_entity['entity_type'] = line.split(':', 1)[1].strip()
                    
                elif line.startswith('VALUE:'):
                    current_entity['text'] = line.split(':', 1)[1].strip()
                    
                elif line.startswith('CONFIDENCE:'):
                    conf_str = line.split(':', 1)[1].strip()
                    current_entity['score'] = float(conf_str)
                    
                elif line.startswith('ORIGINAL:'):
                    current_entity['original_text'] = line.split(':', 1)[1].strip()
                    
                    # Entity complete, add to list
                    if 'text' in current_entity:
                        entities.append({
                            'entity_type': current_entity.get('entity_type', 'UNKNOWN'),
                            'text': current_entity['text'],
                            'original_text': current_entity.get('original_text', current_entity['text']),
                            'score': current_entity.get('score', 0.7),
                            'source': 'llm_detection',
                            'start': -1,  # Unknown position
                            'end': -1
                        })
                    current_entity = {}
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
        
        return entities
    
    def _run_llm(self, prompt: str, max_tokens: int = 100, temperature: float = 0.1) -> str:
        """
        Run llama.cpp inference
        
        Args:
            prompt: Validation prompt
            max_tokens: Max output tokens
            temperature: Sampling temperature (low for deterministic)
            
        Returns:
            LLM response text
        """
        try:
            # Construct llama-cli command
            cmd = [
                self.llama_cpp_path,
                "-m", self.model_path,
                "-p", prompt,
                "-n", str(max_tokens),
                "--temp", str(temperature),
                "--log-disable",  # Disable logging
            ]
            
            # Run with timeout (<100ms target)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=0.1  # 100ms timeout
            )
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            logger.warning("LLM inference timeout (>100ms)")
            return "UNCERTAIN\nReason: Timeout"
        except Exception as e:
            logger.error(f"LLM execution error: {e}")
            return "UNCERTAIN\nReason: Execution error"
    
    def _parse_llm_response(self, response: str) -> tuple:
        """
        Parse LLM response
        
        Returns:
            (is_valid: bool, confidence_adjustment: float, reason: str)
        """
        response_lower = response.lower()
        
        # Extract decision
        if "yes" in response_lower:
            is_valid = True
            confidence_adjustment = 1.1  # Boost confidence by 10%
        elif "no" in response_lower:
            is_valid = False
            confidence_adjustment = 0.5  # Reduce confidence by 50%
        else:  # UNCERTAIN
            is_valid = True  # Default to accepting
            confidence_adjustment = 0.9  # Slightly reduce confidence
        
        # Extract reason
        reason_parts = response.split("Reason:", 1)
        reason = reason_parts[1].strip() if len(reason_parts) > 1 else "No reason provided"
        
        return is_valid, confidence_adjustment, reason
    
    def validate_batch(self, entities: List[Dict], context: str) -> List[Dict]:
        """
        Validate multiple entities (batch processing)
        
        Args:
            entities: List of entity dicts
            context: Full document text
            
        Returns:
            List of entities with validation results
        """
        validated = []
        
        for entity in entities:
            validation = self.validate_entity(entity, context)
            
            # Merge validation results into entity
            entity_validated = {
                **entity,
                **validation
            }
            
            validated.append(entity_validated)
        
        return validated


# Example usage
if __name__ == "__main__":
    validator = LLMValidator()
    
    # Test entity
    entity = {
        "entity_type": "PERSON",
        "text": "Via Roma",
        "start": 50,
        "end": 58,
        "score": 0.85
    }
    
    context = "Il contratto è stato firmato presso l'ufficio in Via Roma 123, Milano."
    
    result = validator.validate_entity(entity, context)
    print(f"Validation: {result}")
    print(f"Adjusted score: {result['adjusted_score']:.2f} (original: {result['original_score']:.2f})")
