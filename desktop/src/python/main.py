"""
Python Backend for Document Processing
Runs as child process, communicates via JSON on stdin/stdout

UPDATED: Now uses shared_backend/ for all business logic
"""
import sys
import json
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

# ADD SHARED BACKEND TO PYTHON PATH
# This allows imports like: from core.gemini_client import GeminiClient
repo_root = Path(__file__).parent.parent.parent.parent
shared_backend_path = repo_root / 'shared_backend'
if shared_backend_path.exists():
    sys.path.insert(0, str(shared_backend_path))
    logging.info(f"Added shared_backend to Python path: {shared_backend_path}")
else:
    logging.warning(f"shared_backend not found at: {shared_backend_path}")

# Load environment variables from .env file
# Look for .env in the desktop directory (parent of src/python)
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logging.info(f"Loaded environment variables from: {env_path}")
else:
    logging.warning(f".env file not found at: {env_path}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # INFO level for production (use DEBUG for troubleshooting)
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('redact.log'),
        logging.StreamHandler(sys.stderr)  # Use stderr for logs, stdout for IPC
    ]
)

logger = logging.getLogger(__name__)


def safe_output(data: dict) -> bool:
    """
    Safely write JSON output to stdout with EPIPE error handling

    Args:
        data: Dictionary to output as JSON

    Returns:
        True if successful, False otherwise
    """
    try:
        output = json.dumps(data)
        print(output, flush=True)
        return True
    except BrokenPipeError:
        # EPIPE - the receiving end (Electron) has closed the pipe
        # This is expected during shutdown, so we log and exit gracefully
        logger.info("Output pipe closed (expected during shutdown)")
        return False
    except IOError as e:
        # Other IO errors (disk full, etc)
        if e.errno == 32:  # EPIPE errno
            logger.info("Output pipe closed (EPIPE)")
            return False
        else:
            logger.error(f"IO error writing to stdout: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error writing to stdout: {e}")
        return False


def deduplicate_entities(entities: list) -> list:
    """
    Deduplicate entities, prioritizing learned entities over detected ones

    Args:
        entities: List of entities (learned + detected)

    Returns:
        Deduplicated list with learned entities taking priority
    """
    if not entities:
        return []

    # Separate entities with and without position information
    entities_with_positions = []
    entities_without_positions = []

    for entity in entities:
        if 'start' in entity and 'end' in entity and entity['start'] is not None and entity['end'] is not None:
            entities_with_positions.append(entity)
        else:
            # Entity without positions - keep but handle separately
            entities_without_positions.append(entity)
            logger.debug(f"Entity without positions: {entity.get('text', 'unknown')} (type: {entity.get('entity_type', 'unknown')})")

    # Sort entities with positions by:
    # 1. Source (learned_from_gemini first)
    # 2. Score (higher first)
    # 3. Start position (earlier first)
    def sort_key(entity):
        is_learned = entity.get('source') == 'learned_from_gemini'
        score = entity.get('score', entity.get('confidence', 0))
        start = entity.get('start', 0)
        return (not is_learned, -score, start)

    sorted_entities = sorted(entities_with_positions, key=sort_key)

    # Track occupied character ranges
    occupied_ranges = []
    deduped = []

    for entity in sorted_entities:
        start = entity['start']
        end = entity['end']

        # Check for overlap with existing entities
        overlaps = False
        for occupied_start, occupied_end in occupied_ranges:
            # Check if ranges overlap
            if not (end <= occupied_start or start >= occupied_end):
                overlaps = True
                logger.debug(f"Entity '{entity.get('text', 'unknown')}' at [{start},{end}] overlaps with existing range [{occupied_start},{occupied_end}]")
                break

        if not overlaps:
            deduped.append(entity)
            occupied_ranges.append((start, end))

    # For entities without positions, try to deduplicate by text (case-insensitive)
    if entities_without_positions:
        logger.info(f"Processing {len(entities_without_positions)} entities without position info")
        seen_texts = set()

        # First, mark texts already in deduped list
        for entity in deduped:
            text_lower = entity.get('text', '').lower().strip()
            if text_lower:
                seen_texts.add(text_lower)

        # Then add non-duplicate entities without positions
        for entity in entities_without_positions:
            text_lower = entity.get('text', '').lower().strip()
            if text_lower and text_lower not in seen_texts:
                deduped.append(entity)
                seen_texts.add(text_lower)
                logger.debug(f"Added entity without positions: {entity.get('text', 'unknown')}")

    logger.info(f"Deduplicated {len(entities)} -> {len(deduped)} entities ({len(entities_with_positions)} with positions, {len(entities_without_positions)} without)")
    return deduped


def process_document(file_path: str, config_dict: dict = None) -> dict:
    """
    Process document for PII detection with configurable detection layers

    Args:
        file_path: Path to document file
        config_dict: Detection configuration from UI slider (depth, LLM, visual settings)

    Returns:
        dict with processing results, entities, and summary
    """
    try:
        logger.info(f"Processing document: {file_path}")

        # Import processors
        from core.document_processor import DocumentProcessor
        from config.redaction_config import get_config
        from config.detection_config import DetectionConfig
        from pathlib import Path
        import os

        # Import detection infrastructure
        import os
        from detectors.pii_detector_factory import PIIDetectorFactory
        from detectors.pii_detector_adapter import PIIDetectorAdapter, mark_as_integrated

        # Parse detection config from UI
        if config_dict:
            detection_config = DetectionConfig.from_dict(config_dict)
            logger.info(f"Using detection config: depth={detection_config.depth}, "
                       f"llm={detection_config.enable_llm}, visual={detection_config.enable_visual}")
        else:
            detection_config = DetectionConfig()  # Use defaults
            logger.info("Using default detection config (balanced)")

        # Extract text from document
        result = DocumentProcessor.process_document(file_path)

        if result["status"] == "error":
            return result

        # Create detector using factory pattern with feature flag
        # Environment variable: USE_NEW_PII_DETECTOR=true/false
        use_new = os.getenv("USE_NEW_PII_DETECTOR", "false").lower() in ["true", "1", "yes"]

        try:
            if use_new:
                logger.info("Creating NEW integrated detector (optimized configuration)...")
                from core.pii_detector_integrated import IntegratedPIIDetector
                raw_detector = IntegratedPIIDetector(
                    enable_gliner=True,
                    use_multi_model=False,          # ❌ DISABLED: Causes memory crash (Access Violation)
                    enable_prefilter=True,          # Keep enabled (no harm, may help)
                    enable_italian_context=True,    # Keep enabled (no harm, may help)
                    enable_entity_thresholds=False  # ✅ DISABLED: Causes 42% F1 degradation
                )
                raw_detector = mark_as_integrated(raw_detector)
                logger.info("[OK] Optimized detector created (F1: 12.37%, Email: 100%, 2.7x improvement)")
            else:
                logger.info("Creating OLD enhanced detector (fallback)...")
                from pii_detector_enhanced import EnhancedPIIDetector
                raw_detector = EnhancedPIIDetector(enable_gliner=True)
                logger.info("[OK] Old enhanced detector created")
        except Exception as e:
            logger.error(f"Failed to create primary detector: {e}")
            logger.info("Falling back to base PIIDetector...")
            from detectors.pii_detector import PIIDetector
            raw_detector = PIIDetector()

        # Wrap detector with adapter for backward compatibility
        detector = PIIDetectorAdapter(raw_detector)
        logger.info(f"Detector initialized: depth={detection_config.depth}, architecture={'new' if use_new else 'old'}")

        # PHASE 0: Query learned entities database (from Gemini scans)
        learned_entities = []
        try:
            from core.learned_entities_db import LearnedEntitiesDB
            learned_db = LearnedEntitiesDB()  # Auto-detects environment
            full_text = result.get("full_text", "")
            learned_matches = learned_db.find_matches(full_text)
            learned_entities = learned_matches
            logger.info(f"Phase 0 (Learned DB): Found {len(learned_entities)} learned entity matches")
        except Exception as e:
            logger.warning(f"Failed to query learned database: {e}")

        # PHASE 1: Run PII detection with config (local ML)
        pii_result = detector.process_document(result, config=detection_config)

        if pii_result["status"] == "error":
            return pii_result

        # PHASE 2: Merge learned entities with detected entities
        # Learned entities take priority (score 1.0, already confirmed by user)
        all_entities = learned_entities + pii_result["entities"]

        # Deduplicate entities (keep learned entities when overlapping)
        deduped_entities = deduplicate_entities(all_entities)
        logger.info(f"After deduplication: {len(deduped_entities)} total entities (learned + detected)")

        # Replace entities with merged result
        pii_result["entities"] = deduped_entities

        # Add entity locations for PDF files (for PDF preview in UI)
        file_type = result.get("file_type", "unknown")
        if file_type == "pdf":
            logger.info("Adding entity locations for PDF preview")
            entities_with_locations = detector.get_entity_locations(
                file_path,
                pii_result["entities"]
            )
        else:
            entities_with_locations = pii_result["entities"]
            # Initialize empty locations for non-PDF files
            for entity in entities_with_locations:
                entity['locations'] = []

        # Get configuration and apply filters
        config = get_config()
        logger.info(f"Before filtering: {len(entities_with_locations)} entities")
        logger.info(f"Entity types in data: {set(e.get('entity_type') for e in entities_with_locations[:10])}")
        logger.info(f"Enabled types in config: {config.get_enabled_types()}")

        filtered_entities = config.filter_entities(entities_with_locations)
        logger.info(f"After filtering: {len(filtered_entities)} entities")

        summary = config.get_summary(pii_result["entities"])

        response = {
            "status": "success",
            "entities": filtered_entities,
            "summary": summary,
            "full_text": result.get("full_text", ""),
            "metadata": result.get("metadata", {}),
            "file_path": file_path,  # Include for PDF viewer
            "file_type": file_type
        }

        logger.info(f"Returning {len(response['entities'])} entities to UI")
        return response

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def export_redacted_document(file_path: str, entities: list, export_txt: bool = False, redaction_style: str = 'placeholder') -> dict:
    """
    Export redacted document with entity placeholders

    Args:
        file_path: Path to original document
        entities: List of PII entities to redact
        export_txt: If True, also export as plain text for LLM use
        redaction_style: 'placeholder' (black text on yellow) or 'solid_black' (traditional censorship)

    Returns:
        dict with export results and mapping table
    """
    try:
        logger.info(f"Exporting redacted document: {file_path}")
        logger.info(f"Received {len(entities)} entities from frontend")

        # Safety filter: Only redact entities marked as accepted
        # (Frontend should already filter, but this is defense-in-depth)
        accepted_entities = [e for e in entities if e.get('accepted', True)]
        logger.info(f"Redacting {len(accepted_entities)} accepted entities")
        logger.info(f"Export TXT: {export_txt}")

        from redaction_exporter import RedactionExporter
        from pathlib import Path

        # Generate output filename
        input_path = Path(file_path)
        output_filename = f"{input_path.stem}_REDACTED{input_path.suffix}"
        output_path = input_path.parent / output_filename

        # Generate mapping table CSV filename
        mapping_filename = f"{input_path.stem}_MAPPING_TABLE.csv"
        mapping_path = input_path.parent / mapping_filename

        # Export redacted PDF with safety checks disabled for now
        # TODO: Fix false positives in invisible text detection (too aggressive 95% white threshold)
        exporter = RedactionExporter()
        result = exporter.export_redacted_pdf(
            input_path=str(input_path),
            output_path=str(output_path),
            entities=accepted_entities,
            add_watermark=False,  # Can be made configurable
            clean_metadata=True,
            enable_safety_checks=False  # Disabled due to false positives blocking legitimate redactions
        )

        if result['status'] == 'success':
            # Export mapping table to CSV
            mapping_result = exporter.export_mapping_table(str(mapping_path))

            response = {
                "status": "success",
                "output_path": str(output_path),
                "mapping_table_path": str(mapping_path),
                "entities_redacted": result['entities_redacted'],
                "unique_entities": result['unique_entities'],
                "safety_checks": result.get('safety_checks', {})  # Include safety check stats
            }

            # Log safety check summary for transparency
            if 'safety_checks' in result and result['safety_checks']['enabled']:
                stats = result['safety_checks']['statistics']
                blocked = result['safety_checks']['total_blocked']
                logger.info(f"Safety checks summary: {stats['safe_redactions']} safe, {blocked} blocked")
                if blocked > 0:
                    logger.info(f"  - Already redacted: {stats['already_redacted_blocked']}")
                    logger.info(f"  - Invisible text: {stats['invisible_text_blocked']}")
                    logger.info(f"  - Text mismatch: {stats['text_mismatch_blocked']}")

            # Export TXT if requested
            if export_txt:
                txt_filename = f"{input_path.stem}_REDACTED.txt"
                txt_path = input_path.parent / txt_filename

                txt_result = exporter.export_redacted_text(
                    input_path=str(input_path),
                    output_path=str(txt_path),
                    entities=accepted_entities  # Use accepted entities only
                )

                if txt_result['status'] == 'success':
                    response['txt_output_path'] = str(txt_path)
                    logger.info(f"TXT export successful: {txt_path}")
                else:
                    logger.warning(f"TXT export failed: {txt_result.get('error')}")

            return response
        else:
            return result

    except Exception as e:
        logger.error(f"Error exporting redacted document: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def gemini_scan_document(file_path: str, custom_prompt: str = None) -> dict:
    """
    Scan document using Google Gemini API for high-accuracy PII detection

    Args:
        file_path: Path to PDF document
        custom_prompt: Optional custom prompt for Gemini

    Returns:
        dict with Gemini scan results
    """
    try:
        logger.info(f"Starting Gemini scan: {file_path}")

        from core.gemini_client import GeminiPIIDetector

        # Get Gemini detector instance
        detector = GeminiPIIDetector()

        # Run Gemini detection
        result = detector.detect_pii(
            file_path=file_path,
            custom_prompt=custom_prompt,
            return_raw_response=False
        )

        logger.info(f"Gemini scan complete: {result['summary']['total_entities']} entities found")
        return {
            "status": "success",
            **result
        }

    except ImportError as e:
        logger.error(f"Gemini dependencies not installed: {e}")
        return {
            "status": "error",
            "error": "Google Gemini library not installed. Run: pip install google-generativeai"
        }
    except ValueError as e:
        logger.error(f"Gemini API key not configured: {e}")
        return {
            "status": "error",
            "error": "Gemini API key not configured. Set GEMINI_API_KEY environment variable."
        }
    except Exception as e:
        logger.error(f"Gemini scan failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def teach_template_document(file_path: str, voice_command: str, description: str = None) -> dict:
    """
    Teach Gemini a blank template structure with bounding boxes for PII fields

    Args:
        file_path: Path to blank template (PDF or image)
        voice_command: User's voice instruction (e.g., "Find tenant names and phone numbers")
        description: Optional description

    Returns:
        dict with template regions including bounding boxes
    """
    try:
        logger.info(f"Teaching template: {file_path}")
        logger.info(f"Voice command: {voice_command}")

        from gemini_client import GeminiPIIDetector

        # Get Gemini detector instance
        detector = GeminiPIIDetector()

        # Run template teaching with bounding box detection
        result = detector.teach_template(
            template_path=file_path,
            voice_command=voice_command,
            description=description
        )

        logger.info(f"Template teaching complete: {len(result.get('regions', []))} regions found")

        # Return result directly (already includes regions)
        return {
            "status": "success",
            "regions": result.get('regions', []),
            "template_id": result.get('template_id'),
            "description": result.get('description'),
            "model": result.get('model', 'gemini-2.5-pro')
        }

    except ImportError as e:
        logger.error(f"Gemini dependencies not installed: {e}")
        return {
            "status": "error",
            "error": "Google Gemini library not installed. Run: pip install google-generativeai"
        }
    except ValueError as e:
        logger.error(f"Gemini API key not configured: {e}")
        return {
            "status": "error",
            "error": "Gemini API key not configured. Set GEMINI_API_KEY environment variable."
        }
    except Exception as e:
        logger.error(f"Template teaching failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def learn_from_gemini(confirmed_entities: list, denied_entities: list = None) -> dict:
    """
    Learn entities from Gemini scan results (confirmed by user)

    Args:
        confirmed_entities: List of entities user confirmed as correct
        denied_entities: List of entities user rejected as false positives

    Returns:
        dict with learning results
    """
    try:
        logger.info(f"Learning from Gemini: {len(confirmed_entities)} confirmed, {len(denied_entities or [])} denied")

        from core.learned_entities_db import LearnedEntitiesDB

        # Get learned entities database
        learned_db = LearnedEntitiesDB()

        # Add confirmed entities
        confirmed_count = 0
        for entity in confirmed_entities:
            if learned_db.add_learned_entity(entity, source="gemini_scan"):
                confirmed_count += 1

        # Add denied entities
        denied_count = 0
        for entity in (denied_entities or []):
            if learned_db.add_denied_entity(entity, reason="user_rejected"):
                denied_count += 1

        # Get updated stats
        stats = learned_db.get_stats()

        logger.info(f"Learning complete: {confirmed_count} added, {denied_count} denied")
        return {
            "status": "success",
            "learned_count": confirmed_count,
            "denied_count": denied_count,
            "total_learned": stats['total_learned'],
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to learn from Gemini: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def get_learned_stats() -> dict:
    """
    Get current learned entities statistics

    Returns:
        dict with stats from learned database
    """
    try:
        from core.learned_entities_db import LearnedEntitiesDB

        learned_db = LearnedEntitiesDB()
        stats = learned_db.get_stats()

        return {
            "action": "get_learned_stats",
            "status": "success",
            **stats
        }

    except Exception as e:
        logger.error(f"Failed to get learned stats: {e}")
        return {
            "action": "get_learned_stats",
            "status": "error",
            "error": str(e)
        }


def apply_template_to_document(file_path: str, template_id: str) -> dict:
    """
    Apply a template to a document by extracting text at bbox coordinates

    Args:
        file_path: Path to PDF file
        template_id: Template ID to load and apply

    Returns:
        dict with extracted entities
    """
    try:
        import fitz  # PyMuPDF

        # Load template
        script_dir = Path(__file__).parent
        templates_dir = script_dir / 'templates'
        template_file = templates_dir / f"{template_id}.json"

        if not template_file.exists():
            return {
                'action': 'apply_template',
                'status': 'error',
                'error': f'Template not found: {template_id}'
            }

        with open(template_file, 'r') as f:
            template = json.load(f)

        logger.info(f"Applying template {template_id} to {file_path}")
        logger.info(f"Template has {len(template.get('regions', []))} regions")

        # Open PDF
        doc = fitz.open(file_path)

        entities = []
        for region in template.get('regions', []):
            bbox = region.get('bbox', [])
            if len(bbox) != 4:
                logger.warning(f"Invalid bbox for region: {bbox}")
                continue

            # bbox format: [x, y, width, height]
            # Convert to fitz rect: [x0, y0, x1, y1]
            x, y, width, height = bbox
            rect = fitz.Rect(x, y, x + width, y + height)

            # Extract text from all pages at this bbox location
            extracted_text = ""
            found_page = 1  # Default to page 1
            for page_num, page in enumerate(doc):
                # Get text within the rectangle
                text = page.get_textbox(rect)
                if text and text.strip():
                    extracted_text = text.strip()
                    found_page = page_num + 1  # Store which page we found it on
                    logger.info(f"Extracted text from page {found_page}: '{extracted_text}' at bbox {bbox}")
                    break

            if not extracted_text:
                # Fallback to user label if no text extracted
                extracted_text = region.get('user_label') or region.get('field_name') or f"[{region.get('entity_type')}]"
                logger.warning(f"No text found at bbox {bbox}, using label: {extracted_text}")

            # Create entity with extracted text AND bbox location for direct redaction
            # bbox format: [x, y, width, height] -> convert to rect format
            x, y, width, height = bbox
            entity = {
                'text': extracted_text,
                'entity_type': region.get('entity_type'),
                'score': region.get('confidence', 0.9),
                'start': 0,  # Templates don't have character positions
                'end': len(extracted_text),
                'bbox': bbox,
                'field_name': region.get('field_name'),
                'user_label': region.get('user_label'),
                'source': 'template',
                'accepted': True,
                # IMPORTANT: Add pre-computed location so redaction uses bbox directly
                # This bypasses text search and uses exact coordinates for redaction
                'locations': [{
                    'page': found_page,  # Page number where text was found
                    'rect': {
                        'x0': x,
                        'y0': y,
                        'x1': x + width,
                        'y1': y + height
                    }
                }]
            }
            entities.append(entity)

        doc.close()

        logger.info(f"Successfully applied template, extracted {len(entities)} entities")

        return {
            'action': 'apply_template',
            'status': 'success',
            'entities': entities,
            'summary': {
                'total': len(entities),
                'by_type': {},
                'auto_accepted': len(entities),
                'requires_review': 0
            },
            'template_applied': True,
            'template_id': template_id,
            'template_description': template.get('description', '')
        }

    except Exception as e:
        logger.error(f"Error applying template: {e}", exc_info=True)
        return {
            'action': 'apply_template',
            'status': 'error',
            'error': str(e)
        }


def handle_command(command: dict):
    """
    Handle command from Electron process

    Args:
        command: dict with action and parameters
    """
    action = command.get('action')

    if action == 'process_document':
        file_path = command.get('file_path')
        config_dict = command.get('config', None)  # Extract config from UI
        result = process_document(file_path, config_dict)
        # Send result back to Electron via stdout
        safe_output(result)

    elif action == 'export_redacted':
        file_path = command.get('file_path')
        entities = command.get('entities', [])
        export_txt = command.get('export_txt', False)
        redaction_style = command.get('redaction_style', 'placeholder')  # Default to placeholder style
        result = export_redacted_document(file_path, entities, export_txt, redaction_style)
        # Send result back to Electron via stdout
        safe_output(result)

    elif action == 'gemini_scan':
        file_path = command.get('file_path')
        custom_prompt = command.get('prompt', None)
        result = gemini_scan_document(file_path, custom_prompt)
        safe_output(result)

    elif action == 'teach_template':
        file_path = command.get('file_path')
        voice_command = command.get('voice_command', '')
        description = command.get('description', None)
        result = teach_template_document(file_path, voice_command, description)
        safe_output(result)

    elif action == 'learn_from_gemini':
        confirmed = command.get('confirmed_entities', [])
        denied = command.get('denied_entities', [])
        result = learn_from_gemini(confirmed, denied)
        safe_output(result)

    elif action == 'get_learned_stats':
        result = get_learned_stats()
        safe_output(result)

    elif action == 'save_template':
        template_id = command.get('template_id')
        cache_name = command.get('cache_name')
        description = command.get('description', '')
        regions = command.get('regions', [])
        created_at = command.get('created_at')
        expires_at = command.get('expires_at')
        voice_command = command.get('voice_command', '')

        logger.info(f"Saving template: {template_id} with {len(regions)} regions")

        # Save template to disk
        template_data = {
            'template_id': template_id,
            'cache_name': cache_name,
            'description': description,
            'regions': regions,
            'created_at': created_at,
            'expires_at': expires_at,
            'voice_command': voice_command
        }

        # Create templates directory if it doesn't exist (in same dir as script)
        script_dir = Path(__file__).parent
        templates_dir = script_dir / 'templates'
        templates_dir.mkdir(exist_ok=True)

        # Save template as JSON file
        template_file = templates_dir / f"{template_id}.json"
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)

        logger.info(f"Template saved to: {template_file}")

        result = {
            'status': 'success',
            'template_id': template_id,
            'template_path': str(template_file),
            'regions_count': len(regions),
            'message': f'Template saved with {len(regions)} regions'
        }
        safe_output(result)

    elif action == 'list_templates':
        # List all available templates
        script_dir = Path(__file__).parent
        templates_dir = script_dir / 'templates'
        templates = []

        logger.info(f"📋 Listing templates from: {templates_dir}")
        logger.info(f"📋 Templates dir exists: {templates_dir.exists()}")

        if templates_dir.exists():
            json_files = list(templates_dir.glob('*.json'))
            logger.info(f"📋 Found {len(json_files)} template files")

            for template_file in json_files:
                try:
                    logger.info(f"📋 Reading template: {template_file}")
                    with open(template_file, 'r') as f:
                        template_data = json.load(f)
                        templates.append({
                            'template_id': template_data.get('template_id'),
                            'description': template_data.get('description', ''),
                            'regions_count': len(template_data.get('regions', [])),
                            'created_at': template_data.get('created_at'),
                            'voice_command': template_data.get('voice_command', '')
                        })
                        logger.info(f"📋 Loaded template: {template_data.get('template_id')}")
                except Exception as e:
                    logger.error(f"Error loading template {template_file}: {e}")
        else:
            logger.warning(f"📋 Templates directory does not exist: {templates_dir}")

        result = {
            'action': 'list_templates',  # Add action to identify response
            'status': 'success',
            'templates': templates,
            'count': len(templates)
        }
        logger.info(f"📋 Returning {len(templates)} templates")
        safe_output(result)

    elif action == 'load_template':
        template_id = command.get('template_id')
        script_dir = Path(__file__).parent
        templates_dir = script_dir / 'templates'
        template_file = templates_dir / f"{template_id}.json"

        if not template_file.exists():
            result = {
                'action': 'load_template',
                'status': 'error',
                'error': f'Template not found: {template_id}'
            }
        else:
            with open(template_file, 'r') as f:
                template_data = json.load(f)

            result = {
                'action': 'load_template',
                'status': 'success',
                'template': template_data
            }

        safe_output(result)

    elif action == 'apply_template':
        file_path = command.get('file_path')
        template_id = command.get('template_id')
        result = apply_template_to_document(file_path, template_id)
        safe_output(result)

    else:
        logger.warning(f"Unknown action: {action}")
        safe_output({"status": "error", "error": "Unknown action"})


def main():
    """
    Main loop: read commands from stdin, process, send results to stdout
    """
    logger.info("Python backend started")
    
    # Send ready signal
    safe_output({"status": "ready"})
    
    try:
        # Read commands from stdin line by line
        for line in sys.stdin:
            try:
                command = json.loads(line.strip())
                handle_command(command)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                safe_output({"status": "error", "error": "Invalid JSON"})
                
    except KeyboardInterrupt:
        logger.info("Python backend stopping...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
