import random
import string
from datetime import datetime, timedelta
from app import db
from app.models.common import OTPVerification
from app.utils.email import send_email_otp

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def create_otp(email, otp_type="email_verification"):
    """Create and store OTP in database"""
    # Delete only expired or used OTPs for this email and type
    OTPVerification.query.filter_by(
        email=email, 
        type=otp_type
    ).filter(
        (OTPVerification.is_used == True) | 
        (OTPVerification.expires_at < datetime.utcnow())
    ).delete()
    
    # Check if there's already an active OTP
    active_otp = OTPVerification.query.filter_by(
        email=email,
        type=otp_type,
        is_used=False
    ).filter(OTPVerification.expires_at > datetime.utcnow()).first()
    
    if active_otp:
        # Return existing active OTP instead of creating a new one
        return active_otp.otp
    
    # Generate new OTP
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Store in database
    otp_record = OTPVerification(
        email=email,
        otp=otp,
        type=otp_type,
        expires_at=expires_at
    )
    db.session.add(otp_record)
    db.session.commit()
    
    return otp

def send_otp_email(email, otp_type="email_verification"):
    """Generate OTP and send via email"""
    otp = create_otp(email, otp_type)
    
    purpose = "verification"
    if otp_type == "password_reset":
        purpose = "password_reset"
    
    return send_email_otp(email, otp, purpose)

def verify_otp(email, otp, otp_type="email_verification"):
    """Verify OTP from database"""
    otp_record = OTPVerification.query.filter_by(
        email=email,
        otp=otp,
        type=otp_type,
        is_used=False
    ).first()
    
    if not otp_record:
        return False, "Invalid OTP"
    
    if datetime.utcnow() > otp_record.expires_at:
        return False, "OTP has expired"
    
    # Mark OTP as used
    otp_record.is_used = True
    db.session.commit()
    
    return True, "OTP verified successfully"

def cleanup_expired_otps():
    """Clean up expired OTPs from database"""
    expired_otps = OTPVerification.query.filter(
        OTPVerification.expires_at < datetime.utcnow()
    ).all()
    
    for otp in expired_otps:
        db.session.delete(otp)
    
    db.session.commit() 