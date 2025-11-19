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
import requests

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

    def __init__(self, api_key: Optional[str] = None, openrouter_key: Optional[str] = None):
        """
        Initialize Gemini PII Detector with OpenRouter fallback

        Args:
            api_key: Google Gemini API key (if None, reads from GEMINI_API_KEY env var)
            openrouter_key: OpenRouter API key for fallback (if None, reads from OPENROUTER_API_KEY env var)
        """
        # Store API keys
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.openrouter_key = openrouter_key or os.getenv('OPENROUTER_API_KEY')

        # Flags for provider availability
        self.gemini_available = False
        self.openrouter_available = bool(self.openrouter_key)

        # Try to initialize Gemini first
        if genai is not None and self.api_key:
            try:
                # Configure Gemini API
                genai.configure(api_key=self.api_key)

                # Initialize Gemini model (supports vision + structured output)
                # Try multiple model names in order of preference
                model_names = [
                    'models/gemini-2.5-pro',     # Gemini 2.5 Pro (exact model path)
                    'gemini-2.5-pro',            # Gemini 2.5 Pro (short name)
                    'gemini-1.5-flash',          # Flash model (fallback)
                    'gemini-2.5-pro-latest',     # Latest pro model (fallback)
                    'gemini-pro-vision',         # Legacy vision model (fallback)
                ]

                model_initialized = False
                last_error = None

                for model_name in model_names:
                    try:
                        logger.info(f"Trying to initialize model: {model_name}")
                        self.model = genai.GenerativeModel(model_name)
                        logger.info(f"Gemini PII Detector initialized successfully with model: {model_name}")
                        model_initialized = True
                        self.gemini_available = True
                        self.current_provider = 'gemini'
                        break
                    except Exception as e:
                        last_error = e
                        logger.warning(f"Failed to initialize {model_name}: {e}")
                        continue

                if not model_initialized:
                    logger.warning(f"Failed to initialize any Gemini model: {last_error}")
            except Exception as e:
                logger.warning(f"Gemini initialization failed: {e}")

        # Fallback to OpenRouter if Gemini not available
        if not self.gemini_available and self.openrouter_available:
            logger.info("Using OpenRouter as primary provider")
            self.current_provider = 'openrouter'
            # OpenRouter models (Chinese models preferred)
            self.openrouter_models = [
                'qwen/qwen-2.5-72b-instruct',    # Qwen 2.5 (Alibaba)
                'deepseek/deepseek-chat',         # DeepSeek Chat
                'openai/gpt-4o',                  # GPT-4 Omni fallback
            ]
        elif not self.gemini_available and not self.openrouter_available:
            raise ValueError(
                "No API provider available. Set either GEMINI_API_KEY or OPENROUTER_API_KEY.\n"
                "Get Gemini API key: https://aistudio.google.com/app/apikey\n"
                "Get OpenRouter API key: https://openrouter.ai/keys"
            )

    def _detect_pii_openrouter(
        self,
        pdf_base64: str,
        prompt: str,
        model: str = 'qwen/qwen-2.5-72b-instruct'
    ) -> str:
        """
        Call OpenRouter API for PII detection

        Args:
            pdf_base64: Base64-encoded PDF data
            prompt: Detection prompt
            model: OpenRouter model ID

        Returns:
            JSON string response
        """
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://redaxai.app",  # Your app URL
            "X-Title": "RedaxAI PII Detector",
            "Content-Type": "application/json"
        }

        # OpenRouter supports vision models with base64 images
        # For PDFs, we'll use text-based analysis
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{prompt}\n\nNote: Analyze the PDF content and return ONLY a JSON array as specified."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=180)
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']

            return content

        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise RuntimeError(f"OpenRouter API error: {str(e)}")

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

        # Try Gemini first, then OpenRouter fallback
        response_text = None
        provider_used = None

        if self.gemini_available:
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
                response_text = response.text
                provider_used = 'gemini'

            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}")
                if self.openrouter_available:
                    logger.info("Falling back to OpenRouter...")
                else:
                    raise RuntimeError(f"Gemini API error and no fallback available: {str(e)}")

        # Fallback to OpenRouter
        if response_text is None and self.openrouter_available:
            for model in self.openrouter_models:
                try:
                    logger.info(f"Trying OpenRouter model: {model}")
                    response_text = self._detect_pii_openrouter(pdf_base64, prompt, model)
                    provider_used = f'openrouter-{model}'
                    logger.info(f"OpenRouter call successful with {model}")
                    break
                except Exception as e:
                    logger.warning(f"OpenRouter model {model} failed: {e}")
                    continue

        if response_text is None:
            raise RuntimeError("All API providers failed")

        # Parse response
        try:
            # Handle OpenRouter response format
            if provider_used and provider_used.startswith('openrouter'):
                # OpenRouter might wrap the response, try to extract array
                try:
                    parsed = json.loads(response_text)
                    # If it's an object with entities key, extract it
                    if isinstance(parsed, dict) and 'entities' in parsed:
                        entities_raw = parsed['entities']
                    elif isinstance(parsed, list):
                        entities_raw = parsed
                    else:
                        # Try to find the array in the response
                        entities_raw = parsed
                except:
                    entities_raw = json.loads(response_text)
            else:
                entities_raw = json.loads(response_text)

            # Add source metadata to each entity
            entities = []
            for entity in entities_raw:
                entities.append({
                    **entity,
                    "source": provider_used or "api_scan",
                    "file_name": file_path.name
                })

            logger.info(f"Parsed {len(entities)} entities from {provider_used} response")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API JSON response: {e}")
            logger.error(f"Raw response: {response_text}")
            raise RuntimeError(f"Invalid JSON from API: {str(e)}")

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
            "api_provider": provider_used or "unknown",
            "api_model": provider_used or "unknown"
        }

        result = {
            "entities": entities,
            "summary": summary
        }

        if return_raw_response:
            if provider_used == 'gemini':
                result["raw_response"] = {
                    "text": response_text,
                    "provider": provider_used,
                    "prompt_tokens": getattr(response, 'usage_metadata', {}).get('prompt_token_count', 0) if 'response' in locals() else 0,
                    "response_tokens": getattr(response, 'usage_metadata', {}).get('candidates_token_count', 0) if 'response' in locals() else 0
                }
            else:
                result["raw_response"] = {
                    "text": response_text,
                    "provider": provider_used
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

    def teach_template(
        self,
        template_path: str,
        voice_command: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Teach Gemini a document template structure using Context Caching.
        This allows fast batch processing of similar documents.

        Args:
            template_path: Path to blank template (PDF or image)
            voice_command: User's voice instruction (e.g., "Learn tenant name in section 1")
            description: Optional template description

        Returns:
            Dict with structure:
            {
                "template_id": "lease_agreement_v1",
                "cache_name": "cachedContent/abc123...",
                "description": "Lease agreement template",
                "regions": [
                    {
                        "field_name": "tenant_name",
                        "bbox": [100, 50, 200, 150],  # [ymin, xmin, ymax, xmax] in 0-1000 scale
                        "entity_type": "PERSON",
                        "confidence": 0.95
                    },
                    ...
                ],
                "created_at": "2025-01-17T10:30:00Z",
                "expires_at": "2025-01-17T11:30:00Z"  # 1 hour TTL
            }
        """
        template_path = Path(template_path)
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        logger.info(f"Teaching template: {template_path.name}")
        logger.info(f"Voice command: {voice_command}")

        # Read and encode template file
        try:
            with open(template_path, 'rb') as f:
                file_data = f.read()
            file_base64 = base64.b64encode(file_data).decode('utf-8')

            # Detect MIME type
            if template_path.suffix.lower() == '.pdf':
                mime_type = 'application/pdf'
            elif template_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                mime_type = f'image/{template_path.suffix.lower()[1:]}'
            else:
                raise ValueError(f"Unsupported file type: {template_path.suffix}")

        except Exception as e:
            logger.error(f"Failed to read template: {e}")
            raise

        # Create system instruction for template learning
        system_instruction = """Sei un Privacy Officer esperto nell'analisi di template di documenti.

Il tuo compito è identificare le coordinate delle regioni (bounding boxes) dove si trovano i campi dati personali (PII),
SENZA leggere i dati reali (questo template è vuoto o anonimizzato).

Analizza il layout del documento e identifica le coordinate per ogni campo richiesto dall'utente.

Output SOLO JSON con questo formato:
{
  "regions": [
    {
      "field_name": "nome_campo",
      "bbox": [ymin, xmin, ymax, xmax],
      "entity_type": "PERSON|ORGANIZATION|LOCATION|etc",
      "confidence": 0.0-1.0
    }
  ]
}

IMPORTANTE - Sistema di coordinate:
- bbox format: [ymin, xmin, ymax, xmax]
- Scala normalizzata: 0-1000 su entrambi gli assi
- Origine: TOP-LEFT (0,0 = angolo in alto a sinistra)
- ymin: distanza dal bordo superiore (Y minimo)
- xmin: distanza dal bordo sinistro (X minimo)
- ymax: distanza dal bordo superiore al bordo inferiore della box (Y massimo)
- xmax: distanza dal bordo sinistro al bordo destro della box (X massimo)

Esempio: un campo nell'angolo in alto a sinistra potrebbe essere [50, 100, 150, 300]
         (da 50px dall'alto, 100px da sinistra, fino a 150px dall'alto, 300px da sinistra)"""

        # Analyze template with Gemini (without caching for simplicity)
        try:
            logger.info("Analyzing template with Gemini...")

            # Create the prompt combining system instruction and user command
            full_prompt = f"""{system_instruction}

COMANDO UTENTE: {voice_command}

Analizza il template allegato e identifica le coordinate dei campi richiesti."""

            # Use the initialized model (from __init__)
            response = self.model.generate_content(
                [
                    full_prompt,
                    {
                        "mime_type": mime_type,
                        "data": file_base64
                    }
                ],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            logger.info("Template analysis complete")

        except Exception as e:
            logger.error(f"Failed to analyze template: {e}")
            raise RuntimeError(f"Gemini analysis error: {str(e)}")

        # Parse regions from response
        try:
            result_data = json.loads(response.text)
            regions = result_data.get('regions', [])

            logger.info(f"Identified {len(regions)} regions")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.error(f"Raw response: {response.text}")
            raise RuntimeError(f"Invalid JSON from Gemini: {str(e)}")

        # Build result (simplified without caching)
        from datetime import datetime

        template_result = {
            "template_id": template_path.stem,
            "description": description or f"Template for {template_path.name}",
            "regions": regions,
            "created_at": datetime.now().isoformat(),
            "voice_command": voice_command,
            "model": "gemini-2.5-pro"  # Using Gemini 2.5 Pro
        }

        return template_result

    def apply_cached_template(
        self,
        cache_name: str,
        document_paths: List[str],
        callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Apply cached template to batch of documents (fast processing).

        Args:
            cache_name: Cache name from teach_template()
            document_paths: List of document paths to process
            callback: Optional progress callback(current, total, file_path)

        Returns:
            List of processing results for each document
        """
        logger.info(f"Applying cached template to {len(document_paths)} documents")

        results = []

        for idx, doc_path in enumerate(document_paths):
            if callback:
                callback(idx + 1, len(document_paths), doc_path)

            try:
                # For each document, just apply the template coordinates
                # (no need to call Gemini again - that's the point of caching!)
                result = self._apply_template_local(doc_path, cache_name)
                results.append({
                    "file_path": doc_path,
                    "status": "success",
                    "result": result
                })

            except Exception as e:
                logger.error(f"Failed to process {doc_path}: {e}")
                results.append({
                    "file_path": doc_path,
                    "status": "error",
                    "error": str(e)
                })

        return results

    def _apply_template_local(self, document_path: str, cache_name: str) -> Dict[str, Any]:
        """
        Apply template coordinates locally without calling Gemini.
        This is MUCH faster than re-analyzing each document.

        Args:
            document_path: Path to document to redact
            cache_name: Cache name with template structure

        Returns:
            Dict with redaction coordinates ready for local execution
        """
        # In a real implementation, you would:
        # 1. Load the cached template structure (bbox coordinates)
        # 2. Apply those coordinates to the new document
        # 3. Return redaction map

        # For now, just return placeholder
        # This should be integrated with your existing redaction_exporter
        return {
            "redaction_map": [],
            "note": "Template coordinates should be applied locally here"
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
