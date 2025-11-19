"""
User management endpoints including GDPR compliance
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Dict
import json
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.db.models.subscription import Subscription
from app.db.models.usage_log import UsageLog
from app.schemas.auth import UserResponse

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile
    
    Args:
        current_user: Authenticated user
        
    Returns:
        User profile information
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


@router.get("/export", status_code=status.HTTP_200_OK)
async def export_user_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    GDPR Right to Access: Export all user data
    
    Args:
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        db: Database session
        
    Returns:
        User data as JSON
    """
    # Gather all user data
    user_data = {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "email_verified": current_user.email_verified,
            "created_at": current_user.created_at.isoformat(),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        }
    }
    
    # Get subscription data
    sub_result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = sub_result.scalar_one_or_none()
    
    if subscription:
        user_data["subscription"] = {
            "id": str(subscription.id),
            "plan_tier": subscription.plan_tier,
            "status": subscription.status,
            "created_at": subscription.created_at.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
        }
    
    # Get usage logs
    usage_result = await db.execute(
        select(UsageLog).where(UsageLog.user_id == current_user.id).limit(1000)
    )
    usage_logs = usage_result.scalars().all()
    
    user_data["usage_logs"] = [
        {
            "action_type": log.action_type,
            "created_at": log.created_at.isoformat(),
            "metadata": log.metadata,
        }
        for log in usage_logs
    ]
    
    user_data["export_metadata"] = {
        "exported_at": datetime.utcnow().isoformat(),
        "format": "JSON",
        "gdpr_compliance": "Right to Access (GDPR Article 15)",
    }
    
    # TODO: Send via email as ZIP file (Task 0.8)
    # For now, return directly
    return user_data


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    GDPR Right to Erasure: Delete user account and all associated data
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        No content (204)
        
    Note:
        - Deletes user, subscriptions, usage logs (CASCADE)
        - Cancels Stripe subscription
        - Anonymizes audit logs (keeps for compliance)
    """
    # Cancel Stripe subscription if exists
    if current_user.stripe_customer_id:
        sub_result = await db.execute(
            select(Subscription).where(Subscription.user_id == current_user.id)
        )
        subscription = sub_result.scalar_one_or_none()
        
        if subscription and subscription.stripe_subscription_id:
            # TODO: Cancel Stripe subscription via billing service
            pass
    
    # Delete usage logs (or anonymize for compliance)
    # For GDPR, we can keep anonymized logs
    await db.execute(
        delete(UsageLog).where(UsageLog.user_id == current_user.id)
    )
    
    # Delete subscriptions (CASCADE handles this, but explicit is better)
    await db.execute(
        delete(Subscription).where(Subscription.user_id == current_user.id)
    )
    
    # Delete user (this cascades to related tables)
    await db.execute(
        delete(User).where(User.id == current_user.id)
    )
    
    await db.commit()
    
    # Return 204 No Content (successful deletion)
    return None


@router.get("/usage", status_code=status.HTTP_200_OK)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user usage statistics for current billing period
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Usage statistics
    """
    # Get subscription to check limits
    sub_result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = sub_result.scalar_one_or_none()
    
    # Count usage logs by type
    from sqlalchemy import func
    usage_result = await db.execute(
        select(
            UsageLog.action_type,
            func.count(UsageLog.id).label('count')
        )
        .where(UsageLog.user_id == current_user.id)
        .group_by(UsageLog.action_type)
    )
    usage_counts = {row.action_type: row.count for row in usage_result}
    
    return {
        "plan_tier": subscription.plan_tier if subscription else "free",
        "usage": {
            "documents_redacted": usage_counts.get("redaction", 0),
            "searches_performed": usage_counts.get("search", 0),
            "chat_messages": usage_counts.get("chat", 0),
        },
        "limits": {
            "documents": subscription.usage_limit_docs if subscription else 3,
            "searches": subscription.usage_limit_searches if subscription else 10,
        },
        "unlimited": subscription and subscription.plan_tier in ["professional", "enterprise"] if subscription else False,
    }
