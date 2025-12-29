from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models.hospital import Hospital
from app.models.common import BloodTransfusionRequest, Recipient, Notification, DonationAppointment
from app.models.donor import Donor
from app.models.user import User
from app.utils.helpers import role_required, format_date, format_datetime, get_status_color, get_cities, get_donors_by_blood_group
from datetime import datetime, timedelta

hospital_bp = Blueprint('hospital', __name__)

@hospital_bp.route('/hospital/dashboard')
@login_required
@role_required(['hospital'])
def dashboard():
    """Hospital dashboard"""
    hospital = current_user.hospital
    
    if not hospital:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    # Get recent requests
    recent_requests = hospital.transfusion_requests.order_by(BloodTransfusionRequest.created_at.desc()).limit(5).all()
    
    # Get recent recipients
    recent_recipients = hospital.recipients.order_by(Recipient.created_at.desc()).limit(5).all()
    
    # Get unread notifications
    unread_notifications = current_user.notifications.filter_by(is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Statistics
    total_requests = hospital.transfusion_requests.count()
    pending_requests = hospital.transfusion_requests.filter_by(status='pending').count()
    approved_requests = hospital.transfusion_requests.filter_by(status='approved').count()
    total_recipients = hospital.recipients.count()
    
    return render_template('hospital/dashboard.html',
                         hospital=hospital,
                         recent_requests=recent_requests,
                         recent_recipients=recent_recipients,
                         unread_notifications=unread_notifications,
                         total_requests=total_requests,
                         pending_requests=pending_requests,
                         approved_requests=approved_requests,
                         total_recipients=total_recipients)

@hospital_bp.route('/hospital/profile', methods=['GET', 'POST'])
@login_required
@role_required(['hospital'])
def profile():
    """Hospital profile management"""
    hospital = current_user.hospital
    
    if not hospital:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    if request.method == 'POST':
        # Update basic info
        current_user.name = request.form.get('name')
        hospital.phone = request.form.get('phone')
        hospital.address = request.form.get('address')
        hospital.city = request.form.get('city')
        
        # Update new fields
        age = request.form.get('age')
        if age:
            try:
                hospital.age = int(age)
            except ValueError:
                flash('Invalid age format.', 'danger')
                return redirect(url_for('hospital.profile'))
        
        hospital.gender = request.form.get('gender')
        hospital.hospital_type = request.form.get('hospital_type')
        hospital.specialties = request.form.get('specialties')
        
        # Update license number if changed
        new_license_number = request.form.get('license_number')
        if new_license_number and new_license_number != hospital.license_number:
            # Check if license number already exists
            existing_hospital = Hospital.query.filter_by(license_number=new_license_number).first()
            if existing_hospital and existing_hospital.id != hospital.id:
                flash('License number already exists.', 'danger')
                return redirect(url_for('hospital.profile'))
            hospital.license_number = new_license_number
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('hospital.profile'))
    
    cities = get_cities()
    states = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
        'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
        'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
        'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
        'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
    ]
    
    return render_template('hospital/profile.html', hospital=hospital, cities=cities, states=states)

@hospital_bp.route('/hospital/request-blood', methods=['GET', 'POST'])
@login_required
@role_required(['hospital'])
def request_blood():
    """Submit blood transfusion request"""
    hospital = current_user.hospital
    
    if not hospital:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    if request.method == 'POST':
        blood_group = request.form.get('blood_group')
        quantity = request.form.get('quantity')
        urgency = request.form.get('urgency')
        required_by_date = request.form.get('required_by_date')
        reason = request.form.get('reason')
        recipient_id = request.form.get('recipient_id')
        
        if not all([blood_group, quantity, urgency]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('hospital/request_blood.html')
        
        try:
            quantity = float(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            flash('Invalid quantity. Please enter a valid number.', 'danger')
            return render_template('hospital/request_blood.html')
        
        # Validate urgency level
        valid_urgency_levels = ['normal', 'urgent', 'emergency']
        if urgency not in valid_urgency_levels:
            flash('Invalid urgency level.', 'danger')
            return render_template('hospital/request_blood.html')
        
        # Parse required by date
        required_date = None
        if required_by_date:
            try:
                required_date = datetime.strptime(required_by_date, "%Y-%m-%d").date()
                if required_date < datetime.now().date():
                    flash('Required by date must be in the future.', 'danger')
                    return render_template('hospital/request_blood.html')
            except ValueError:
                flash('Invalid date format.', 'danger')
                return render_template('hospital/request_blood.html')
        
        # Create blood request
        blood_request = BloodTransfusionRequest(
            hospital_id=hospital.id,
            recipient_id=recipient_id if recipient_id else None,
            blood_group=blood_group,
            quantity=quantity,
            urgency=urgency,
            required_by_date=required_date,
            reason=reason
        )
        
        db.session.add(blood_request)
        db.session.commit()
        
        flash('Blood request submitted successfully! It will be reviewed by admin.', 'success')
        return redirect(url_for('hospital.requests'))
    
    # Get recipients for dropdown
    recipients = hospital.recipients.all()
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    urgency_levels = ['normal', 'urgent', 'emergency']
    
    return render_template('hospital/request_blood.html',
                         recipients=recipients,
                         blood_groups=blood_groups,
                         urgency_levels=urgency_levels)

@hospital_bp.route('/hospital/requests')
@login_required
@role_required(['hospital'])
def requests():
    """View blood transfusion requests"""
    hospital = current_user.hospital
    
    if not hospital:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = hospital.transfusion_requests
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    requests = query.order_by(BloodTransfusionRequest.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('hospital/requests.html', requests=requests, status_filter=status_filter)

@hospital_bp.route('/hospital/recipients', methods=['GET', 'POST'])
@login_required
@role_required(['hospital'])
def recipients():
    """Manage recipients"""
    hospital = current_user.hospital
    
    if not hospital:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        blood_group = request.form.get('blood_group')
        contact = request.form.get('contact')
        age = request.form.get('age')
        gender = request.form.get('gender')
        remarks = request.form.get('remarks')
        
        if not all([name, blood_group]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('hospital/recipients.html')
        
        # Validate blood group
        valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if blood_group not in valid_blood_groups:
            flash('Invalid blood group.', 'danger')
            return render_template('hospital/recipients.html')
        
        # Validate age
        if age:
            try:
                age = int(age)
                if age < 0 or age > 150:
                    raise ValueError("Invalid age")
            except ValueError:
                flash('Invalid age. Please enter a valid number.', 'danger')
                return render_template('hospital/recipients.html')
        
        # Create recipient
        recipient = Recipient(
            hospital_id=hospital.id,
            name=name,
            blood_group=blood_group,
            contact=contact,
            age=age,
            gender=gender,
            remarks=remarks
        )
        
        db.session.add(recipient)
        db.session.commit()
        
        flash('Recipient added successfully!', 'success')
        return redirect(url_for('hospital.recipients'))
    
    page = request.args.get('page', 1, type=int)
    recipients = hospital.recipients.order_by(Recipient.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    genders = ['Male', 'Female', 'Other']
    
    return render_template('hospital/recipients.html',
                         recipients=recipients,
                         blood_groups=blood_groups,
                         genders=genders)

@hospital_bp.route('/hospital/recipients/<int:recipient_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['hospital'])
def edit_recipient(recipient_id):
    """Edit recipient details"""
    recipient = Recipient.query.get_or_404(recipient_id)
    
    # Check if recipient belongs to current hospital
    if recipient.hospital_id != current_user.hospital.id:
        flash('You can only edit your own recipients.', 'danger')
        return redirect(url_for('hospital.recipients'))
    
    if request.method == 'POST':
        recipient.name = request.form.get('name')
        recipient.blood_group = request.form.get('blood_group')
        recipient.contact = request.form.get('contact')
        recipient.age = request.form.get('age')
        recipient.gender = request.form.get('gender')
        recipient.remarks = request.form.get('remarks')
        
        # Validate age
        if recipient.age:
            try:
                recipient.age = int(recipient.age)
                if recipient.age < 0 or recipient.age > 150:
                    raise ValueError("Invalid age")
            except ValueError:
                flash('Invalid age. Please enter a valid number.', 'danger')
                return render_template('hospital/edit_recipient.html', recipient=recipient)
        
        db.session.commit()
        flash('Recipient updated successfully!', 'success')
        return redirect(url_for('hospital.recipients'))
    
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    genders = ['Male', 'Female', 'Other']
    
    return render_template('hospital/edit_recipient.html',
                         recipient=recipient,
                         blood_groups=blood_groups,
                         genders=genders)

@hospital_bp.route('/hospital/recipients/<int:recipient_id>/delete')
@login_required
@role_required(['hospital'])
def delete_recipient(recipient_id):
    """Delete recipient"""
    recipient = Recipient.query.get_or_404(recipient_id)
    
    # Check if recipient belongs to current hospital
    if recipient.hospital_id != current_user.hospital.id:
        flash('You can only delete your own recipients.', 'danger')
        return redirect(url_for('hospital.recipients'))
    
    db.session.delete(recipient)
    db.session.commit()
    
    flash('Recipient deleted successfully!', 'success')
    return redirect(url_for('hospital.recipients'))

@hospital_bp.route('/hospital/notifications')
@login_required
@role_required(['hospital'])
def notifications():
    """View notifications"""
    page = request.args.get('page', 1, type=int)
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('hospital/notifications.html', notifications=notifications)

@hospital_bp.route('/hospital/mark-notification-read/<int:notification_id>')
@login_required
@role_required(['hospital'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        flash('Invalid notification.', 'danger')
        return redirect(url_for('hospital.notifications'))
    
    notification.is_read = True
    db.session.commit()
    
    flash('Notification marked as read.', 'success')
    return redirect(url_for('hospital.notifications'))

@hospital_bp.route('/hospital/suggested-donors/<blood_group>')
@login_required
@role_required(['hospital'])
def suggested_donors(blood_group):
    """Get suggested donors for blood group"""
    hospital = current_user.hospital
    
    if not hospital:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    # Get donors by blood group in the same city
    donors = get_donors_by_blood_group(blood_group, hospital.city)
    
    # If no donors in same city, get from nearby cities
    if not donors:
        donors = get_donors_by_blood_group(blood_group)
    
    return render_template('hospital/suggested_donors.html',
                         donors=donors,
                         blood_group=blood_group,
                         hospital_city=hospital.city)

@hospital_bp.route('/hospital/appointments')
@login_required
@role_required(['hospital'])
def appointments():
    """View hospital appointments with filtering"""
    hospital = current_user.hospital
    
    if not hospital:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    # Get filter parameters
    status_filter = request.args.get('status', 'upcoming')
    search_query = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = hospital.appointments
    
    # Apply status filter
    if status_filter == 'upcoming':
        query = query.filter(DonationAppointment.status.in_(['pending', 'confirmed']))
        query = query.filter(DonationAppointment.appointment_date >= datetime.now())
    elif status_filter == 'completed':
        query = query.filter(DonationAppointment.status == 'completed')
    elif status_filter == 'cancelled':
        query = query.filter(DonationAppointment.status == 'cancelled')
    # 'all' shows everything
    
    # Apply search filter
    if search_query:
        query = query.join(DonationAppointment.donor).join(Donor.user)
        query = query.filter(User.name.ilike(f'%{search_query}%'))
    
    # Apply date range filter
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(DonationAppointment.appointment_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(DonationAppointment.appointment_date <= date_to_obj)
        except ValueError:
            pass
    
    # Order and paginate
    appointments = query.order_by(DonationAppointment.appointment_date.desc()).paginate(
        page=page, per_page=5, error_out=False)
    
    # Get counts for each tab
    upcoming_count = hospital.appointments.filter(
        DonationAppointment.status.in_(['pending', 'confirmed']),
        DonationAppointment.appointment_date >= datetime.now()
    ).count()
    completed_count = hospital.appointments.filter_by(status='completed').count()
    cancelled_count = hospital.appointments.filter_by(status='cancelled').count()
    all_count = hospital.appointments.count()
    
    return render_template('hospital/appointments.html', 
                         appointments=appointments,
                         status_filter=status_filter,
                         search_query=search_query,
                         date_from=date_from,
                         date_to=date_to,
                         upcoming_count=upcoming_count,
                         completed_count=completed_count,
                         cancelled_count=cancelled_count,
                         all_count=all_count) 