from flask import Blueprint, render_template, request, flash, redirect, url_for, session, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models.user import User
from app.models.donor import Donor
from app.models.hospital import Hospital
from app.utils.otp import send_otp_email, verify_otp
from app.utils.helpers import role_required
from app.utils.email import send_notification_email
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        if current_user.role == 'donor':
            return redirect(url_for('donor.dashboard'))
        elif current_user.role == 'hospital':
            return redirect(url_for('hospital.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
    
    return render_template('index.html')

@auth_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory('static', 'favicon.svg')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields.', 'warning')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_verified:
                flash('Please verify your email before logging in.', 'warning')
                return render_template('auth/login.html')
            
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Redirect based on role
            if user.role == 'donor':
                return redirect(url_for('donor.dashboard'))
            elif user.role == 'hospital':
                return redirect(url_for('hospital.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        
        # Validation
        if not all([name, email, password, confirm_password, role]):
            flash('Please fill in all fields.', 'warning')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')
        
        if role not in ['donor', 'hospital']:
            flash('Invalid role selected.', 'danger')
            return render_template('auth/register.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = User(
            name=name,
            email=email,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Send OTP for email verification
        if send_otp_email(email, 'email_verification'):
            session['verification_email'] = email
            session['verification_role'] = role
            flash('Registration successful! Please check your email for verification code.', 'success')
            return redirect(url_for('auth.verify_email'))
        else:
            flash('Registration successful but failed to send verification email. Please contact support.', 'warning')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Email verification with OTP"""
    email = session.get('verification_email')
    role = session.get('verification_role')
    
    if not email or not role:
        flash('Invalid verification session.', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        
        if not otp:
            flash('Please enter the verification code.', 'warning')
            return render_template('auth/verify_email.html')
        
        success, message = verify_otp(email, otp, 'email_verification')
        
        if success:
            # Mark user as verified
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_verified = True
                db.session.commit()
                
                # Send welcome notification
                send_notification_email(
                    email,
                    "Welcome to Blood Bank Management System!",
                    f"Thank you for registering as a {role}. Your account has been verified successfully.",
                    "success"
                )
                
                flash('Email verified successfully! You can now log in.', 'success')
                session.pop('verification_email', None)
                session.pop('verification_role', None)
                return redirect(url_for('auth.login'))
            else:
                flash('User not found.', 'danger')
        else:
            # Provide more specific error messages
            if "Invalid OTP" in message:
                flash('Invalid verification code. Please check the code and try again.', 'danger')
            elif "expired" in message.lower():
                flash('Verification code has expired. Please request a new code.', 'danger')
            else:
                flash(message, 'danger')
    
    return render_template('auth/verify_email.html', email=email)

@auth_bp.route('/resend-otp')
def resend_otp():
    """Resend OTP for email verification"""
    email = session.get('verification_email')
    
    if not email:
        flash('Invalid verification session.', 'danger')
        return redirect(url_for('auth.login'))
    
    if send_otp_email(email, 'email_verification'):
        flash('Verification code has been resent to your email.', 'success')
    else:
        flash('Failed to send verification code. Please try again.', 'danger')
    
    return redirect(url_for('auth.verify_email'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - send reset OTP"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Please enter your email address.', 'warning')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            if send_otp_email(email, 'password_reset'):
                session['reset_email'] = email
                flash('Password reset code has been sent to your email.', 'success')
                return redirect(url_for('auth.reset_password'))
            else:
                flash('Failed to send reset code. Please try again.', 'danger')
        else:
            flash('Email not found in our records.', 'danger')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password with OTP"""
    email = session.get('reset_email')
    
    if not email:
        flash('Invalid reset session.', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([otp, new_password, confirm_password]):
            flash('Please fill in all fields.', 'warning')
            return render_template('auth/reset_password.html')
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/reset_password.html')
        
        success, message = verify_otp(email, otp, 'password_reset')
        
        if success:
            user = User.query.filter_by(email=email).first()
            if user:
                user.set_password(new_password)
                db.session.commit()
                
                flash('Password reset successfully! You can now log in with your new password.', 'success')
                session.pop('reset_email', None)
                return redirect(url_for('auth.login'))
            else:
                flash('User not found.', 'danger')
        else:
            flash(message, 'danger')
    
    return render_template('auth/reset_password.html')

@auth_bp.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    """Complete user profile after registration"""
    if current_user.role == 'donor':
        if current_user.donor:
            flash('Profile already completed.', 'info')
            return redirect(url_for('donor.dashboard'))
    elif current_user.role == 'hospital':
        if current_user.hospital:
            flash('Profile already completed.', 'info')
            return redirect(url_for('hospital.dashboard'))
    
    if request.method == 'POST':
        if current_user.role == 'donor':
            return complete_donor_profile()
        elif current_user.role == 'hospital':
            return complete_hospital_profile()
    
    return render_template('auth/complete_profile.html')

def complete_donor_profile():
    """Complete donor profile"""
    blood_group = request.form.get('blood_group')
    city = request.form.get('city')
    phone = request.form.get('phone')
    age = request.form.get('age')
    gender = request.form.get('gender')
    last_donation = request.form.get('last_donation')
    medical_conditions = request.form.get('medical_conditions')
    
    if not all([blood_group, city, phone, age, gender]):
        flash('Please fill in all required fields.', 'warning')
        return render_template('auth/complete_profile.html')
    
    # Validate blood group
    valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    if blood_group not in valid_blood_groups:
        flash('Invalid blood group.', 'danger')
        return render_template('auth/complete_profile.html')
    
    # Validate age
    try:
        age = int(age)
        if age < 18 or age > 100:
            flash('Age must be between 18 and 100.', 'danger')
            return render_template('auth/complete_profile.html')
    except ValueError:
        flash('Invalid age.', 'danger')
        return render_template('auth/complete_profile.html')
    
    # Create donor profile
    donor = Donor(
        user_id=current_user.id,
        blood_group=blood_group,
        city=city,
        phone=phone,
        age=age,
        gender=gender,
        last_donation_date=datetime.strptime(last_donation, '%Y-%m-%d').date() if last_donation else None,
        medical_conditions=medical_conditions
    )
    
    db.session.add(donor)
    db.session.commit()
    
    flash('Profile completed successfully!', 'success')
    return redirect(url_for('donor.dashboard'))

def complete_hospital_profile():
    """Complete hospital profile"""
    license_number = request.form.get('license_number')
    phone = request.form.get('phone')
    address = request.form.get('address')
    city = request.form.get('city')
    state = request.form.get('state', '')  # Add state field with default
    pincode = request.form.get('pincode', '')  # Add pincode field with default
    age = request.form.get('age')
    gender = request.form.get('gender')
    hospital_type = request.form.get('hospital_type')
    specialties = request.form.get('specialties')
    
    if not all([license_number, phone, address, city, age, gender, hospital_type]):
        flash('Please fill in all required fields.', 'warning')
        return render_template('auth/complete_profile.html')
    
    # Check if license number already exists
    if Hospital.query.filter_by(license_number=license_number).first():
        flash('License number already registered.', 'danger')
        return render_template('auth/complete_profile.html')
    
    # Validate age
    try:
        age = int(age)
        if age < 18 or age > 100:
            flash('Age must be between 18 and 100.', 'danger')
            return render_template('auth/complete_profile.html')
    except ValueError:
        flash('Invalid age.', 'danger')
        return render_template('auth/complete_profile.html')
    
    # Create hospital profile
    hospital = Hospital(
        user_id=current_user.id,
        license_id=license_number,  # Set license_id to same value as license_number
        license_number=license_number,
        phone=phone,
        address=address,
        city=city,
        state=state,  # Add state field
        pincode=pincode,  # Add pincode field
        age=age,
        gender=gender,
        hospital_type=hospital_type,
        specialties=specialties
    )
    
    db.session.add(hospital)
    db.session.commit()
    
    flash('Profile completed successfully!', 'success')
    return redirect(url_for('hospital.dashboard')) 