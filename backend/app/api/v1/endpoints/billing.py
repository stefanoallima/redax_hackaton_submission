"""
Billing endpoints for Stripe integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    SubscriptionResponse
)
from app.db.models.user import User
from app.db.models.subscription import Subscription
from app.services.billing import (
    create_checkout_session,
    create_customer_portal_session,
    get_price_id,
    verify_webhook_signature,
)
import stripe

router = APIRouter()


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create Stripe Checkout session for subscription
    
    Args:
        data: Checkout request with tier selection
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Checkout session with URL
        
    Raises:
        HTTPException: If tier is invalid or Stripe error occurs
    """
    try:
        # Get price ID for tier
        price_id = get_price_id(data.tier)
        
        # Create checkout session
        session_data = await create_checkout_session(
            user_id=str(current_user.id),
            price_id=price_id,
            customer_id=current_user.stripe_customer_id
        )
        
        return CheckoutResponse(**session_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/portal", response_model=PortalResponse)
async def customer_portal(
    current_user: User = Depends(get_current_user)
):
    """
    Create Stripe Customer Portal session for subscription management
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Portal session with URL
        
    Raises:
        HTTPException: If user has no Stripe customer ID
    """
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )
    
    try:
        portal_data = await create_customer_portal_session(
            customer_id=current_user.stripe_customer_id
        )
        return PortalResponse(**portal_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's subscription information
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Subscription information
        
    Raises:
        HTTPException: If no subscription found
    """
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    return SubscriptionResponse(
        id=str(subscription.id),
        status=subscription.status,
        plan_tier=subscription.plan_tier,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=False,  # TODO: Get from Stripe
        usage_limit_docs=subscription.usage_limit_docs,
        usage_limit_searches=subscription.usage_limit_searches
    )


@router.post("/webhooks", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events
    
    Args:
        request: FastAPI request with webhook payload
        db: Database session
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If signature verification fails
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = verify_webhook_signature(payload, sig_header)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Handle different event types
    event_type = event["type"]
    data_object = event["data"]["object"]
    
    if event_type == "checkout.session.completed":
        await handle_checkout_completed(data_object, db)
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(data_object, db)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(data_object, db)
    elif event_type == "invoice.payment_succeeded":
        await handle_payment_succeeded(data_object, db)
    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(data_object, db)
    
    return {"status": "success"}


async def handle_checkout_completed(session: dict, db: AsyncSession):
    """Handle successful checkout"""
    user_id = session["metadata"]["user_id"]
    customer_id = session["customer"]
    subscription_id = session["subscription"]
    
    # Update user with Stripe customer ID
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user:
        user.stripe_customer_id = customer_id
        
        # Get subscription details from Stripe
        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        price_id = stripe_sub["items"]["data"][0]["price"]["id"]
        
        # Determine tier from price ID
        from app.core.config import settings
        tier_map = {
            settings.STRIPE_PRICE_ID_PREMIUM: "premium",
            settings.STRIPE_PRICE_ID_PROFESSIONAL: "professional",
            settings.STRIPE_PRICE_ID_ENTERPRISE: "enterprise",
        }
        tier = tier_map.get(price_id, "free")
        
        # Create or update subscription
        sub_result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = sub_result.scalar_one_or_none()
        
        if subscription:
            subscription.stripe_subscription_id = subscription_id
            subscription.plan_tier = tier
            subscription.status = stripe_sub["status"]
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_sub["current_period_end"]
            )
        else:
            subscription = Subscription(
                user_id=user_id,
                stripe_subscription_id=subscription_id,
                plan_tier=tier,
                status=stripe_sub["status"],
                current_period_end=datetime.fromtimestamp(
                    stripe_sub["current_period_end"]
                ),
                usage_limit_docs=None if tier in ["professional", "enterprise"] else 3,
                usage_limit_searches=None if tier in ["professional", "enterprise"] else 10,
            )
            db.add(subscription)
        
        await db.commit()


async def handle_subscription_updated(subscription: dict, db: AsyncSession):
    """Handle subscription update"""
    subscription_id = subscription["id"]
    
    result = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == subscription_id
        )
    )
    db_subscription = result.scalar_one_or_none()
    
    if db_subscription:
        db_subscription.status = subscription["status"]
        db_subscription.current_period_end = datetime.fromtimestamp(
            subscription["current_period_end"]
        )
        await db.commit()


async def handle_subscription_deleted(subscription: dict, db: AsyncSession):
    """Handle subscription cancellation"""
    subscription_id = subscription["id"]
    
    result = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == subscription_id
        )
    )
    db_subscription = result.scalar_one_or_none()
    
    if db_subscription:
        db_subscription.status = "canceled"
        db_subscription.plan_tier = "free"
        await db.commit()


async def handle_payment_succeeded(invoice: dict, db: AsyncSession):
    """Handle successful payment"""
    # TODO: Send receipt email via Celery (Task 0.8)
    pass


async def handle_payment_failed(invoice: dict, db: AsyncSession):
    """Handle failed payment"""
    # TODO: Send payment failure email via Celery (Task 0.8)
    pass
