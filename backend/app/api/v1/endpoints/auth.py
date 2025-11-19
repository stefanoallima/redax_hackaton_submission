"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerify
)
from app.db.models.user import User
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token
)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        JWT tokens
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        email_verified=False  # Requires email verification
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # TODO: Send verification email (Task 0.8)
    
    # Generate tokens
    access_token = create_access_token(str(new_user.id))
    refresh_token = create_refresh_token(str(new_user.id))
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    
    Args:
        credentials: Login credentials
        db: Database session
        
    Returns:
        JWT tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    # Verify user and password
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current user from auth dependency
        
    Returns:
        User information
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        email_verified=current_user.email_verified,
        stripe_customer_id=current_user.stripe_customer_id,
        created_at=current_user.created_at
    )


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    data: EmailVerify,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user email with token
    
    Args:
        data: Email verification data
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid
    """
    # TODO: Implement token verification logic
    # For now, this is a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email verification not yet implemented"
    )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset
    
    Args:
        data: Password reset request data
        db: Database session
        
    Returns:
        Success message
    """
    # Get user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if user:
        # TODO: Send password reset email (Task 0.8)
        pass
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password with token
    
    Args:
        data: Password reset confirmation data
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid
    """
    # TODO: Implement token verification and password reset logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not yet implemented"
    )


# OAuth 2.0 endpoints (Google, Microsoft) - TODO: Implement in later iteration
# @router.get("/oauth/google")
# @router.get("/oauth/google/callback")
# @router.get("/oauth/microsoft")
# @router.get("/oauth/microsoft/callback")
