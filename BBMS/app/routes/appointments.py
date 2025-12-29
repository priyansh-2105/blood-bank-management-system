from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.common import DonationAppointment, BloodDonationRecord, Notification
from app.utils.helpers import role_required, format_datetime, get_status_color
from app.utils.email import send_notification_email
from datetime import datetime

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments/<int:appointment_id>/confirm')
@login_required
@role_required(['hospital'])
def confirm_appointment(appointment_id):
    """Confirm donation appointment"""
    appointment = DonationAppointment.query.get_or_404(appointment_id)
    
    # Check if appointment belongs to current hospital
    if appointment.hospital.user_id != current_user.id:
        flash('You can only confirm appointments for your hospital.', 'danger')
        return redirect(url_for('hospital.dashboard'))
    
    if appointment.status != 'pending':
        flash('Appointment is not pending for confirmation.', 'warning')
        return redirect(url_for('hospital.dashboard'))
    
    appointment.status = 'confirmed'
    db.session.commit()
    
    # Send notification to donor
    notification = Notification(
        user_id=appointment.donor.user_id,
        title="Appointment Confirmed",
        message=f"Your blood donation appointment on {appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')} has been confirmed.",
        type="success"
    )
    db.session.add(notification)
    db.session.commit()
    
    # Send email notification
    send_notification_email(
        appointment.donor.user.email,
        "Appointment Confirmed",
        f"Your blood donation appointment on {appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')} has been confirmed.",
        "success"
    )
    
    flash('Appointment confirmed successfully!', 'success')
    return redirect(url_for('hospital.dashboard'))

@appointments_bp.route('/appointments/<int:appointment_id>/complete', methods=['GET', 'POST'])
@login_required
@role_required(['hospital'])
def complete_appointment(appointment_id):
    """Complete donation appointment"""
    appointment = DonationAppointment.query.get_or_404(appointment_id)
    
    # Check if appointment belongs to current hospital
    if appointment.hospital.user_id != current_user.id:
        flash('You can only complete appointments for your hospital.', 'danger')
        return redirect(url_for('hospital.dashboard'))
    
    if appointment.status != 'confirmed':
        flash('Appointment must be confirmed before completion.', 'warning')
        return redirect(url_for('hospital.dashboard'))
    
    if request.method == 'POST':
        quantity = request.form.get('quantity')
        
        if not quantity:
            flash('Please enter the quantity donated.', 'warning')
            return render_template('appointments/complete_appointment.html', appointment=appointment)
        
        try:
            quantity = float(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            flash('Invalid quantity. Please enter a valid number.', 'danger')
            return render_template('appointments/complete_appointment.html', appointment=appointment)
        
        # Mark appointment as completed
        appointment.status = 'completed'
        db.session.commit()
        
        # Create blood donation record
        donation_record = BloodDonationRecord(
            appointment_id=appointment.id,
            donor_id=appointment.donor.id,
            quantity=quantity,
            blood_group=appointment.donor.blood_group,
            donation_date=datetime.now()
        )
        db.session.add(donation_record)
        
        # Update donor's last donation date
        appointment.donor.last_donation_date = datetime.now().date()
        db.session.commit()
        
        # Send notification to donor
        notification = Notification(
            user_id=appointment.donor.user_id,
            title="Donation Completed",
            message=f"Thank you for your blood donation! {quantity} units of {appointment.donor.blood_group} blood have been recorded.",
            type="success"
        )
        db.session.add(notification)
        db.session.commit()
        
        # Send email notification
        send_notification_email(
            appointment.donor.user.email,
            "Donation Completed",
            f"Thank you for your blood donation! {quantity} units of {appointment.donor.blood_group} blood have been recorded.",
            "success"
        )
        
        flash('Appointment completed successfully!', 'success')
        return redirect(url_for('hospital.dashboard'))
    
    return render_template('appointments/complete_appointment.html', appointment=appointment)

@appointments_bp.route('/appointments/<int:appointment_id>/cancel', methods=['GET', 'POST'])
@login_required
@role_required(['donor', 'hospital'])
def cancel_appointment(appointment_id):
    """Cancel donation appointment"""
    appointment = DonationAppointment.query.get_or_404(appointment_id)
    
    # Check if user has permission to cancel
    if current_user.role == 'donor' and appointment.donor.user_id != current_user.id:
        flash('You can only cancel your own appointments.', 'danger')
        return redirect(url_for('donor.dashboard'))
    
    if current_user.role == 'hospital' and appointment.hospital.user_id != current_user.id:
        flash('You can only cancel appointments for your hospital.', 'danger')
        return redirect(url_for('hospital.dashboard'))
    
    if appointment.status not in ['pending', 'confirmed']:
        flash('Appointment cannot be cancelled.', 'warning')
        return redirect(url_for('donor.dashboard' if current_user.role == 'donor' else 'hospital.dashboard'))
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    # Send notification to the other party
    if current_user.role == 'donor':
        notification_user_id = appointment.hospital.user_id
        notification_message = f"Blood donation appointment with {appointment.donor.user.name} has been cancelled."
    else:
        notification_user_id = appointment.donor.user_id
        notification_message = f"Your blood donation appointment on {appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')} has been cancelled."
    
    notification = Notification(
        user_id=notification_user_id,
        title="Appointment Cancelled",
        message=notification_message,
        type="warning"
    )
    db.session.add(notification)
    db.session.commit()
    
    flash('Appointment cancelled successfully!', 'success')
    return redirect(url_for('donor.dashboard' if current_user.role == 'donor' else 'hospital.dashboard')) 