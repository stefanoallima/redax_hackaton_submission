# Desktop App - OscuraTestiAI Redact

Electron desktop application for offline PII redaction.

## Structure

```
/src
  /electron       # Main process, IPC
  /renderer       # React UI
  /python         # Python backend (document processing)
/assets           # Icons, resources
/dist             # Built app
```

## Setup

1. Install Node dependencies:
   ```bash
   npm install
   ```

2. Set up Python environment:
   ```bash
   cd src/python
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m spacy download it_core_news_lg
   ```

3. Run development:
   ```bash
   npm run electron:dev
   ```

## Build

Windows installer:
```bash
npm run electron:build:win
```

macOS (future):
```bash
npm run electron:build:mac
```

## Phase 1 Tasks
- [x] 0.1 Repository Setup
- [ ] 1.1 Electron Scaffold
- [ ] 1.2 Python Backend Integration
- [ ] 1.5 Presidio PII Detection
