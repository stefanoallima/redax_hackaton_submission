"""
API v1 router aggregation
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth

api_router = APIRouter()

# Include auth router
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include billing router
from app.api.v1.endpoints import billing
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])

# Include user router (GDPR compliance)
from app.api.v1.endpoints import user
api_router.include_router(user.router, prefix="/user", tags=["user"])

# TODO: Add more routers as they're implemented
# api_router.include_router(desktop.router, prefix="/desktop", tags=["desktop"])
# api_router.include_router(search.router, prefix="/search", tags=["search"])
