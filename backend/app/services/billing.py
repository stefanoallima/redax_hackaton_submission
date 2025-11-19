"""
Stripe billing service
"""
import stripe
from typing import Optional
from app.core.config import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_checkout_session(
    user_id: str,
    price_id: str,
    customer_id: Optional[str] = None
) -> dict:
    """
    Create Stripe Checkout Session for subscription
    
    Args:
        user_id: User UUID
        price_id: Stripe Price ID (e.g., price_xxx for Professional tier)
        customer_id: Existing Stripe Customer ID (optional)
        
    Returns:
        Checkout session data with URL
    """
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            success_url=f"{settings.FRONTEND_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/pricing",
            metadata={
                "user_id": user_id,
            },
            allow_promotion_codes=True,
        )
        
        return {
            "session_id": session.id,
            "checkout_url": session.url,
        }
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


async def create_customer_portal_session(customer_id: str) -> dict:
    """
    Create Stripe Customer Portal session for subscription management
    
    Args:
        customer_id: Stripe Customer ID
        
    Returns:
        Portal session data with URL
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{settings.FRONTEND_URL}/dashboard",
        )
        
        return {
            "portal_url": session.url,
        }
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


async def get_subscription(subscription_id: str) -> dict:
    """
    Get subscription details from Stripe
    
    Args:
        subscription_id: Stripe Subscription ID
        
    Returns:
        Subscription data
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


async def cancel_subscription(subscription_id: str) -> dict:
    """
    Cancel a subscription
    
    Args:
        subscription_id: Stripe Subscription ID
        
    Returns:
        Updated subscription data
    """
    try:
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )
        return subscription
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


def verify_webhook_signature(payload: bytes, sig_header: str) -> stripe.Event:
    """
    Verify Stripe webhook signature
    
    Args:
        payload: Request body bytes
        sig_header: Stripe-Signature header
        
    Returns:
        Verified Stripe Event
        
    Raises:
        ValueError: If signature verification fails
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError as e:
        raise ValueError("Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise ValueError("Invalid signature")


# Price ID mappings for convenience
PRICE_IDS = {
    "premium": settings.STRIPE_PRICE_ID_PREMIUM,
    "professional": settings.STRIPE_PRICE_ID_PROFESSIONAL,
    "enterprise": settings.STRIPE_PRICE_ID_ENTERPRISE,
}


def get_price_id(tier: str) -> str:
    """
    Get Stripe Price ID for a given tier
    
    Args:
        tier: Tier name (premium, professional, enterprise)
        
    Returns:
        Stripe Price ID
        
    Raises:
        ValueError: If tier is invalid
    """
    price_id = PRICE_IDS.get(tier.lower())
    if not price_id:
        raise ValueError(f"Invalid tier: {tier}")
    return price_id
