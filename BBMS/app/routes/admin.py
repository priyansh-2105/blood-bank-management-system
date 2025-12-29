from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.donor import Donor
from app.models.hospital import Hospital
from app.models.common import BloodTransfusionRequest, DonationAppointment, BloodDonationRecord, Notification, Feedback, BloodInventory
from app.utils.helpers import role_required, format_date, format_datetime, get_status_color, get_cities
from app.utils.email import send_notification_email
from datetime import datetime, timedelta
import csv
from io import BytesIO

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def dashboard():
    """Admin dashboard with analytics"""
    
    # Get statistics
    total_donors = Donor.query.count()
    total_hospitals = Hospital.query.count()
    total_requests = BloodTransfusionRequest.query.count()
    pending_requests = BloodTransfusionRequest.query.filter_by(status='pending').count()
    total_appointments = DonationAppointment.query.count()
    completed_appointments = DonationAppointment.query.filter_by(status='completed').count()
    
    # Blood group statistics
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    blood_group_stats = {}
    
    for bg in blood_groups:
        donors_count = Donor.query.filter_by(blood_group=bg, is_available=True).count()
        requests_count = BloodTransfusionRequest.query.filter_by(blood_group=bg).count()
        blood_group_stats[bg] = {
            'donors': donors_count,
            'requests': requests_count
        }
    
    # Recent activities
    recent_requests = BloodTransfusionRequest.query.order_by(BloodTransfusionRequest.created_at.desc()).limit(5).all()
    recent_appointments = DonationAppointment.query.order_by(DonationAppointment.created_at.desc()).limit(5).all()
    recent_feedback = Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all()
    
    # City-wise statistics
    city_stats = db.session.query(Donor.city, db.func.count(Donor.id)).group_by(Donor.city).all()
    
    return render_template('admin/dashboard.html',
                         total_donors=total_donors,
                         total_hospitals=total_hospitals,
                         total_requests=total_requests,
                         pending_requests=pending_requests,
                         total_appointments=total_appointments,
                         completed_appointments=completed_appointments,
                         blood_group_stats=blood_group_stats,
                         recent_requests=recent_requests,
                         recent_appointments=recent_appointments,
                         recent_feedback=recent_feedback,
                         city_stats=city_stats)

@admin_bp.route('/admin/donors')
@login_required
@role_required(['admin'])
def donors():
    """Manage donors"""
    page = request.args.get('page', 1, type=int)
    blood_group_filter = request.args.get('blood_group', '')
    city_filter = request.args.get('city', '')
    
    query = Donor.query
    
    if blood_group_filter:
        query = query.filter_by(blood_group=blood_group_filter)
    
    if city_filter:
        query = query.filter_by(city=city_filter)
    
    donors = query.order_by(Donor.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    cities = get_cities()
    
    return render_template('admin/donors.html',
                         donors=donors,
                         blood_groups=blood_groups,
                         cities=cities,
                         blood_group_filter=blood_group_filter,
                         city_filter=city_filter)

@admin_bp.route('/admin/hospitals')
@login_required
@role_required(['admin'])
def hospitals():
    """Manage hospitals"""
    page = request.args.get('page', 1, type=int)
    city_filter = request.args.get('city', '')
    verified_filter = request.args.get('verified', '')
    
    query = Hospital.query
    
    if city_filter:
        query = query.filter_by(city=city_filter)
    
    if verified_filter == 'verified':
        query = query.filter_by(is_verified=True)
    elif verified_filter == 'unverified':
        query = query.filter_by(is_verified=False)
    
    hospitals = query.order_by(Hospital.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    cities = get_cities()
    
    return render_template('admin/hospitals.html',
                         hospitals=hospitals,
                         cities=cities,
                         city_filter=city_filter,
                         verified_filter=verified_filter)

@admin_bp.route('/admin/verify-hospital/<int:hospital_id>')
@login_required
@role_required(['admin'])
def verify_hospital(hospital_id):
    """Verify hospital"""
    hospital = Hospital.query.get_or_404(hospital_id)
    
    hospital.is_verified = True
    db.session.commit()
    
    # Send notification to hospital
    notification = Notification(
        user_id=hospital.user_id,
        title="Hospital Verification Approved",
        message="Your hospital has been verified by the admin. You can now submit blood requests.",
        type="success"
    )
    db.session.add(notification)
    db.session.commit()
    
    # Send email notification
    send_notification_email(
        hospital.user.email,
        "Hospital Verification Approved",
        "Your hospital has been verified by the admin. You can now submit blood requests.",
        "success"
    )
    
    flash('Hospital verified successfully!', 'success')
    return redirect(url_for('admin.hospitals'))

@admin_bp.route('/admin/requests')
@login_required
@role_required(['admin'])
def requests():
    """Manage blood transfusion requests"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    urgency_filter = request.args.get('urgency', '')
    
    query = BloodTransfusionRequest.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if urgency_filter:
        query = query.filter_by(urgency=urgency_filter)
    
    requests = query.order_by(BloodTransfusionRequest.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/requests.html',
                         requests=requests,
                         status_filter=status_filter,
                         urgency_filter=urgency_filter)

@admin_bp.route('/admin/approve-request/<int:request_id>')
@login_required
@role_required(['admin'])
def approve_request(request_id):
    """Approve blood transfusion request"""
    blood_request = BloodTransfusionRequest.query.get_or_404(request_id)
    
    if blood_request.status != 'pending':
        flash('Request is not pending for approval.', 'warning')
        return redirect(url_for('admin.requests'))
    
    blood_request.status = 'approved'
    db.session.commit()
    
    # Send notification to hospital
    notification = Notification(
        user_id=blood_request.hospital.user_id,
        title="Blood Request Approved",
        message=f"Your blood request for {blood_request.blood_group} has been approved.",
        type="success"
    )
    db.session.add(notification)
    db.session.commit()
    
    # Send email notification
    send_notification_email(
        blood_request.hospital.user.email,
        "Blood Request Approved",
        f"Your blood request for {blood_request.blood_group} has been approved.",
        "success"
    )
    
    flash('Request approved successfully!', 'success')
    return redirect(url_for('admin.requests'))

@admin_bp.route('/admin/reject-request/<int:request_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def reject_request(request_id):
    """Reject blood transfusion request"""
    blood_request = BloodTransfusionRequest.query.get_or_404(request_id)
    
    if blood_request.status != 'pending':
        flash('Request is not pending for approval.', 'warning')
        return redirect(url_for('admin.requests'))
    
    if request.method == 'POST':
        remarks = request.form.get('remarks', '')
        
        blood_request.status = 'rejected'
        blood_request.admin_remarks = remarks
        db.session.commit()
        
        # Send notification to hospital
        notification = Notification(
            user_id=blood_request.hospital.user_id,
            title="Blood Request Rejected",
            message=f"Your blood request for {blood_request.blood_group} has been rejected. Reason: {remarks}",
            type="error"
        )
        db.session.add(notification)
        db.session.commit()
        
        # Send email notification
        send_notification_email(
            blood_request.hospital.user.email,
            "Blood Request Rejected",
            f"Your blood request for {blood_request.blood_group} has been rejected. Reason: {remarks}",
            "error"
        )
        
        flash('Request rejected successfully!', 'success')
        return redirect(url_for('admin.requests'))
    
    return render_template('admin/reject_request.html', request=blood_request)

@admin_bp.route('/admin/appointments')
@login_required
@role_required(['admin'])
def appointments():
    """View all appointments"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = DonationAppointment.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    appointments = query.order_by(DonationAppointment.appointment_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/appointments.html',
                         appointments=appointments,
                         status_filter=status_filter)

@admin_bp.route('/admin/feedback')
@login_required
@role_required(['admin'])
def feedback():
    """View feedback messages"""
    page = request.args.get('page', 1, type=int)
    feedback_messages = Feedback.query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/feedback.html', feedback_messages=feedback_messages)

@admin_bp.route('/admin/export-data')
@login_required
@role_required(['admin'])
def export_data():
    """Export data as CSV"""
    data_type = request.args.get('type', 'donors')
    
    if data_type == 'donors':
        # Export donors data
        donors = Donor.query.all()
        data = []
        for donor in donors:
            data.append({
                'Name': donor.user.name,
                'Email': donor.user.email,
                'Blood Group': donor.blood_group,
                'City': donor.city,
                'Phone': donor.phone,
                'Available': donor.is_available,
                'Created': donor.created_at.strftime('%Y-%m-%d')
            })
        
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow(data[0].keys())  # Header
        for row in data:
            writer.writerow(row.values())
        output.seek(0)
        
        return send_file(
            BytesIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'donors_export_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    elif data_type == 'hospitals':
        # Export hospitals data
        hospitals = Hospital.query.all()
        data = []
        for hospital in hospitals:
            data.append({
                'Name': hospital.user.name,
                'Email': hospital.user.email,
                'License ID': hospital.license_id,
                'City': hospital.city,
                'State': hospital.state,
                'Phone': hospital.phone,
                'Verified': hospital.is_verified,
                'Created': hospital.created_at.strftime('%Y-%m-%d')
            })
        
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow(data[0].keys())  # Header
        for row in data:
            writer.writerow(row.values())
        output.seek(0)
        
        return send_file(
            BytesIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'hospitals_export_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    elif data_type == 'requests':
        # Export blood requests data
        requests = BloodTransfusionRequest.query.all()
        data = []
        for req in requests:
            data.append({
                'Hospital': req.hospital.user.name,
                'Blood Group': req.blood_group,
                'Quantity': req.quantity,
                'Urgency': req.urgency,
                'Status': req.status,
                'Created': req.created_at.strftime('%Y-%m-%d'),
                'Required By': req.required_by_date.strftime('%Y-%m-%d') if req.required_by_date else ''
            })
        
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow(data[0].keys())  # Header
        for row in data:
            writer.writerow(row.values())
        output.seek(0)
        
        return send_file(
            BytesIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'requests_export_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    flash('Invalid export type.', 'danger')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/notifications')
@login_required
@role_required(['admin'])
def notifications():
    """View all notifications"""
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/notifications.html', notifications=notifications)

@admin_bp.route('/admin/send-notification', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def send_notification():
    """Send notification to users"""
    if request.method == 'POST':
        user_type = request.form.get('user_type')  # all, donors, hospitals
        title = request.form.get('title')
        message = request.form.get('message')
        notification_type = request.form.get('type', 'info')
        
        if not all([title, message]):
            flash('Please fill in all fields.', 'warning')
            return render_template('admin/send_notification.html')
        
        # Get users based on type
        if user_type == 'all':
            users = User.query.filter(User.role.in_(['donor', 'hospital'])).all()
        elif user_type == 'donors':
            users = User.query.filter_by(role='donor').all()
        elif user_type == 'hospitals':
            users = User.query.filter_by(role='hospital').all()
        else:
            flash('Invalid user type.', 'danger')
            return render_template('admin/send_notification.html')
        
        # Create notifications
        for user in users:
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                type=notification_type
            )
            db.session.add(notification)
            
            # Send email notification
            send_notification_email(user.email, title, message, notification_type)
        
        db.session.commit()
        flash(f'Notification sent to {len(users)} users successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/send_notification.html') 