Here is the **New Product Requirements Document (PRD) Scope** for your pivotal submission.

This document is designed to be copy-pasted into your project management tool or shared with teammates. It focuses entirely on the **"Voice-First Sovereign Agent"** architecture.

-----

# 📄 Product Scope: "Priva.ci Agent"

**Tagline:** The Voice-First Data Sovereign. Talk to Gemini; Execute Locally.
**Track:** Google Gemini (Best Use of Gemini)

## 1\. Executive Summary

**Priva.ci** is a multimodal AI agent that orchestrates secure, local-first document redaction. Instead of uploading sensitive files to the cloud, the user "teaches" the Agent via voice and templates. The Agent (Gemini 1.5 Pro) generates a secure "Redaction Map" (JSON), which is then executed by a local desktop engine. It leverages a **Hybrid Architecture**: Intelligence in the Cloud, Execution on the Edge.

## 2\. The "Sovereign" Architecture

  * **The Brain (Cloud):** **Gemini 1.5 Pro** (via API). Handles Voice I/O, Reasoning, Template Analysis, and Anomaly Resolution.
  * **The Muscle (Local):** **Python/Streamlit Local**. Handles File I/O, PDF rendering, Coordinate Mapping, and "Pixel-Level" Redaction.
  * **The Bridge:** **JSON Function Calls**. The Brain never touches the sensitive data; it only sends instructions (coordinates, rules) to the Muscle.

-----

## 3\. Core Features (The MVP Flow)

### Feature A: The "Teaching" Mode (Adaptive Context Caching)

  * **User Story:** "I want to teach the AI my standard lease agreement so it knows *where* to look without reading my client's names."
  * **Input:** User uploads a **Blank Template** (PDF/Image) + Voice Command (*"Learn this structure. The Tenant Name is in Section 1."*).
  * **Gemini Action:**
      * Uses **Gemini 1.5 Pro (Vision)** to scan the document layout.
      * Identifies bounding box coordinates `[ymin, xmin, ymax, xmax]` for requested fields.
      * Returns a **Structured JSON Map**.
  * **Output:** A saved "Redaction Template" (JSON) stored locally.

### Feature B: The "Sovereign" Execution (Batch Processing)

  * **User Story:** "I want to redact 50 filled applications using the template I just taught you."
  * **Input:** User selects a folder of PDF files.
  * **Local Action (Python):**
      * Script loops through files.
      * Applies the **JSON Map** coordinates (draws black boxes).
      * **Crucial:** No data leaves the device.
  * **Output:** 50 Redacted PDFs in seconds.

### Feature C: The "Escalation" Protocol (Hybrid Loop)

  * **User Story:** "If the AI sees something weird (like a photo or handwriting), I want it to ask me before sending it to the cloud."
  * **Trigger:** Local script detects an object (image/annotation) inside a "Safe Zone" or outside the Template structure.
  * **Voice Interaction:**
      * **Agent:** *"I applied the template, but File \#4 contains an unmapped photo. Permission to analyze securely?"*
      * **User:** *"Granted."*
  * **Gemini Action:** The specific image crop is sent to Gemini for **Multimodal Redaction**.

-----

## 4\. Technical Implementation Steps

### Step 1: The Web/UI Layer (Streamlit)

  * **Framework:** Streamlit (running locally for hackathon simplicity).
  * **Audio Input:** Use `st.audio_input` (Streamlit 1.39+) or `audio-recorder-streamlit`.
  * **Display:** Split screen. Left: Chat/Voice Log. Right: PDF Previewer.

### Step 2: The Gemini "Brain" Logic

  * **Model:** `gemini-1.5-pro-002` (Best for complex instruction following).
  * **System Instruction:**
    > "You are an expert Privacy Officer. You analyze document layouts to create 'Redaction Maps'. You never ask for PII. You output strictly in JSON format containing coordinates (0-1000 scale)."
  * **Schema:** Use `response_mime_type: "application/json"` to force the Coordinate Map output.

### Step 3: The Local "Muscle" Logic

  * **Library:** `PyMuPDF` (aka `fitz`) for fast, coordinate-based redaction.
  * **Coordinate Conversion:**
    ```python
    # Logic to convert Gemini's 0-1000 scale to PDF Points
    rect = fitz.Rect(
        (x_min/1000)*page.rect.width, 
        (y_min/1000)*page.rect.height, 
        ...
    )
    page.draw_rect(rect, color=(0,0,0), fill=(0,0,0))
    ```

-----

## 5\. Hackathon Deliverables Checklist

| Component | Status | Notes |
| :--- | :--- | :--- |
| **Repo** | ⬜ Pending | Create public GitHub repo `privaci-agent`. |
| **Frontend** | ⬜ Pending | Streamlit app with Microphone button. |
| **Backend** | ⬜ Pending | `gemini_helper.py` with the "Teaching" prompt. |
| **Redactor** | ⬜ Pending | `pdf_engine.py` with PyMuPDF logic. |
| **Demo Video** | ⬜ Pending | **Must record:** Voice conversation + Template upload. |
| **Demo URL** | ⬜ Pending | Deploy a "Lite" version to Streamlit Cloud (even if it just mocks the local part). |

## 6\. Judging Criteria Alignment (The "Why")

  * **Best Use of Gemini:**
      * ✅ **Multimodal:** Voice input + Document Vision.
      * ✅ **Context Caching:** "Teaching" the template implies caching the structure.
      * ✅ **Safety:** The architecture itself is a safety feature (Hybrid Cloud).
  * **Business Value:** Solves the cost/privacy trade-off for professional services.
  * **Originality:** "Voice-First Privacy" is a completely new UX for this boring market.

**Shall I generate the Python code for the "Gemini Helper" (Step 2) so you can start building the Brain immediately?**s