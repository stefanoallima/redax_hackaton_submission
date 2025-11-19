"""
Email service for sending transactional emails
Supports both SendGrid and Resend
"""
from typing import Optional
from app.core.config import settings

# Choose email provider based on config
USE_SENDGRID = bool(settings.SENDGRID_API_KEY)


def send_email_sync(
    to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send email using configured provider (SendGrid or Resend)
    
    Args:
        to: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        if USE_SENDGRID:
            return _send_with_sendgrid(to, subject, html_content, text_content)
        else:
            return _send_with_resend(to, subject, html_content, text_content)
    except Exception as e:
        print(f"Email send error: {str(e)}")
        return False


def _send_with_sendgrid(
    to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """Send email via SendGrid"""
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=to,
        subject=subject,
        html_content=html_content,
        plain_text_content=text_content or ""
    )
    
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = sg.send(message)
    
    return response.status_code in [200, 202]


def _send_with_resend(
    to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """Send email via Resend"""
    import resend
    
    resend.api_key = settings.RESEND_API_KEY
    
    params = {
        "from": settings.FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html_content,
    }
    
    if text_content:
        params["text"] = text_content
    
    email = resend.Emails.send(params)
    return bool(email)


# Email templates
def generate_verification_email(token: str, user_name: str) -> tuple[str, str]:
    """
    Generate email verification email
    
    Args:
        token: Verification token
        user_name: User's full name
        
    Returns:
        Tuple of (html_content, text_content)
    """
    verify_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #2563eb;">Verify Your Email</h1>
            <p>Hi {user_name},</p>
            <p>Thank you for registering with CodiceCivile.ai. Please verify your email address by clicking the button below:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_link}" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Verify Email
                </a>
            </div>
            <p>Or copy this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{verify_link}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                CodiceCivile.ai - Privacy-first legal AI platform<br>
                © {datetime.now().year} All rights reserved
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Verify Your Email
    
    Hi {user_name},
    
    Thank you for registering with CodiceCivile.ai. Please verify your email address by visiting:
    
    {verify_link}
    
    This link will expire in 24 hours.
    
    If you didn't create an account, please ignore this email.
    
    ---
    CodiceCivile.ai - Privacy-first legal AI platform
    © {datetime.now().year} All rights reserved
    """
    
    return html_content, text_content


def generate_password_reset_email(token: str, user_name: str) -> tuple[str, str]:
    """Generate password reset email"""
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #2563eb;">Reset Your Password</h1>
            <p>Hi {user_name},</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p>Or copy this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{reset_link}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                CodiceCivile.ai - Privacy-first legal AI platform<br>
                © {datetime.now().year} All rights reserved
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Reset Your Password
    
    Hi {user_name},
    
    We received a request to reset your password. Visit this link to create a new password:
    
    {reset_link}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, please ignore this email.
    
    ---
    CodiceCivile.ai - Privacy-first legal AI platform
    © {datetime.now().year} All rights reserved
    """
    
    return html_content, text_content


def generate_subscription_receipt_email(user_name: str, amount: float, currency: str) -> tuple[str, str]:
    """Generate subscription payment receipt email"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #2563eb;">Payment Successful</h1>
            <p>Hi {user_name},</p>
            <p>Thank you for your payment. Your subscription is now active.</p>
            <div style="background-color: #f3f4f6; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Amount:</strong> {amount:.2f} {currency.upper()}</p>
                <p style="margin: 10px 0 0 0;"><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            <p>You can manage your subscription in your dashboard.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{settings.FRONTEND_URL}/dashboard" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    View Dashboard
                </a>
            </div>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                CodiceCivile.ai - Privacy-first legal AI platform<br>
                © {datetime.now().year} All rights reserved
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Payment Successful
    
    Hi {user_name},
    
    Thank you for your payment. Your subscription is now active.
    
    Amount: {amount:.2f} {currency.upper()}
    Date: {datetime.now().strftime('%B %d, %Y')}
    
    Manage your subscription: {settings.FRONTEND_URL}/dashboard
    
    ---
    CodiceCivile.ai - Privacy-first legal AI platform
    © {datetime.now().year} All rights reserved
    """
    
    return html_content, text_content


from datetime import datetime
