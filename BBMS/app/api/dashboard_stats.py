from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.donor import Donor
from app.models.hospital import Hospital
from app.models.common import BloodTransfusionRequest, DonationAppointment, BloodDonationRecord
from app.utils.helpers import role_required
from datetime import datetime, timedelta

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/inventory')
@login_required
@role_required(['admin'])
def inventory():
    """Get blood inventory statistics"""
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    inventory_data = []
    
    for bg in blood_groups:
        # Count available donors
        available_donors = Donor.query.filter_by(blood_group=bg, is_available=True).count()
        
        # Count recent donations (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_donations = BloodDonationRecord.query.filter(
            BloodDonationRecord.blood_group == bg,
            BloodDonationRecord.donation_date >= thirty_days_ago
        ).count()
        
        # Count pending requests
        pending_requests = BloodTransfusionRequest.query.filter_by(
            blood_group=bg, status='pending'
        ).count()
        
        inventory_data.append({
            'blood_group': bg,
            'available_donors': available_donors,
            'recent_donations': recent_donations,
            'pending_requests': pending_requests
        })
    
    return jsonify({'inventory': inventory_data})

@stats_bp.route('/requests')
@login_required
@role_required(['admin'])
def requests():
    """Get request statistics"""
    # Request status counts
    pending_count = BloodTransfusionRequest.query.filter_by(status='pending').count()
    approved_count = BloodTransfusionRequest.query.filter_by(status='approved').count()
    fulfilled_count = BloodTransfusionRequest.query.filter_by(status='fulfilled').count()
    rejected_count = BloodTransfusionRequest.query.filter_by(status='rejected').count()
    
    # Urgency counts
    normal_count = BloodTransfusionRequest.query.filter_by(urgency='normal').count()
    urgent_count = BloodTransfusionRequest.query.filter_by(urgency='urgent').count()
    emergency_count = BloodTransfusionRequest.query.filter_by(urgency='emergency').count()
    
    # Monthly trends (last 6 months)
    monthly_data = []
    for i in range(6):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        month_requests = BloodTransfusionRequest.query.filter(
            BloodTransfusionRequest.created_at >= month_start,
            BloodTransfusionRequest.created_at <= month_end
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%B %Y'),
            'requests': month_requests
        })
    
    return jsonify({
        'status_counts': {
            'pending': pending_count,
            'approved': approved_count,
            'fulfilled': fulfilled_count,
            'rejected': rejected_count
        },
        'urgency_counts': {
            'normal': normal_count,
            'urgent': urgent_count,
            'emergency': emergency_count
        },
        'monthly_trends': monthly_data
    })

@stats_bp.route('/donations')
@login_required
@role_required(['admin'])
def donations():
    """Get donation statistics"""
    # Total donations by blood group
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    donation_data = []
    
    for bg in blood_groups:
        total_donations = BloodDonationRecord.query.filter_by(blood_group=bg).count()
        total_units = db.session.query(db.func.sum(BloodDonationRecord.quantity)).filter_by(blood_group=bg).scalar() or 0
        
        donation_data.append({
            'blood_group': bg,
            'total_donations': total_donations,
            'total_units': float(total_units)
        })
    
    # Monthly donation trends
    monthly_donations = []
    for i in range(6):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        month_donations = BloodDonationRecord.query.filter(
            BloodDonationRecord.donation_date >= month_start,
            BloodDonationRecord.donation_date <= month_end
        ).count()
        
        monthly_donations.append({
            'month': month_start.strftime('%B %Y'),
            'donations': month_donations
        })
    
    return jsonify({
        'donation_data': donation_data,
        'monthly_donations': monthly_donations
    })

@stats_bp.route('/city-stats')
@login_required
@role_required(['admin'])
def city_stats():
    """Get city-wise statistics"""
    # Donors by city
    donor_city_stats = db.session.query(
        Donor.city, 
        db.func.count(Donor.id)
    ).group_by(Donor.city).all()
    
    # Hospitals by city
    hospital_city_stats = db.session.query(
        Hospital.city, 
        db.func.count(Hospital.id)
    ).group_by(Hospital.city).all()
    
    # Requests by city
    request_city_stats = db.session.query(
        Hospital.city, 
        db.func.count(BloodTransfusionRequest.id)
    ).join(BloodTransfusionRequest).group_by(Hospital.city).all()
    
    return jsonify({
        'donor_cities': [{'city': city, 'count': count} for city, count in donor_city_stats],
        'hospital_cities': [{'city': city, 'count': count} for city, count in hospital_city_stats],
        'request_cities': [{'city': city, 'count': count} for city, count in request_city_stats]
    })

@stats_bp.route('/user-activity')
@login_required
@role_required(['admin'])
def user_activity():
    """Get user activity statistics"""
    # Recent registrations (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    new_donors = Donor.query.join(Donor.user).filter(
        Donor.created_at >= thirty_days_ago
    ).count()
    
    new_hospitals = Hospital.query.join(Hospital.user).filter(
        Hospital.created_at >= thirty_days_ago
    ).count()
    
    # Active users (users with activity in last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    active_donors = Donor.query.join(Donor.user).filter(
        Donor.updated_at >= seven_days_ago
    ).count()
    
    active_hospitals = Hospital.query.join(Hospital.user).filter(
        Hospital.updated_at >= seven_days_ago
    ).count()
    
    return jsonify({
        'new_users': {
            'donors': new_donors,
            'hospitals': new_hospitals
        },
        'active_users': {
            'donors': active_donors,
            'hospitals': active_hospitals
        }
    }) 