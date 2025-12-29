from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models.donor import Donor
from app.models.hospital import Hospital
from app.models.common import DonationAppointment, BloodDonationRecord, Notification
from app.models.hospital import Hospital
from app.models.user import User
from app.utils.helpers import role_required, format_date, format_datetime, get_status_color, get_cities, get_hospitals_by_city
from app.utils.certificate import generate_html_certificate, generate_pdf_certificate
from app.utils.helpers import save_uploaded_file, is_allowed_file
from datetime import datetime, timedelta
import os
from io import BytesIO

donor_bp = Blueprint('donor', __name__)

@donor_bp.route('/donor/dashboard')
@login_required
@role_required(['donor'])
def dashboard():
    """Donor dashboard"""
    donor = current_user.donor
    
    if not donor:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    # Get recent appointments
    recent_appointments = donor.appointments.order_by(DonationAppointment.appointment_date.desc()).limit(5).all()
    
    # Get recent donations
    recent_donations = donor.donation_records.order_by(BloodDonationRecord.donation_date.desc()).limit(5).all()
    
    # Get unread notifications
    unread_notifications = current_user.notifications.filter_by(is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Statistics
    total_donations = donor.donation_records.count()
    total_appointments = donor.appointments.count()
    pending_appointments = donor.appointments.filter_by(status='pending').count()
    
    return render_template('donor/dashboard.html',
                         donor=donor,
                         recent_appointments=recent_appointments,
                         recent_donations=recent_donations,
                         unread_notifications=unread_notifications,
                         total_donations=total_donations,
                         total_appointments=total_appointments,
                         pending_appointments=pending_appointments)

@donor_bp.route('/donor/profile', methods=['GET', 'POST'])
@login_required
@role_required(['donor'])
def profile():
    """Donor profile management"""
    donor = current_user.donor
    
    if not donor:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    if request.method == 'POST':
        # Update basic info
        current_user.name = request.form.get('name')
        donor.phone = request.form.get('phone')
        donor.address = request.form.get('address')
        donor.city = request.form.get('city')
        
        # Update new fields
        age = request.form.get('age')
        if age:
            try:
                donor.age = int(age)
            except ValueError:
                flash('Invalid age format.', 'danger')
                return redirect(url_for('donor.profile'))
        
        donor.gender = request.form.get('gender')
        donor.medical_conditions = request.form.get('medical_conditions')
        
        # Update availability
        donor.is_available = 'is_available' in request.form
        
        # Update blood group if changed
        new_blood_group = request.form.get('blood_group')
        if new_blood_group and new_blood_group != donor.blood_group:
            donor.blood_group = new_blood_group
        
        # Handle profile photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                if is_allowed_file(file.filename, {'.jpg', '.jpeg', '.png', '.gif'}):
                    # Delete old photo if exists
                    if donor.photo:
                        old_photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], donor.photo)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    # Save new photo
                    filename = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
                    if filename:
                        donor.photo = filename
                else:
                    flash('Invalid file type. Please upload JPG, PNG, or GIF images only.', 'danger')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('donor.profile'))
    
    cities = get_cities()
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    return render_template('donor/profile.html', donor=donor, cities=cities, blood_groups=blood_groups)

@donor_bp.route('/donor/book-appointment', methods=['GET', 'POST'])
@login_required
@role_required(['donor'])
def book_appointment():
    """Book blood donation appointment"""
    donor = current_user.donor
    
    if not donor:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    if request.method == 'POST':
        hospital_id = request.form.get('hospital_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        notes = request.form.get('notes')
        
        if not all([hospital_id, appointment_date, appointment_time]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('donor/book_appointment.html')
        
        # Combine date and time
        try:
            appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return render_template('donor/book_appointment.html')
        
        # Check if appointment is in the future
        if appointment_datetime <= datetime.now():
            flash('Appointment must be scheduled for a future date and time.', 'danger')
            return render_template('donor/book_appointment.html')
        
        # Check if donor is available for donation
        if not donor.is_available:
            flash('You are currently not available for blood donation.', 'warning')
            return render_template('donor/book_appointment.html')
        
        # Check donation interval
        if donor.last_donation_date:
            days_since_last = (datetime.now().date() - donor.last_donation_date).days
            if days_since_last < 56:  # Minimum 56 days between donations
                remaining_days = 56 - days_since_last
                flash(f'You must wait {remaining_days} more days before your next donation.', 'warning')
                return render_template('donor/book_appointment.html')
        
        # Create appointment
        appointment = DonationAppointment(
            donor_id=donor.id,
            hospital_id=hospital_id,
            appointment_date=appointment_datetime,
            notes=notes
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        flash('Appointment booked successfully! You will receive a confirmation email.', 'success')
        return redirect(url_for('donor.appointments'))
    
    # Get all hospitals for the dropdown
    hospitals = Hospital.query.all()
    cities = get_cities()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('donor/book_appointment.html', hospitals=hospitals, cities=cities, today=today)

@donor_bp.route('/donor/appointments')
@login_required
@role_required(['donor'])
def appointments():
    """View donor appointments with filtering"""
    donor = current_user.donor
    
    if not donor:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    # Get filter parameters
    status_filter = request.args.get('status', 'upcoming')
    search_query = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = donor.appointments
    
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
        query = query.join(DonationAppointment.hospital).join(Hospital.user)
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
        page=page, per_page=5, error_out=False
    )
    
    # Get counts for each tab
    upcoming_count = donor.appointments.filter(
        DonationAppointment.status.in_(['pending', 'confirmed']),
        DonationAppointment.appointment_date >= datetime.now()
    ).count()
    completed_count = donor.appointments.filter_by(status='completed').count()
    cancelled_count = donor.appointments.filter_by(status='cancelled').count()
    all_count = donor.appointments.count()
    
    return render_template('donor/appointments.html', 
                         appointments=appointments,
                         status_filter=status_filter,
                         search_query=search_query,
                         date_from=date_from,
                         date_to=date_to,
                         upcoming_count=upcoming_count,
                         completed_count=completed_count,
                         cancelled_count=cancelled_count,
                         all_count=all_count)

@donor_bp.route('/donor/donations')
@login_required
@role_required(['donor'])
def donations():
    """View donation history"""
    donor = current_user.donor
    
    if not donor:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    page = request.args.get('page', 1, type=int)
    donations = donor.donation_records.order_by(BloodDonationRecord.donation_date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('donor/donations.html', donations=donations)

@donor_bp.route('/donor/certificate/<int:donation_id>')
@login_required
@role_required(['donor'])
def download_certificate(donation_id):
    """Download donation certificate"""
    donation = BloodDonationRecord.query.get_or_404(donation_id)
    
    # Check if the donation belongs to the current user
    if donation.donor.user_id != current_user.id:
        flash('You can only download your own certificates.', 'danger')
        return redirect(url_for('donor.donations'))
    
    format_type = request.args.get('format', 'html')
    
    if format_type == 'pdf':
        pdf_data, certificate_id = generate_pdf_certificate(donation)
        
        # Update certificate ID in database
        donation.certificate_id = certificate_id
        db.session.commit()
        
        return send_file(
            BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'donation_certificate_{certificate_id}.pdf'
        )
    else:
        html_content, certificate_id = generate_html_certificate(donation)
        
        # Update certificate ID in database
        donation.certificate_id = certificate_id
        db.session.commit()
        
        return html_content

@donor_bp.route('/donor/notifications')
@login_required
@role_required(['donor'])
def notifications():
    """View notifications"""
    page = request.args.get('page', 1, type=int)
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('donor/notifications.html', notifications=notifications)

@donor_bp.route('/donor/mark-notification-read/<int:notification_id>')
@login_required
@role_required(['donor'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        flash('Invalid notification.', 'danger')
        return redirect(url_for('donor.notifications'))
    
    notification.is_read = True
    db.session.commit()
    
    flash('Notification marked as read.', 'success')
    return redirect(url_for('donor.notifications'))

@donor_bp.route('/donor/toggle-availability')
@login_required
@role_required(['donor'])
def toggle_availability():
    """Toggle donor availability"""
    donor = current_user.donor
    
    if not donor:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('auth.complete_profile'))
    
    donor.is_available = not donor.is_available
    db.session.commit()
    
    status = "available" if donor.is_available else "unavailable"
    flash(f'You are now {status} for blood donation.', 'success')
    
    return redirect(url_for('donor.dashboard'))

@donor_bp.route('/api/hospitals/<city>')
@login_required
@role_required(['donor'])
def get_hospitals_by_city_api(city):
    """API endpoint to get hospitals by city"""
    hospitals = get_hospitals_by_city(city)
    hospital_list = []
    
    for hospital in hospitals:
        hospital_list.append({
            'id': hospital.id,
            'name': hospital.user.name,
            'address': hospital.address,
            'phone': hospital.phone
        })
    
    return {'hospitals': hospital_list} 