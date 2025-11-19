"""
FastAPI main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title="redaxai.app API",
    description="Backend API for legal research and document redaction platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "oscuratestiai-api"
    }


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint
    """
    return {
        "message": "redaxai.app API",
        "docs": "/docs",
        "health": "/health"
    }


# Include API routers
from app.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")
