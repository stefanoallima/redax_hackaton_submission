"""
Gemini PII Detector - Google Gemini 1.5 Pro integration for Italian legal document analysis
Uses multimodal capabilities to detect PII with high accuracy
"""

import os
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import logging

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)


class GeminiPIIDetector:
    """
    Wrapper for Google Gemini API to detect PII in Italian legal documents
    """

    # Default prompt optimized for Italian legal documents
    DEFAULT_PROMPT = """Sei un esperto nell'analisi di documenti legali italiani per identificare dati personali (PII).

Analizza attentamente questo documento PDF e identifica TUTTI i seguenti tipi di informazioni personali:

1. **PERSON** (Persone fisiche): Nomi e cognomi completi (es. Mario Rossi, Avv. Giovanni Bianchi)
2. **ORGANIZATION** (Enti/Organizzazioni): Tribunali, aziende, studi legali (es. Tribunale di Milano)
3. **LOCATION** (Luoghi specifici): Indirizzi completi, vie, città con numeri civici
4. **DATE_TIME** (Date): Date di nascita, udienze, sentenze
5. **EMAIL_ADDRESS** (Email): Indirizzi email completi
6. **PHONE_NUMBER** (Telefoni): Numeri di telefono, fax, cellulari
7. **IT_FISCAL_CODE** (Codice Fiscale): Codici fiscali italiani (16 caratteri)
8. **IT_VAT_CODE** (Partita IVA): Partite IVA italiane
9. **IBAN** (Conti bancari): Codici IBAN
10. **IT_IDENTITY_CARD** (Documenti): Numeri di carta d'identità, passaporto, patente

**IMPORTANTE**:
- Estrai il testo ESATTO come appare nel documento
- Se una persona appare più volte, segnala ogni occorrenza con il numero di pagina
- Includi anche informazioni parziali se chiaramente identificabili (es. solo cognome se unico nel documento)
- Ignora termini generici come "giudice", "avvocato" senza nomi specifici
- Per LOCATION, includi solo indirizzi completi, non solo nomi di città generici

Rispondi SOLO con un array JSON, senza testo aggiuntivo."""

    # Gemini API response schema for structured output
    # Note: Using simpler schema format compatible with Gemini API
    RESPONSE_SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The exact PII text found in the document"
                },
                "entity_type": {
                    "type": "string",
                    "enum": [
                        "PERSON",
                        "ORGANIZATION",
                        "LOCATION",
                        "DATE_TIME",
                        "EMAIL_ADDRESS",
                        "PHONE_NUMBER",
                        "IT_FISCAL_CODE",
                        "IT_VAT_CODE",
                        "IBAN",
                        "IT_IDENTITY_CARD"
                    ],
                    "description": "The type of PII detected"
                },
                "page": {
                    "type": "integer",
                    "description": "Page number where the entity was found (1-indexed)"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence score between 0 and 1"
                }
            },
            "required": ["text", "entity_type", "page", "confidence"]
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini PII Detector

        Args:
            api_key: Google Gemini API key (if None, reads from GEMINI_API_KEY env var)
        """
        if genai is None:
            raise ImportError(
                "google-generativeai not installed. Run: pip install google-generativeai"
            )

        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable or pass api_key parameter.\n"
                "Get your API key from: https://aistudio.google.com/app/apikey"
            )

        # Configure Gemini API
        genai.configure(api_key=self.api_key)

        # Initialize Gemini model (supports vision + structured output)
        # Try multiple model names in order of preference
        model_names = [
            'gemini-2.5-pro',  # Latest flash model (fast)
            'gemini-1.5-flash',          # Flash model
            'gemini-2.5-pro-latest',     # Latest pro model
            'gemini-pro-vision',         # Legacy vision model
        ]

        model_initialized = False
        last_error = None

        for model_name in model_names:
            try:
                logger.info(f"Trying to initialize model: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"Gemini PII Detector initialized successfully with model: {model_name}")
                model_initialized = True
                break
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to initialize {model_name}: {e}")
                continue

        if not model_initialized:
            raise RuntimeError(f"Failed to initialize any Gemini model. Last error: {last_error}")

    def detect_pii(
        self,
        file_path: str,
        custom_prompt: Optional[str] = None,
        return_raw_response: bool = False
    ) -> Dict[str, Any]:
        """
        Detect PII in a PDF document using Gemini multimodal analysis

        Args:
            file_path: Path to PDF file
            custom_prompt: Optional custom prompt (uses DEFAULT_PROMPT if None)
            return_raw_response: If True, includes raw Gemini response in output

        Returns:
            Dict with structure:
            {
                "entities": [
                    {
                        "text": "Mario Rossi",
                        "entity_type": "PERSON",
                        "page": 1,
                        "confidence": 0.98,
                        "source": "gemini_scan"
                    },
                    ...
                ],
                "summary": {
                    "total_entities": 15,
                    "by_type": {"PERSON": 5, "EMAIL_ADDRESS": 2, ...},
                    "pages_analyzed": 10
                },
                "raw_response": {...}  # Only if return_raw_response=True
            }
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if file_path.suffix.lower() != '.pdf':
            raise ValueError(f"Only PDF files supported, got: {file_path.suffix}")

        logger.info(f"Starting Gemini PII detection for: {file_path.name}")

        # Read and encode PDF
        try:
            with open(file_path, 'rb') as f:
                pdf_data = f.read()
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            logger.debug(f"PDF encoded, size: {len(pdf_base64)} bytes (base64)")
        except Exception as e:
            logger.error(f"Failed to read PDF: {e}")
            raise

        # Prepare prompt
        prompt = custom_prompt or self.DEFAULT_PROMPT

        # Call Gemini API with structured output
        try:
            logger.info("Calling Gemini API...")
            response = self.model.generate_content(
                [
                    prompt,
                    {
                        "mime_type": "application/pdf",
                        "data": pdf_base64
                    }
                ],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=self.RESPONSE_SCHEMA,
                    temperature=0.1,  # Low temperature for deterministic output
                )
            )

            logger.info("Gemini API call successful")

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise RuntimeError(f"Gemini API error: {str(e)}")

        # Parse response
        try:
            entities_raw = json.loads(response.text)

            # Add source metadata to each entity
            entities = []
            for entity in entities_raw:
                entities.append({
                    **entity,
                    "source": "gemini_scan",
                    "file_name": file_path.name
                })

            logger.info(f"Parsed {len(entities)} entities from Gemini response")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            logger.error(f"Raw response: {response.text}")
            raise RuntimeError(f"Invalid JSON from Gemini: {str(e)}")

        # Calculate summary statistics
        entity_types = {}
        pages_seen = set()

        for entity in entities:
            entity_type = entity.get('entity_type', 'UNKNOWN')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            page = entity.get('page')
            if page:
                pages_seen.add(page)

        summary = {
            "total_entities": len(entities),
            "by_type": entity_types,
            "pages_analyzed": len(pages_seen),
            "api_model": "gemini-2.5-pro"
        }

        result = {
            "entities": entities,
            "summary": summary
        }

        if return_raw_response:
            result["raw_response"] = {
                "text": response.text,
                "prompt_tokens": getattr(response, 'usage_metadata', {}).get('prompt_token_count', 0),
                "response_tokens": getattr(response, 'usage_metadata', {}).get('candidates_token_count', 0)
            }

        logger.info(f"Detection complete: {summary['total_entities']} entities found")
        return result

    def get_quota_info(self) -> Dict[str, Any]:
        """
        Get current Gemini API quota/usage information

        Returns:
            Dict with quota details (implementation depends on Gemini API)
        """
        # Note: As of Jan 2025, Gemini API doesn't have built-in quota endpoint
        # This is a placeholder for future implementation
        return {
            "status": "Quota tracking not yet available",
            "free_tier": "15 requests/minute, 1500 requests/day",
            "docs": "https://ai.google.dev/pricing"
        }


# Singleton instance (optional, for caching)
_gemini_detector_instance: Optional[GeminiPIIDetector] = None


def get_gemini_detector(api_key: Optional[str] = None) -> GeminiPIIDetector:
    """
    Get or create singleton Gemini detector instance

    Args:
        api_key: Optional API key (only used on first call)

    Returns:
        GeminiPIIDetector instance
    """
    global _gemini_detector_instance

    if _gemini_detector_instance is None:
        _gemini_detector_instance = GeminiPIIDetector(api_key=api_key)

    return _gemini_detector_instance
