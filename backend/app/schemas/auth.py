"""
Pydantic schemas for authentication
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh"""
    refresh_token: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: str
    full_name: str
    role: str
    email_verified: bool
    stripe_customer_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class EmailVerify(BaseModel):
    """Schema for email verification"""
    token: str
