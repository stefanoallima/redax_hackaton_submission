"""
Web API endpoints for DigitalOcean deployment
Provides HTTP endpoints that match the Electron IPC interface
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import tempfile
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add shared_backend to path
SHARED_BACKEND_PATH = os.getenv('SHARED_BACKEND_PATH', '../../../shared_backend')
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared_backend'))

# Import shared backend modules
from core.document_processor import DocumentProcessor
from core.pii_detector_integrated import IntegratedPIIDetector
from core.redaction_exporter import RedactionExporter
from core.learned_entities_db import LearnedEntitiesDB

# Initialize FastAPI app
app = FastAPI(title="Redactor AI API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize backend services
document_processor = DocumentProcessor()
pii_detector = IntegratedPIIDetector(
    enable_gliner=True,
    use_multi_model=False,
    enable_prefilter=True,
    enable_italian_context=True
)
redaction_exporter = RedactionExporter()
learning_db = LearnedEntitiesDB()

# Temporary file storage
UPLOAD_DIR = Path(tempfile.gettempdir()) / "redactor_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

logger.info(f"Upload directory: {UPLOAD_DIR}")
logger.info("Backend services initialized")


# === Pydantic Models ===

class AnalyzeRequest(BaseModel):
    depth: str
    language: str
    enableGliner: bool
    focusAreas: Optional[List[str]] = None
    customKeywords: Optional[List[str]] = None


class ExportPDFRequest(BaseModel):
    inputPath: str
    entities: List[Dict[str, Any]]
    placeholder: str = "[REDACTED]"


class LearnEntitiesRequest(BaseModel):
    entities: List[Dict[str, Any]]


class TeachTemplateRequest(BaseModel):
    voice_command: str
    description: Optional[str] = None


class SaveTemplateRequest(BaseModel):
    template_id: str
    cache_name: str
    description: str
    regions: List[Dict[str, Any]]
    created_at: str
    expires_at: str
    voice_command: str


# === Health Check ===

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Redactor AI API"}


# === File Upload ===

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file and return temporary path
    """
    try:
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        temp_path = UPLOAD_DIR / f"{tempfile.mktemp(dir='')[5:]}{file_ext}"

        # Save uploaded file
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File uploaded: {temp_path}")

        return {
            "filePath": str(temp_path),
            "filename": file.filename,
            "size": temp_path.stat().st_size
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Document Analysis ===

@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    depth: str = Form(...),
    language: str = Form("en"),
    enableGliner: bool = Form(True),
    focusAreas: Optional[str] = Form(None),
    customKeywords: Optional[str] = Form(None)
):
    """
    Analyze document for PII
    """
    try:
        # Save uploaded file
        temp_path = UPLOAD_DIR / f"{tempfile.mktemp(dir='')[5:]}{Path(file.filename).suffix}"
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Analyzing document: {temp_path}, depth: {depth}")

        # Process document
        doc_result = document_processor.process_document(str(temp_path))

        if doc_result.get("status") != "success":
            raise HTTPException(status_code=400, detail=doc_result.get("error", "Processing failed"))

        # Extract text
        full_text = doc_result.get("full_text", "")

        # Parse focus areas and keywords
        focus_areas_list = eval(focusAreas) if focusAreas else None
        custom_keywords_list = eval(customKeywords) if customKeywords else None

        # Detect PII
        detection_result = pii_detector.detect_pii(
            text=full_text,
            depth=depth.lower(),
            language=language,
            focus_areas=focus_areas_list
        )

        entities = detection_result.get("entities", [])

        # Add custom keywords as entities
        if custom_keywords_list:
            for keyword in custom_keywords_list:
                keyword = keyword.strip()
                if keyword and keyword.lower() in full_text.lower():
                    entities.append({
                        "text": keyword,
                        "entity_type": "CUSTOM_KEYWORD",
                        "score": 1.0,
                        "source": "custom",
                        "start": full_text.lower().find(keyword.lower()),
                        "end": full_text.lower().find(keyword.lower()) + len(keyword)
                    })

        logger.info(f"Analysis complete: {len(entities)} entities detected")

        return {
            "status": "success",
            "filePath": str(temp_path),
            "entities": entities,
            "metadata": {
                "total_entities": len(entities),
                "depth": depth,
                "language": language
            }
        }

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# === PDF Export ===

@app.post("/export-pdf")
async def export_redacted_pdf(request: ExportPDFRequest):
    """
    Export redacted PDF
    """
    try:
        input_path = Path(request.inputPath)

        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Input file not found")

        # Create output path
        output_path = UPLOAD_DIR / f"redacted_{input_path.name}"

        logger.info(f"Exporting redacted PDF: {output_path}")

        # Export redacted PDF
        result = redaction_exporter.export_redacted_pdf(
            input_path=str(input_path),
            entities=request.entities,
            output_path=str(output_path)
        )

        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Export failed"))

        logger.info(f"Redacted PDF created: {output_path}")

        # Return file for download
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"redacted_{input_path.name}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# === Learning Database ===

@app.get("/learned-entities")
async def get_learned_entities():
    """
    Get learned entities from database
    """
    try:
        entities = learning_db.get_all_patterns()
        return {
            "status": "success",
            "entities": entities,
            "count": len(entities)
        }

    except Exception as e:
        logger.error(f"Get learned entities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learn-entities")
async def learn_entities(request: LearnEntitiesRequest):
    """
    Learn new entities
    """
    try:
        learned_count = learning_db.learn_entities(request.entities)

        logger.info(f"Learned {learned_count} new entities")

        return {
            "status": "success",
            "learned_count": learned_count
        }

    except Exception as e:
        logger.error(f"Learn entities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Voice-First Teaching Mode (NEW) ===

# Import Gemini client
from gemini_client import GeminiPIIDetector

# Initialize Gemini detector
gemini_detector = None
try:
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if gemini_api_key:
        gemini_detector = GeminiPIIDetector(api_key=gemini_api_key)
        logger.info("Gemini detector initialized for teaching mode")
    else:
        logger.warning("GEMINI_API_KEY not found - teaching mode will not be available")
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {e}")


@app.post("/classify-field")
async def classify_field(request: dict):
    """
    Classify a field based on user's voice description.
    Uses Gemini to understand what type of PII the field contains.

    Example:
      Input: "Nome del locatario"
      Output: {field_name: "tenant_name", entity_type: "PERSON", confidence: 0.95}
    """
    if not gemini_detector:
        raise HTTPException(status_code=503, detail="Gemini not configured")

    try:
        user_label = request.get('user_label', '')
        context = request.get('context', '')

        # Use Gemini to classify the field
        prompt = f"""You are a privacy expert analyzing document templates.

User described a field as: "{user_label}"
Document context: {context}

Classify this field:
1. What is a good machine-readable name? (snake_case)
2. What PII entity type? (PERSON, ORGANIZATION, LOCATION, DATE_TIME, SSN, PHONE_NUMBER, EMAIL_ADDRESS, etc.)
3. How confident are you? (0.0-1.0)

Respond ONLY with JSON:
{{
  "field_name": "snake_case_name",
  "entity_type": "ENTITY_TYPE",
  "confidence": 0.95,
  "reasoning": "brief explanation"
}}"""

        response = gemini_detector.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )

        import json
        result = json.loads(response.text)

        logger.info(f"Classified '{user_label}' as {result['entity_type']}")

        return {
            "status": "success",
            **result
        }

    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        # Fallback classification
        return {
            "status": "success",
            "field_name": user_label.lower().replace(' ', '_'),
            "entity_type": "PERSON",  # Safe default
            "confidence": 0.5,
            "reasoning": f"Fallback classification (error: {str(e)})"
        }


@app.post("/teach-template")
async def teach_template(
    template_file: UploadFile = File(...),
    voice_command: str = Form(...),
    language: str = Form("it-IT"),
    description: Optional[str] = Form(None)
):
    """
    Voice-First Template Teaching Mode
    Teaches Gemini a document template structure using Context Caching

    Args:
        template_file: Blank template (PDF or image, no sensitive data)
        voice_command: User's voice instruction (e.g., "Learn tenant name in section 1")
        language: Voice command language (default: it-IT)
        description: Optional template description

    Returns:
        {
            "status": "success",
            "template": {
                "template_id": "...",
                "cache_name": "...",
                "regions": [...],
                ...
            }
        }
    """
    if not gemini_detector:
        raise HTTPException(
            status_code=503,
            detail="Gemini API not configured. Set GEMINI_API_KEY environment variable."
        )

    try:
        # Save uploaded template
        temp_path = UPLOAD_DIR / f"template_{tempfile.mktemp(dir='')[5:]}{Path(template_file.filename).suffix}"
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(template_file.file, buffer)

        logger.info(f"Teaching template: {template_file.filename}")
        logger.info(f"Voice command: {voice_command}")

        # Call Gemini to teach template with context caching
        result = gemini_detector.teach_template(
            template_path=str(temp_path),
            voice_command=voice_command,
            description=description or template_file.filename
        )

        logger.info(f"Template taught successfully: {result['template']['cache_name']}")

        return result

    except Exception as e:
        logger.error(f"Template teaching error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save-template")
async def save_template(request: SaveTemplateRequest):
    """
    Save taught template locally for future use

    Args:
        request: Template data to save

    Returns:
        {"status": "success", "template_id": "..."}
    """
    try:
        # Create templates directory
        templates_dir = UPLOAD_DIR / "templates"
        templates_dir.mkdir(exist_ok=True)

        # Save template as JSON
        template_path = templates_dir / f"{request.template_id}.json"

        import json
        with template_path.open("w") as f:
            json.dump(request.dict(), f, indent=2)

        logger.info(f"Template saved: {template_path}")

        return {
            "status": "success",
            "template_id": request.template_id,
            "saved_path": str(template_path)
        }

    except Exception as e:
        logger.error(f"Save template error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/templates")
async def list_templates():
    """
    List all saved templates

    Returns:
        {"status": "success", "templates": [...]}
    """
    try:
        templates_dir = UPLOAD_DIR / "templates"
        templates_dir.mkdir(exist_ok=True)

        templates = []
        for template_file in templates_dir.glob("*.json"):
            import json
            with template_file.open("r") as f:
                template_data = json.load(f)
                templates.append(template_data)

        return {
            "status": "success",
            "templates": templates,
            "count": len(templates)
        }

    except Exception as e:
        logger.error(f"List templates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/apply-template")
async def apply_template_batch(
    cache_name: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Apply cached template to batch of documents (fast processing)

    Args:
        cache_name: Cache name from teach-template
        files: List of documents to process

    Returns:
        {"status": "success", "results": [...]}
    """
    if not gemini_detector:
        raise HTTPException(
            status_code=503,
            detail="Gemini API not configured"
        )

    try:
        # Save uploaded files
        document_paths = []
        for file in files:
            temp_path = UPLOAD_DIR / f"batch_{tempfile.mktemp(dir='')[5:]}{Path(file.filename).suffix}"
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            document_paths.append(str(temp_path))

        logger.info(f"Applying template to {len(document_paths)} documents")

        # Apply cached template
        results = gemini_detector.apply_cached_template(
            cache_name=cache_name,
            document_paths=document_paths
        )

        return {
            "status": "success",
            "results": results,
            "total_processed": len(results)
        }

    except Exception as e:
        logger.error(f"Apply template error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# === Learn from Redacted Document (NEW FEATURE) ===

@app.post("/learn-from-redacted")
async def learn_from_redacted(file: UploadFile = File(...)):
    """
    Learn redaction pattern from an already-redacted document.
    Uses Gemini Vision to detect black boxes and infer entity types.

    Args:
        file: Redacted PDF document

    Returns:
        {
            "status": "success",
            "regions": [...],
            "template_id": "..."
        }
    """
    try:
        # Save uploaded file
        temp_path = UPLOAD_DIR / f"redacted_{tempfile.mktemp(dir='')[5:]}{Path(file.filename).suffix}"
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Learning from redacted document: {file.filename}")

        # Import and initialize learner
        from learn_from_redacted import RedactedDocumentLearner
        learner = RedactedDocumentLearner()

        # Analyze redacted document
        result = learner.analyze_redacted_document(str(temp_path))

        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))

        # Save as template
        template_name = Path(file.filename).stem
        save_result = learner.save_template(
            result["regions"],
            template_name,
            output_dir=str(UPLOAD_DIR / "templates")
        )

        logger.info(f"Learned {len(result['regions'])} regions from {file.filename}")

        return {
            "status": "success",
            "regions": result["regions"],
            "template_id": save_result.get("template_id"),
            "template_path": save_result.get("template_path"),
            "total_regions": len(result["regions"])
        }

    except Exception as e:
        logger.error(f"Learn from redacted error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# === Run Server ===

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))

    logger.info(f"Starting Redactor AI API on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
