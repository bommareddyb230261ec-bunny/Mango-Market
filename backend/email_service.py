"""
Email and OTP Service for Mango Market Platform
Production-ready, secure, and reusable email/OTP logic.

Features:
- SMTP email sending with error handling
- OTP generation and verification (6-digit)
- Thread-safe in-memory OTP store (development)
- Async email sending using threading for non-blocking operations
- Structured logging for production monitoring

PRODUCTION NOTE:
- For high-volume deployments, migrating OTP to database or Redis is recommended
- Consider using Celery + RabbitMQ for distributed task queue
- Email sending is non-blocking (threaded) to prevent request timeout
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Callable
from threading import Lock, Thread
from datetime import datetime, timedelta, timezone
import secrets
import socket
import functools

# Configure logger
logger = logging.getLogger(__name__)

# =====================================================
# OTP STORAGE (In-memory for development)
# =====================================================
# OTP in-memory store (thread-safe for demo; use Redis/DB for production)
_otp_store: Dict[str, Dict[str, Any]] = {}
_otp_lock = Lock()


# =====================================================
# SMTP CONFIGURATION
# =====================================================
def _get_smtp_config():
    """Retrieve and validate SMTP configuration from environment variables."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    missing = [k for k, v in {
        'SMTP_SERVER': smtp_server,
        'SMTP_PORT': smtp_port,
        'SMTP_EMAIL': smtp_email,
        'SMTP_PASSWORD': smtp_password
    }.items() if not v]
    
    if missing:
        logger.error(f"Missing SMTP configuration: {', '.join(missing)}")
        raise ValueError(f"Missing SMTP config: {', '.join(missing)}")
    
    return str(smtp_server), int(smtp_port), str(smtp_email), str(smtp_password)


# =====================================================
# ASYNC EMAIL SENDING (Threading)
# =====================================================
def _send_email_async(to_email: str, subject: str, body: str, retries: int = 2):
    """
    Internal function that actually sends email (runs in thread).
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (HTML format)
        retries: Number of retries on failure
    """
    def _do_send():
        for attempt in range(1, retries + 1):
            try:
                smtp_server, smtp_port, smtp_email, smtp_password = _get_smtp_config()
                
                msg = MIMEMultipart()
                msg['From'] = smtp_email
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html'))
                
                with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
                    server.login(smtp_email, smtp_password)
                    server.send_message(msg)
                
                logger.info(f"Email sent successfully to {to_email}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP auth failed (attempt {attempt}/{retries}): {e}")
                if attempt == retries:
                    return False
                    
            except (smtplib.SMTPException, socket.timeout) as e:
                logger.error(f"SMTP error (attempt {attempt}/{retries}): {e}")
                if attempt == retries:
                    return False
                    
            except Exception as e:
                logger.exception(f"Unexpected error sending email to {to_email}: {e}")
                if attempt == retries:
                    return False
    
    _do_send()


def send_email(to_email: str, subject: str, body: str, async_mode: bool = True) -> bool:
    """
    Send email via SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (HTML format)
        async_mode: If True, send asynchronously (non-blocking). Default: True
    
    Returns:
        True if email queued/sent successfully, False on immediate error
    
    PRODUCTION NOTE:
    - async_mode=True (default) prevents request blocking
    - Email delivery failures are logged but don't block user request
    - For guaranteed delivery, implement retry queue with database/queue system
    """
    # Validate email format (basic check)
    if not to_email or '@' not in to_email:
        logger.warning(f"Invalid email address: {to_email}")
        return False
    
    try:
        if async_mode:
            # Send email in background thread (non-blocking)
            thread = Thread(
                target=_send_email_async,
                args=(to_email, subject, body),
                daemon=True
            )
            thread.start()
            logger.debug(f"Email queued for async sending to {to_email}")
            return True
        else:
            # Send synchronously (blocking) - use only in admin/critical paths
            _send_email_async(to_email, subject, body)
            return True
            
    except ValueError as ve:
        logger.error(f"SMTP configuration error: {ve}")
        return False
    except Exception as e:
        logger.exception(f"Error queueing email to {to_email}: {e}")
        return False


# =====================================================
# OTP MANAGEMENT
# =====================================================
def generate_otp(email: str) -> str:
    """
    Generate a 6-digit OTP and store it with 5-minute expiration.
    
    Args:
        email: Email address to generate OTP for
    
    Returns:
        6-digit OTP string
    """
    # Cryptographically secure random number
    otp = f"{secrets.randbelow(900000) + 100000:06d}"
    expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    with _otp_lock:
        _otp_store[email] = {
            'otp': otp,
            'expires': expiry,
            'attempts': 0
        }
        logger.info(f"OTP generated for {email}")
    
    return otp


def send_otp_email(email: str) -> bool:
    """
    Generate OTP and send it via email.
    
    Args:
        email: Recipient email address
    
    Returns:
        True if email sent successfully, False otherwise
    
    Raises:
        ValueError: If SMTP not configured
    """
    otp = generate_otp(email)
    
    subject = "Your Mango Market OTP"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e65100;">🥭 Your OTP for Mango Market</h2>
                
                <p>Please use the OTP below to complete your verification:</p>
                
                <div style="background: #f0f0f0; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
                    <h3 style="color: #2e7d32; font-size: 48px; letter-spacing: 10px; margin: 0;">{otp}</h3>
                    <p style="color: #666; margin: 10px 0;">Valid for 5 minutes</p>
                </div>
                
                <p style="color: #666; font-size: 0.9em; margin-top: 20px;">
                    If you didn't request this OTP, please ignore this email.<br>
                    For security, never share your OTP with anyone.
                </p>
                
                <p style="margin-top: 30px; color: #666; font-size: 0.9em;">
                    Best regards,<br>
                    <strong>Mango Market Team</strong>
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(email, subject, body, async_mode=True)


def verify_otp_check(email: str, otp: str) -> bool:
    """
    Verify OTP without consuming it (step 1: email verification).
    
    Args:
        email: Email address
        otp: OTP to verify
    
    Returns:
        True if OTP is valid and not expired, False otherwise
    """
    with _otp_lock:
        entry = _otp_store.get(email)
        
        if not entry:
            logger.warning(f"OTP verification attempted for non-existent email: {email}")
            return False
        
        if entry['otp'] != otp:
            entry['attempts'] = entry.get('attempts', 0) + 1
            logger.warning(f"Invalid OTP attempt #{entry['attempts']} for {email}")
            return False
        
        if datetime.now(timezone.utc) > entry['expires']:
            del _otp_store[email]
            logger.warning(f"OTP expired for {email}")
            return False
        
        logger.info(f"OTP verified (non-consuming) for {email}")
        return True


def verify_otp(email: str, otp: str) -> bool:
    """
    Verify OTP and consume it (step 2: password reset/critical action).
    
    Args:
        email: Email address
        otp: OTP to verify
    
    Returns:
        True if OTP is valid, not expired, and consumed successfully
    """
    with _otp_lock:
        entry = _otp_store.get(email)
        
        if not entry:
            logger.warning(f"OTP consumption attempted for non-existent email: {email}")
            return False
        
        if entry['otp'] != otp:
            logger.warning(f"Invalid OTP provided for password reset: {email}")
            return False
        
        if datetime.now(timezone.utc) > entry['expires']:
            del _otp_store[email]
            logger.warning(f"Expired OTP attempted for password reset: {email}")
            return False
        
        # Consume OTP (delete entry)
        del _otp_store[email]
        logger.info(f"OTP consumed (password reset) for {email}")
        return True


# =====================================================
# TEST/VERIFICATION ENDPOINT LOGIC
# =====================================================
def send_test_otp_email(email: str) -> Dict[str, object]:
    """
    Test endpoint for sending OTP email (development/debugging).
    
    Args:
        email: Email address to send test OTP to
    
    Returns:
        Dict with success status and message
    """
    try:
        success = send_otp_email(email)
        if success:
            return {
                "success": True,
                "message": f"OTP email queued for {email}. Check inbox in a few moments.",
                "test_mode": os.getenv('FLASK_ENV') != 'production'
            }
        else:
            return {
                "success": False,
                "message": f"Failed to queue OTP email to {email}. Check SMTP configuration."
            }
    except ValueError as ve:
        logger.error(f"SMTP configuration error in test: {ve}")
        return {
            "success": False,
            "message": str(ve),
            "error_type": "configuration"
        }


def send_weighment_confirmation_email(
    farmer_email: str,
    farmer_name: str,
    broker_name: str,
    market_name: str,
    final_weight_tons: float,
    final_price_per_kg: float,
    mango_variety: str,
    weighment_date: str
) -> bool:
    """
    Send weighment confirmation email to farmer after weighment is recorded.
    
    This email is sent asynchronously and doesn't block the HTTP response.
    
    Args:
        farmer_email: Farmer's email address
        farmer_name: Farmer's full name
        broker_name: Broker/market name
        market_name: Market area/location
        final_weight_tons: Final weight in tons
        final_price_per_kg: Final price per kg
        mango_variety: Mango variety
        weighment_date: Formatted date string (DD-MMM-YYYY)
    
    Returns:
        True if email queued successfully, False otherwise
    """
    subject = f"Weighment Confirmation - Order Processed"
    
    total_amount = final_weight_tons * 1000 * final_price_per_kg
    
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e65100;">🥭 Weighment Confirmation</h2>
                
                <p>Dear <strong>{farmer_name}</strong>,</p>
                
                <p>Your mango weighment has been successfully recorded at <strong>{broker_name}</strong>, {market_name}.</p>
                
                <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #e65100; margin: 20px 0;">
                    <p><strong>Weighment Details:</strong></p>
                    <table style="width: 100%; margin-top: 10px;">
                        <tr>
                            <td style="padding: 8px 0;">Weighment Date:</td>
                            <td style="padding: 8px 0; font-weight: bold;">{weighment_date}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">Mango Variety:</td>
                            <td style="padding: 8px 0; font-weight: bold;">{mango_variety}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">Final Weight:</td>
                            <td style="padding: 8px 0; font-weight: bold;">{final_weight_tons:.2f} Tons ({final_weight_tons * 1000:.0f} kg)</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">Price per kg:</td>
                            <td style="padding: 8px 0; font-weight: bold;">₹{final_price_per_kg:.2f}</td>
                        </tr>
                        <tr style="border-top: 2px solid #e65100; font-size: 1.1em;">
                            <td style="padding: 12px 0; font-weight: bold;">Total Amount:</td>
                            <td style="padding: 12px 0; font-weight: bold; color: #2e7d32;">₹{total_amount:,.2f}</td>
                        </tr>
                    </table>
                </div>
                
                <p>Your payment will be processed shortly. You can track your transaction status in your farmer dashboard.</p>
                
                <p style="margin-top: 30px; color: #666; font-size: 0.9em;">
                    Thank you for choosing Mango Market Platform!<br>
                    Best regards,<br>
                    <strong>Mango Market Team</strong>
                </p>
            </div>
        </body>
    </html>
    """
    
    total_amount = final_weight_tons * 1000 * final_price_per_kg
    
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e65100;">🥭 Weighment Confirmation</h2>
                
                <p>Dear <strong>{farmer_name}</strong>,</p>
                
                <p>Your mango weighment has been successfully recorded at <strong>{broker_name}</strong>, {market_name}.</p>
                
                <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #e65100; margin: 20px 0;">
                    <p><strong>Weighment Details:</strong></p>
                    <table style="width: 100%; margin-top: 10px;">
                        <tr>
                            <td style="padding: 8px 0;">Weighment Date:</td>
                            <td style="padding: 8px 0; font-weight: bold;">{weighment_date}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">Mango Variety:</td>
                            <td style="padding: 8px 0; font-weight: bold;">{mango_variety}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">Final Weight:</td>
                            <td style="padding: 8px 0; font-weight: bold;">{final_weight_tons:.2f} Tons ({final_weight_tons * 1000:.0f} kg)</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">Price per kg:</td>
                            <td style="padding: 8px 0; font-weight: bold;">₹{final_price_per_kg:.2f}</td>
                        </tr>
                        <tr style="border-top: 2px solid #e65100; font-size: 1.1em;">
                            <td style="padding: 12px 0; font-weight: bold;">Total Amount:</td>
                            <td style="padding: 12px 0; font-weight: bold; color: #2e7d32;">₹{total_amount:,.2f}</td>
                        </tr>
                    </table>
                </div>
                
                <p>Your payment will be processed shortly. You can track your transaction status in your farmer dashboard.</p>
                
                <p style="margin-top: 30px; color: #666; font-size: 0.9em;">
                    Thank you for choosing Mango Market Platform!<br>
                    Best regards,<br>
                    <strong>Mango Market Team</strong>
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(farmer_email, subject, body, async_mode=True)
