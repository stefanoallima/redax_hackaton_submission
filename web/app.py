"""
Redactor AI - Gradio Web Application (Enhanced)
Conversational PII Detection & Redaction for Legal Documents

Deployment: Hugging Face Spaces (CPU Upgrade tier)
Architecture: Shared backend with Electron desktop app

ENHANCEMENTS:
- PDF redaction export (P0)
- Learning confirmation (P1)
- Focus areas + custom keywords (P1)
- Better loading states (P2)
- Improved error handling (P2)
"""

import sys
import os
from pathlib import Path
import logging
import tempfile
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add shared_backend to Python path
# Try HF Spaces structure first (same directory), then local dev structure (parent directory)
backend_path_spaces = Path(__file__).parent / 'shared_backend'
backend_path_local = Path(__file__).parent.parent / 'shared_backend'

if backend_path_spaces.exists():
    sys.path.insert(0, str(backend_path_spaces))
    logger.info(f"Added shared_backend to path (HF Spaces): {backend_path_spaces}")
elif backend_path_local.exists():
    sys.path.insert(0, str(backend_path_local))
    logger.info(f"Added shared_backend to path (Local Dev): {backend_path_local}")
else:
    logger.error(f"shared_backend not found at: {backend_path_spaces} or {backend_path_local}")
    sys.exit(1)

import gradio as gr
from typing import Optional, List, Dict, Tuple, Any
import json

# Import shared backend modules
from core.gemini_client import GeminiPIIDetector
from core.pii_detector_integrated import IntegratedPIIDetector
from core.learned_entities_db import LearnedEntitiesDB
from core.document_processor import DocumentProcessor
from core.redaction_exporter import RedactionExporter

# Initialize shared backend (singleton instances)
logger.info("Initializing shared backend...")
learning_db = LearnedEntitiesDB()  # Auto-detects environment (/data or ~/.oscuratesti)
document_processor = DocumentProcessor()
redaction_exporter = RedactionExporter()

# Gemini client (lazy load - only if API key available)
gemini_client = None

def get_gemini_client():
    """Lazy load Gemini client"""
    global gemini_client
    if gemini_client is None:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured in environment")
        gemini_client = GeminiPIIDetector()
    return gemini_client

# Standard detector (lazy load - heavy model loading)
standard_detector = None

def get_standard_detector():
    """Lazy load standard detector"""
    global standard_detector
    if standard_detector is None:
        logger.info("Loading Standard detector (Presidio + GLINER)...")
        standard_detector = IntegratedPIIDetector(
            enable_gliner=True,
            use_multi_model=False,  # Single model for performance
            enable_prefilter=True,
            enable_italian_context=True,
            enable_entity_thresholds=False
        )
        logger.info("Standard detector loaded successfully")
    return standard_detector

logger.info("Backend initialization complete")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_temp_file(suffix=".pdf") -> str:
    """Create temporary file for redacted output"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    return temp_file.name

def format_error_message(error: Exception) -> str:
    """Convert technical errors to user-friendly messages"""
    error_msg = str(error).lower()

    if "api key" in error_msg or "authentication" in error_msg:
        return "⚠️ API key issue. Please check your Gemini API key configuration."
    elif "timeout" in error_msg:
        return "⏱️ Request timed out. Please try again with a smaller document."
    elif "file" in error_msg and ("size" in error_msg or "large" in error_msg):
        return "📄 Document too large. Please use a file under 100MB."
    elif "model" in error_msg or "load" in error_msg:
        return "🔄 AI models are loading. Please wait a moment and try again."
    else:
        return f"❌ Error: {str(error)}"

# =============================================================================
# GEMINI EXPERIENCE FUNCTIONS
# =============================================================================

def gemini_chat(message: str, chat_history: List) -> Tuple[str, List]:
    """
    Handle Gemini chat interaction for policy extraction

    Args:
        message: User message
        chat_history: Previous messages

    Returns:
        (response, updated_history)
    """
    try:
        if not chat_history:
            # First message
            response = (
                f"Got it! You want to work with a **{message}**.\\n\\n"
                "Please describe what you'd like to redact. For example:\\n"
                "- 'Redact employee names but keep manager names'\\n"
                "- 'Oscura l'inquilino ma mantieni l'avvocato'\\n"
                "- 'Remove all personal information'"
            )
        else:
            # Subsequent messages - acknowledge and enable upload
            response = (
                "✅ Perfect! I understand your redaction policy.\\n\\n"
                "**You can now upload your document** using the file upload below. "
                "I'll analyze it and apply your rules."
            )

        chat_history.append((message, response))
        return "", chat_history

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return "", chat_history + [(message, format_error_message(e))]


def gemini_analyze(
    file,
    chat_history: List,
    save_patterns: bool,
    progress=gr.Progress()
) -> Tuple[str, str, Dict, gr.Button]:
    """
    Analyze document with Gemini (multimodal)

    Returns:
        (status_message, results_markdown, results_state, download_button)
    """
    if file is None:
        return "⚠️ Please upload a document first", "", {}, gr.update(visible=False)

    if not chat_history:
        return "⚠️ Please chat with me first to describe what to redact", "", {}, gr.update(visible=False)

    try:
        progress(0, desc="Initializing Gemini client...")

        # Get Gemini client
        client = get_gemini_client()

        # Extract conversation context from chat history
        conversation = "\\n".join([f"User: {u}\\nAI: {a}" for u, a in chat_history])

        # Process document
        progress(0.2, desc="Processing document...")
        logger.info(f"Processing file: {file.name}")
        result = document_processor.process_file(file.name)

        if result["status"] != "success":
            return format_error_message(Exception(result.get('error', 'Unknown error'))), "", {}, gr.update(visible=False)

        # Run Gemini detection
        progress(0.5, desc="Analyzing with Gemini (multimodal)...")
        logger.info("Running Gemini analysis...")
        gemini_result = client.detect_pii(
            file_path=file.name,
            custom_prompt=f"Context from user conversation:\\n{conversation}"
        )

        if gemini_result["status"] != "success":
            return format_error_message(Exception(gemini_result.get('error', 'Unknown error'))), "", {}, gr.update(visible=False)

        # Save patterns to learning DB if requested
        if save_patterns:
            progress(0.8, desc="Saving discovered patterns...")
            entities = gemini_result.get("entities", [])
            if entities:
                learned_count = learning_db.learn_entities(entities)
                logger.info(f"Saved {learned_count} new patterns to learning database")

        # Format results
        progress(0.9, desc="Formatting results...")
        entities = gemini_result.get("entities", [])
        summary = gemini_result.get("summary", {})

        # Separate text and image PII
        text_entities = [e for e in entities if e.get('source', '').lower() != 'image']
        image_entities = [e for e in entities if e.get('source', '').lower() == 'image']

        results_text = f"""
## 📊 Gemini Analysis Results

**Total Entities Found**: {len(entities)}
- **Text PII**: {len(text_entities)}
- **Image PII**: {len(image_entities)}

### Breakdown by Type
{json.dumps(summary.get('by_type', {}), indent=2)}

### Text PII Detected
"""

        for i, entity in enumerate(text_entities[:30], 1):
            results_text += f"\\n{i}. **{entity['text']}** ({entity['entity_type']}) - Page {entity.get('page', 'N/A')}"

        if len(text_entities) > 30:
            results_text += f"\\n\\n... and {len(text_entities) - 30} more text entities"

        if image_entities:
            results_text += "\\n\\n### Image PII Detected\\n"
            for i, entity in enumerate(image_entities[:20], 1):
                results_text += f"\\n{i}. **{entity['text']}** ({entity['entity_type']}) - Page {entity.get('page', 'N/A')}"

            if len(image_entities) > 20:
                results_text += f"\\n\\n... and {len(image_entities) - 20} more image entities"

        # Store results in state for download
        state = {
            'file_path': file.name,
            'entities': entities,
            'detection_type': 'gemini'
        }

        progress(1.0, desc="Complete!")

        return (
            f"✅ Analysis complete! Found {len(entities)} entities.",
            results_text,
            state,
            gr.update(visible=True)  # Show download button
        )

    except ValueError as e:
        return format_error_message(e), "", {}, gr.update(visible=False)
    except Exception as e:
        logger.error(f"Gemini analysis error: {e}", exc_info=True)
        return format_error_message(e), "", {}, gr.update(visible=False)


def download_gemini_pdf(state: Dict) -> Optional[str]:
    """Generate and return redacted PDF from Gemini results"""
    if not state or 'file_path' not in state:
        logger.error("No results to download")
        return None

    try:
        logger.info("Generating redacted PDF...")

        # Create temporary output file
        output_path = create_temp_file(suffix=".pdf")

        # Export redacted PDF
        result = redaction_exporter.export_redacted_pdf(
            input_path=state['file_path'],
            entities=state['entities'],
            output_path=output_path
        )

        if result.get("status") == "success":
            logger.info(f"Redacted PDF created: {output_path}")
            return output_path
        else:
            logger.error(f"Redaction failed: {result.get('error')}")
            return None

    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        return None


# =============================================================================
# STANDARD EXPERIENCE FUNCTIONS
# =============================================================================

def standard_analyze(
    file,
    depth: str,
    enable_gliner: bool,
    focus_areas: List[str],
    custom_keywords: str,
    progress=gr.Progress()
) -> Tuple[str, str, Dict, gr.Button]:
    """
    Analyze document with Standard pipeline (Presidio + GLINER)

    Returns:
        (status_message, results_html, results_state, download_button)
    """
    if file is None:
        return "⚠️ Please upload a document first", "", {}, gr.update(visible=False)

    try:
        progress(0, desc="Initializing detector...")

        # Get detector
        detector = get_standard_detector()

        # Process document
        progress(0.2, desc="Processing document...")
        logger.info(f"Processing file: {file.name}")
        result = document_processor.process_file(file.name)

        if result["status"] != "success":
            return format_error_message(Exception(result.get('error', 'Unknown error'))), "", {}, gr.update(visible=False)

        # Prepare custom entities from keywords
        custom_entities = []
        if custom_keywords and custom_keywords.strip():
            keywords = [k.strip() for k in custom_keywords.split(',') if k.strip()]
            custom_entities = [{'text': kw, 'entity_type': 'CUSTOM'} for kw in keywords]
            logger.info(f"Added {len(custom_entities)} custom keywords")

        # Run detection
        progress(0.5, desc=f"Running {depth} detection with Presidio + GLINER...")
        logger.info(f"Running Standard detection (depth={depth}, gliner={enable_gliner}, focus={focus_areas})...")
        detection_result = detector.detect_pii(
            text=result.get("full_text", ""),
            depth=depth.lower(),
            language="en",  # Using multilingual model
            focus_areas=focus_areas if focus_areas else None
        )

        # Add custom entities to results
        entities = detection_result.get("entities", [])
        if custom_entities:
            # Simple matching for custom keywords in text
            text = result.get("full_text", "")
            for custom_entity in custom_entities:
                keyword = custom_entity['text']
                if keyword.lower() in text.lower():
                    # Add to entities list with high confidence
                    entities.append({
                        'text': keyword,
                        'entity_type': 'CUSTOM_KEYWORD',
                        'score': 1.0,
                        'source': 'custom'
                    })

        # Format results as HTML table
        progress(0.9, desc="Formatting results...")
        stats = detection_result.get("stats", {})

        results_html = f"""
<div style="margin: 20px 0;">
    <h3>📊 Detection Statistics</h3>
    <p><strong>Total Entities:</strong> {len(entities)}</p>
    <p><strong>Processing Time:</strong> {stats.get('time_ms', 0):.0f}ms</p>
    <p><strong>Focus Areas:</strong> {', '.join(focus_areas) if focus_areas else 'All'}</p>
</div>

<table style="width: 100%; border-collapse: collapse;">
    <thead>
        <tr style="background: #f0f0f0;">
            <th style="padding: 8px; border: 1px solid #ddd;">#</th>
            <th style="padding: 8px; border: 1px solid #ddd;">Entity</th>
            <th style="padding: 8px; border: 1px solid #ddd;">Type</th>
            <th style="padding: 8px; border: 1px solid #ddd;">Confidence</th>
            <th style="padding: 8px; border: 1px solid #ddd;">Source</th>
        </tr>
    </thead>
    <tbody>
"""

        for i, entity in enumerate(entities[:100], 1):
            confidence_pct = f"{entity.get('score', 0) * 100:.0f}%"
            confidence_color = "green" if entity.get('score', 0) > 0.8 else "orange" if entity.get('score', 0) > 0.6 else "red"

            results_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{i}</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>{entity.get('text', '')}</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{entity.get('entity_type', 'UNKNOWN')}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: {confidence_color};">{confidence_pct}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{entity.get('source', 'unknown')}</td>
        </tr>
"""

        results_html += """
    </tbody>
</table>
"""

        if len(entities) > 100:
            results_html += f"<p><em>... and {len(entities) - 100} more entities</em></p>"

        # Store results in state for download
        state = {
            'file_path': file.name,
            'entities': entities,
            'detection_type': 'standard'
        }

        progress(1.0, desc="Complete!")

        return (
            f"✅ Found {len(entities)} entities",
            results_html,
            state,
            gr.update(visible=True)
        )

    except Exception as e:
        logger.error(f"Standard analysis error: {e}", exc_info=True)
        return format_error_message(e), "", {}, gr.update(visible=False)


def download_standard_pdf(state: Dict) -> Optional[str]:
    """Generate and return redacted PDF from Standard results"""
    if not state or 'file_path' not in state:
        logger.error("No results to download")
        return None

    try:
        logger.info("Generating redacted PDF...")

        # Create temporary output file
        output_path = create_temp_file(suffix=".pdf")

        # Export redacted PDF
        result = redaction_exporter.export_redacted_pdf(
            input_path=state['file_path'],
            entities=state['entities'],
            output_path=output_path
        )

        if result.get("status") == "success":
            logger.info(f"Redacted PDF created: {output_path}")
            return output_path
        else:
            logger.error(f"Redaction failed: {result.get('error')}")
            return None

    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        return None


# =============================================================================
# GRADIO UI
# =============================================================================

# Custom CSS
custom_css = """
.gradio-container {
    max-width: 1200px !important;
}
.tab-nav button {
    font-size: 16px !important;
    padding: 12px 24px !important;
}
"""

# Build Gradio interface
with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="purple"),
    css=custom_css,
    title="Redactor AI - Intelligent PII Redaction"
) as app:

    gr.Markdown("""
    # 🤖 Redactor AI
    ### Intelligent PII Detection & Redaction for Legal Documents

    **Choose your experience below:**
    """)

    with gr.Tabs() as tabs:

        # =====================================================================
        # GEMINI EXPERIENCE TAB
        # =====================================================================
        with gr.Tab("🤖 Gemini Experience (Conversational)", id=0):
            gr.Markdown("""
            ### Chat-First Configuration
            Describe what you want to redact in natural language, then upload your document.
            Gemini will understand your intent and apply the rules automatically.
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    # Chat interface
                    gemini_chatbot = gr.Chatbot(
                        label="Chat with AI",
                        height=400,
                        value=[("", "👋 Hello! What type of document do you have? What should I redact?")]
                    )

                    gemini_msg = gr.Textbox(
                        label="Your message",
                        placeholder="e.g., 'Employment contract. Redact employee names but keep manager.'",
                        lines=2
                    )

                    gemini_send_btn = gr.Button("💬 Send", variant="primary")

            gr.Markdown("---")

            with gr.Row():
                gemini_file = gr.File(
                    label="📄 Upload Document (PDF, DOCX, TXT)",
                    file_types=[".pdf", ".docx", ".txt"]
                )

            with gr.Row():
                gemini_save_patterns = gr.Checkbox(
                    label="💾 Save discovered patterns to learning database",
                    value=True,
                    info="Help improve future detections"
                )

            gemini_analyze_btn = gr.Button("✨ Analyze with Gemini", variant="primary", size="lg")

            gemini_status = gr.Markdown("")
            gemini_results = gr.Markdown("")

            # Hidden state to store results
            gemini_state = gr.State({})

            gemini_download_file = gr.File(label="📥 Download Redacted PDF", visible=False)
            gemini_download_btn = gr.Button("📥 Generate Redacted PDF", visible=False)

            # Event handlers
            gemini_send_btn.click(
                fn=gemini_chat,
                inputs=[gemini_msg, gemini_chatbot],
                outputs=[gemini_msg, gemini_chatbot]
            )

            gemini_analyze_btn.click(
                fn=gemini_analyze,
                inputs=[gemini_file, gemini_chatbot, gemini_save_patterns],
                outputs=[gemini_status, gemini_results, gemini_state, gemini_download_btn]
            )

            gemini_download_btn.click(
                fn=download_gemini_pdf,
                inputs=[gemini_state],
                outputs=[gemini_download_file]
            ).then(
                fn=lambda: gr.update(visible=True),
                outputs=[gemini_download_file]
            )

        # =====================================================================
        # STANDARD EXPERIENCE TAB
        # =====================================================================
        with gr.Tab("⚙️ Standard Experience (Manual)", id=1):
            gr.Markdown("""
            ### Manual Configuration
            Configure detection parameters manually for full control.
            Uses Presidio + GLINER for high-accuracy PII detection.
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### ⚙️ Configuration")

                    std_depth = gr.Radio(
                        choices=["Fast", "Balanced", "Thorough", "Maximum"],
                        value="Balanced",
                        label="Detection Depth",
                        info="Higher depth = more accuracy but slower"
                    )

                    std_enable_gliner = gr.Checkbox(
                        label="Enable GLINER (AI-powered detection)",
                        value=True,
                        info="Recommended for best accuracy"
                    )

                    std_focus_areas = gr.CheckboxGroup(
                        choices=["Names", "Locations", "Organizations", "Dates", "Financial", "Contact Info", "Medical", "Legal IDs"],
                        label="Focus Areas (optional)",
                        info="Leave empty to detect all types"
                    )

                    std_custom_keywords = gr.Textbox(
                        label="Custom Keywords (optional)",
                        placeholder="e.g., Project Apollo, Widget X, Secret Term",
                        info="Comma-separated terms to always redact",
                        lines=2
                    )

                    gr.Markdown("### 📄 Upload Document")

                    std_file = gr.File(
                        label="Upload Document (PDF, DOCX, TXT)",
                        file_types=[".pdf", ".docx", ".txt"]
                    )

                    std_analyze_btn = gr.Button("🔍 Start Scan", variant="primary", size="lg")

                with gr.Column(scale=2):
                    gr.Markdown("### 📊 Results")

                    std_status = gr.Markdown("")
                    std_results = gr.HTML("")

                    # Hidden state to store results
                    std_state = gr.State({})

                    std_download_file = gr.File(label="📥 Download Redacted PDF", visible=False)
                    std_download_btn = gr.Button("📥 Generate Redacted PDF", visible=False)

            # Event handlers
            std_analyze_btn.click(
                fn=standard_analyze,
                inputs=[std_file, std_depth, std_enable_gliner, std_focus_areas, std_custom_keywords],
                outputs=[std_status, std_results, std_state, std_download_btn]
            )

            std_download_btn.click(
                fn=download_standard_pdf,
                inputs=[std_state],
                outputs=[std_download_file]
            ).then(
                fn=lambda: gr.update(visible=True),
                outputs=[std_download_file]
            )

    # Footer
    gr.Markdown("""
    ---
    <div style='text-align: center; color: gray; padding: 20px;'>
        Built with Google Gemini 2.5 Pro |
        <a href='https://github.com/yourusername/redactor-ai'>GitHub</a> |
        Powered by Presidio + GLINER + Gemini
    </div>
    """)

# =============================================================================
# LAUNCH
# =============================================================================

if __name__ == "__main__":
    # Detect if running in Electron desktop app
    IS_ELECTRON = os.getenv('ELECTRON') == '1'

    logger.info("Starting Redactor AI web application...")
    logger.info(f"Mode: {'Electron Desktop' if IS_ELECTRON else 'Web/HF Spaces'}")

    # Check Gemini API key
    if os.getenv('GEMINI_API_KEY'):
        logger.info("✅ Gemini API key found")
    else:
        logger.warning("⚠️ GEMINI_API_KEY not set - Gemini Experience will not work")

    # Launch app
    app.queue()  # Enable queuing for better concurrency
    app.launch(
        server_name="127.0.0.1" if IS_ELECTRON else "0.0.0.0",  # Localhost for desktop, 0.0.0.0 for web
        server_port=7860,        # Default Gradio port
        share=False,             # Never share publicly
        inbrowser=not IS_ELECTRON,  # Don't auto-open browser in desktop mode
        # Desktop mode: allow access to user's home directory for file uploads
        allowed_paths=[os.path.expanduser("~")] if IS_ELECTRON else None
    )
