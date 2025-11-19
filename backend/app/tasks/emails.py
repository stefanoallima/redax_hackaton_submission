"""
Celery tasks for sending emails
"""
from app.celery_app import celery_app
from app.services.email import (
    send_email_sync,
    generate_verification_email,
    generate_password_reset_email,
    generate_subscription_receipt_email
)


@celery_app.task(bind=True, max_retries=3)
def send_verification_email(self, to: str, token: str, user_name: str):
    """
    Send email verification email
    
    Args:
        to: Recipient email
        token: Verification token
        user_name: User's full name
    """
    try:
        html_content, text_content = generate_verification_email(token, user_name)
        
        success = send_email_sync(
            to=to,
            subject="Verify Your Email - CodiceCivile.ai",
            html_content=html_content,
            text_content=text_content
        )
        
        if not success:
            raise Exception("Failed to send email")
            
        return {"status": "sent", "to": to}
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_password_reset_email(self, to: str, token: str, user_name: str):
    """
    Send password reset email
    
    Args:
        to: Recipient email
        token: Reset token
        user_name: User's full name
    """
    try:
        html_content, text_content = generate_password_reset_email(token, user_name)
        
        success = send_email_sync(
            to=to,
            subject="Reset Your Password - CodiceCivile.ai",
            html_content=html_content,
            text_content=text_content
        )
        
        if not success:
            raise Exception("Failed to send email")
            
        return {"status": "sent", "to": to}
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_subscription_receipt_email(self, to: str, user_name: str, amount: float, currency: str):
    """
    Send subscription payment receipt
    
    Args:
        to: Recipient email
        user_name: User's full name
        amount: Payment amount
        currency: Currency code (EUR, USD, etc.)
    """
    try:
        html_content, text_content = generate_subscription_receipt_email(
            user_name, amount, currency
        )
        
        success = send_email_sync(
            to=to,
            subject="Payment Receipt - CodiceCivile.ai",
            html_content=html_content,
            text_content=text_content
        )
        
        if not success:
            raise Exception("Failed to send email")
            
        return {"status": "sent", "to": to}
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task
def send_payment_failed_email(to: str, user_name: str):
    """
    Send payment failure notification
    
    Args:
        to: Recipient email
        user_name: User's full name
    """
    html_content = f"""
    <h1>Payment Failed</h1>
    <p>Hi {user_name},</p>
    <p>We were unable to process your subscription payment. Please update your payment method.</p>
    <p><a href="{{settings.FRONTEND_URL}}/dashboard">Update Payment Method</a></p>
    """
    
    text_content = f"Hi {user_name},\n\nYour payment failed. Please update your payment method."
    
    send_email_sync(
        to=to,
        subject="Payment Failed - CodiceCivile.ai",
        html_content=html_content,
        text_content=text_content
    )
    
    return {"status": "sent", "to": to}
