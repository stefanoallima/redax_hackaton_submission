# Backend API - redaxai.app

FastAPI backend for authentication, billing, and legal content serving.

## Structure

```
/app
  /api/v1
    /endpoints     # API route handlers
  /core           # Config, security
  /db
    /models       # SQLAlchemy models
  /services       # Business logic
  /schemas        # Pydantic models
  /tasks          # Celery tasks
  main.py         # FastAPI app entry
/tests            # Pytest tests
/alembic          # Database migrations
requirements.txt
```

## Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure `.env` (see `.env.example`)

4. Run migrations:
   ```bash
   alembic upgrade head
   ```

5. Start server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Testing

```bash
pytest
pytest --cov=app
```

## Phase 0 Tasks
- [x] 0.1 Repository Setup
- [ ] 0.2 Backend API Scaffold
- [ ] 0.4 Database Schema & Migrations
- [ ] 0.5 Authentication
- [ ] 0.6 Stripe Integration
