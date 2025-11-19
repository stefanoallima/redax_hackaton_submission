---
title: Redactor AI
emoji: 🤖
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 4.16.0
app_file: app.py
pinned: false
license: mit
---

# 🤖 Redactor AI

**Intelligent PII Detection & Redaction for Legal Documents**

Conversational AI-powered document redaction using Google Gemini 2.5 Pro, with traditional Presidio + GLINER pipeline for power users.

## Features

### 🤖 Gemini Experience (Conversational)
- **Chat-before-upload**: Describe what to redact in natural language
- **Multimodal analysis**: Detects PII in both text and embedded images
- **AI-powered policy extraction**: Gemini understands your intent automatically
- **95%+ accuracy** on business documents

### ⚙️ Standard Experience (Manual)
- **Presidio + GLINER pipeline**: Industry-standard PII detection
- **Multilingual support**: Optimized for English and Italian
- **Configurable depth levels**: Fast, Balanced, Thorough, Maximum
- **Custom recognizers**: Codice Fiscale, IBAN, Partita IVA, etc.
- **Learning database**: Improves over time with user feedback

## Tech Stack

- **Frontend**: Gradio 4.16
- **AI/ML**: Google Gemini 2.5 Pro, Presidio, GLINER
- **NLP**: spaCy (multilingual models)
- **PDF Processing**: PyMuPDF, pdfplumber
- **Architecture**: Shared backend (85-90% code reuse with desktop app)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_lg

# Set environment variables
export GEMINI_API_KEY=your_key_here

# Run app
python app.py
```

## Deployment on HF Spaces

### Requirements

1. **CPU Upgrade tier** (8 vCPU, 32GB RAM) - Required for GLINER models
2. **Persistent storage** enabled - For learning database
3. **Secrets**: Set `GEMINI_API_KEY` in Space settings

### Directory Structure

```
.
├── app.py                  # Main Gradio application
├── requirements.txt        # Dependencies
└── README.md              # This file

# Shared backend (symlink or copy from parent repo)
../shared_backend/
├── core/                  # Core detection modules
├── detectors/             # Presidio + GLINER
├── config/                # Italian domain knowledge
└── utils/                 # Utilities
```

### Post-Deployment Checklist

- [ ] Verify spaCy model downloads successfully
- [ ] Test Gemini API key connection
- [ ] Test Standard pipeline (may take 30-60s first load)
- [ ] Verify learning database persists to `/data/`
- [ ] Test PDF upload and redaction

## Performance Notes

- **First load**: 30-60 seconds (model initialization)
- **Subsequent scans**: 5-15 seconds
- **Gemini API**: ~10-20 seconds for multimodal analysis

## License

MIT License - See LICENSE file for details

## Links

- **GitHub**: [redactor-ai](https://github.com/yourusername/redactor-ai)
- **Desktop App**: [Electron version](https://github.com/yourusername/redactor-ai/releases)
- **Documentation**: [Architecture docs](https://github.com/yourusername/redactor-ai/tree/main/docs)

---

Built for Google AI Hackathon 2025
