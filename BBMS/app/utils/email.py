import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from flask_mail import Message
from app import mail
import os

def send_email_otp(email, otp, purpose="verification"):
    """Send OTP via email using Flask-Mail with fallback to smtplib"""
    
    subject = "Blood Bank Management System - Email Verification"
    if purpose == "password_reset":
        subject = "Blood Bank Management System - Password Reset"
    
    html_content = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center;">
                <h1>🩸 Blood Bank Management System</h1>
            </div>
            <div style="padding: 20px; background-color: #f8f9fa;">
                <h2>Your Verification Code</h2>
                <p>Hello!</p>
                <p>Your verification code is:</p>
                <div style="background-color: #e9ecef; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                    {otp}
                </div>
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <hr>
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated message from the Blood Bank Management System.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        # Try Flask-Mail first
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_content,
            sender=current_app.config.get('MAIL_USERNAME')
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Flask-Mail failed: {e}")
        
        # Fallback to smtplib
        try:
            smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('MAIL_PORT', 587)
            smtp_username = current_app.config.get('MAIL_USERNAME')
            smtp_password = current_app.config.get('MAIL_PASSWORD')
            
            if not smtp_username or not smtp_password:
                current_app.logger.error("SMTP credentials not configured")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_username
            msg['To'] = email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e2:
            current_app.logger.error(f"SMTP fallback failed: {e2}")
            return False

def send_notification_email(email, subject, message, notification_type="info"):
    """Send notification emails"""
    
    color_map = {
        "info": "#17a2b8",
        "success": "#28a745", 
        "warning": "#ffc107",
        "error": "#dc3545"
    }
    
    color = color_map.get(notification_type, "#17a2b8")
    
    html_content = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                <h1>🩸 Blood Bank Management System</h1>
            </div>
            <div style="padding: 20px; background-color: #f8f9fa;">
                <h2>{subject}</h2>
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    {message}
                </div>
                <hr>
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated message from the Blood Bank Management System.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_content,
            sender=current_app.config.get('MAIL_USERNAME')
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send notification email: {e}")
        return False 