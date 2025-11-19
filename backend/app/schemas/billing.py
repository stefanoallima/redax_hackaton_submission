"""
Pydantic schemas for billing
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CheckoutRequest(BaseModel):
    """Schema for creating checkout session"""
    tier: str  # premium, professional, enterprise


class CheckoutResponse(BaseModel):
    """Schema for checkout session response"""
    session_id: str
    checkout_url: str


class PortalResponse(BaseModel):
    """Schema for customer portal response"""
    portal_url: str


class SubscriptionResponse(BaseModel):
    """Schema for subscription information"""
    id: str
    status: str
    plan_tier: str
    current_period_end: datetime
    cancel_at_period_end: bool
    usage_limit_docs: Optional[int] = None
    usage_limit_searches: Optional[int] = None
    
    class Config:
        from_attributes = True


class WebhookEvent(BaseModel):
    """Schema for webhook event (for logging)"""
    event_type: str
    event_id: str
    processed: bool
    created_at: datetime
