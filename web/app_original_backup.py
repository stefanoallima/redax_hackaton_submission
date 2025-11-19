"""
Redactor AI - Gradio Web Application
Conversational PII Detection & Redaction for Legal Documents

Deployment: Hugging Face Spaces (CPU Upgrade tier)
Architecture: Shared backend with Electron desktop app
"""

import sys
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add shared_backend to Python path
backend_path = Path(__file__).parent.parent / 'shared_backend'
if backend_path.exists():
    sys.path.insert(0, str(backend_path))
    logger.info(f"Added shared_backend to path: {backend_path}")
else:
    logger.error(f"shared_backend not found at: {backend_path}")
    sys.exit(1)

import gradio as gr
from typing import Optional, List, Dict, Tuple
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
        # Simple chat for now - in future, can extract policy
        # For MVP, just acknowledge and guide user to upload

        if not chat_history:
            # First message
            response = (
                f"Got it! You want to work with a **{message}**.\n\n"
                "Please describe what you'd like to redact. For example:\n"
                "- 'Redact employee names but keep manager names'\n"
                "- 'Oscura l'inquilino ma mantieni l'avvocato'\n"
                "- 'Remove all personal information'"
            )
        else:
            # Subsequent messages - acknowledge and enable upload
            response = (
                "✅ Perfect! I understand your redaction policy.\n\n"
                "**You can now upload your document** using the file upload below. "
                "I'll analyze it and apply your rules."
            )

        chat_history.append((message, response))
        return "", chat_history

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return "", chat_history + [(message, f"❌ Error: {str(e)}")]


def gemini_analyze(
    file,
    chat_history: List
) -> Tuple[str, str, str]:
    """
    Analyze document with Gemini (multimodal)

    Returns:
        (status_message, results_json, download_button_visibility)
    """
    if file is None:
        return "⚠️ Please upload a document first", "", gr.update(visible=False)

    if not chat_history:
        return "⚠️ Please chat with me first to describe what to redact", "", gr.update(visible=False)

    try:
        # Get Gemini client
        client = get_gemini_client()

        # Extract conversation context from chat history
        conversation = "\n".join([f"User: {u}\nAI: {a}" for u, a in chat_history])

        # Process document
        logger.info(f"Processing file: {file.name}")
        result = document_processor.process_file(file.name)

        if result["status"] != "success":
            return f"❌ Error processing document: {result.get('error', 'Unknown error')}", "", gr.update(visible=False)

        # Run Gemini detection
        logger.info("Running Gemini analysis...")
        gemini_result = client.detect_pii(
            file_path=file.name,
            custom_prompt=f"Context from user conversation:\n{conversation}"
        )

        if gemini_result["status"] != "success":
            return f"❌ Gemini analysis failed: {gemini_result.get('error', 'Unknown error')}", "", gr.update(visible=False)

        # Format results
        entities = gemini_result.get("entities", [])
        summary = gemini_result.get("summary", {})

        results_text = f"""
## 📊 Gemini Analysis Results

**Total Entities Found**: {summary.get('total_entities', len(entities))}

**Breakdown by Type**:
{json.dumps(summary.get('by_type', {}), indent=2)}

**Detected Entities**:
"""

        for i, entity in enumerate(entities[:50], 1):  # Show first 50
            results_text += f"\n{i}. **{entity['text']}** ({entity['entity_type']}) - Page {entity.get('page', 'N/A')}"

        if len(entities) > 50:
            results_text += f"\n\n... and {len(entities) - 50} more entities"

        # Store results for download
        gemini_result['file_path'] = file.name

        return (
            "✅ Analysis complete!",
            results_text,
            gr.update(visible=True)  # Show download button
        )

    except ValueError as e:
        return f"⚠️ {str(e)}", "", gr.update(visible=False)
    except Exception as e:
        logger.error(f"Gemini analysis error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}", "", gr.update(visible=False)


# =============================================================================
# STANDARD EXPERIENCE FUNCTIONS
# =============================================================================

def standard_analyze(
    file,
    depth: str,
    enable_gliner: bool
) -> Tuple[str, str, str]:
    """
    Analyze document with Standard pipeline (Presidio + GLINER)

    Returns:
        (status_message, results_table_html, download_button_visibility)
    """
    if file is None:
        return "⚠️ Please upload a document first", "", gr.update(visible=False)

    try:
        # Get detector
        detector = get_standard_detector()

        # Process document
        logger.info(f"Processing file: {file.name}")
        result = document_processor.process_file(file.name)

        if result["status"] != "success":
            return f"❌ Error processing document: {result.get('error', 'Unknown error')}", "", gr.update(visible=False)

        # Run detection
        logger.info(f"Running Standard detection (depth={depth}, gliner={enable_gliner})...")
        detection_result = detector.detect_pii(
            text=result.get("full_text", ""),
            depth=depth.lower(),
            language="en"  # Using multilingual model
        )

        # Format results as HTML table
        entities = detection_result.get("entities", [])
        stats = detection_result.get("stats", {})

        results_html = f"""
<div style="margin: 20px 0;">
    <h3>📊 Detection Statistics</h3>
    <p><strong>Total Entities:</strong> {stats.get('total', len(entities))}</p>
    <p><strong>Processing Time:</strong> {stats.get('time_ms', 0):.0f}ms</p>
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

        for i, entity in enumerate(entities[:100], 1):  # Show first 100
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

        return (
            f"✅ Found {len(entities)} entities",
            results_html,
            gr.update(visible=True)
        )

    except Exception as e:
        logger.error(f"Standard analysis error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}", "", gr.update(visible=False)


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

            gemini_analyze_btn = gr.Button("✨ Analyze with Gemini", variant="primary", size="lg")

            gemini_status = gr.Markdown("")
            gemini_results = gr.Markdown("")

            gemini_download = gr.Button("📥 Download Redacted PDF", visible=False)

            # Event handlers
            gemini_send_btn.click(
                fn=gemini_chat,
                inputs=[gemini_msg, gemini_chatbot],
                outputs=[gemini_msg, gemini_chatbot]
            )

            gemini_analyze_btn.click(
                fn=gemini_analyze,
                inputs=[gemini_file, gemini_chatbot],
                outputs=[gemini_status, gemini_results, gemini_download]
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
                    std_download = gr.Button("📥 Download Redacted PDF", visible=False)

            # Event handlers
            std_analyze_btn.click(
                fn=standard_analyze,
                inputs=[std_file, std_depth, std_enable_gliner],
                outputs=[std_status, std_results, std_download]
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
    logger.info("Starting Redactor AI web application...")

    # Check Gemini API key
    if os.getenv('GEMINI_API_KEY'):
        logger.info("✅ Gemini API key found")
    else:
        logger.warning("⚠️ GEMINI_API_KEY not set - Gemini Experience will not work")

    # Launch app
    app.queue()  # Enable queuing for better concurrency
    app.launch(
        server_name="0.0.0.0",  # Allow external access (for HF Spaces)
        server_port=7860,        # Default Gradio port
        share=False              # Set to True for temporary public link
    )
