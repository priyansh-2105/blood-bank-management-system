from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user
from datetime import datetime, timedelta
import os
import csv

def role_required(roles):
    """Decorator to check user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def format_date(date, format_str="%B %d, %Y"):
    """Format date for display"""
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")
    return date.strftime(format_str)

def format_datetime(dt, format_str="%B %d, %Y at %I:%M %p"):
    """Format datetime for display"""
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return dt.strftime(format_str)

def get_blood_groups():
    """Get list of blood groups"""
    return ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

def get_urgency_levels():
    """Get list of urgency levels"""
    return ['normal', 'urgent', 'emergency']

def get_appointment_statuses():
    """Get list of appointment statuses"""
    return ['pending', 'confirmed', 'completed', 'cancelled']

def get_request_statuses():
    """Get list of request statuses"""
    return ['pending', 'approved', 'fulfilled', 'rejected']

def get_cities():
    """Get list of cities from CSV file"""
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'city.csv')
        if os.path.exists(csv_path):
            cities = []
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'city' in row:
                        cities.append(row['city'])
            return cities if cities else get_fallback_cities()
        else:
            return get_fallback_cities()
    except Exception:
        return get_fallback_cities()

def get_fallback_cities():
    """Get fallback list of cities"""
    return [
        'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai',
        'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Surat',
        'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane',
        'Bhopal', 'Visakhapatnam', 'Pimpri-Chinchwad', 'Patna', 'Vadodara'
    ]

def get_hospitals_by_city(city):
    """Get hospitals in a specific city"""
    from app.models.hospital import Hospital
    return Hospital.query.filter_by(city=city, is_verified=True).all()

def get_donors_by_blood_group(blood_group, city=None):
    """Get donors by blood group and optionally by city"""
    from app.models.donor import Donor
    query = Donor.query.filter_by(blood_group=blood_group, is_available=True)
    if city:
        query = query.filter_by(city=city)
    return query.all()

def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    if not date_of_birth:
        return None
    today = datetime.now().date()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

def is_valid_donation_interval(last_donation_date, min_interval_days=56):
    """Check if enough time has passed since last donation"""
    if not last_donation_date:
        return True
    
    today = datetime.now().date()
    days_since_last = (today - last_donation_date).days
    return days_since_last >= min_interval_days

def generate_unique_filename(original_filename):
    """Generate unique filename for uploads"""
    from datetime import datetime
    import uuid
    
    name, ext = os.path.splitext(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"{name}_{timestamp}_{unique_id}{ext}"

def save_uploaded_file(file, folder):
    """Save uploaded file with unique name"""
    if file and file.filename:
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(folder, filename)
        file.save(file_path)
        return filename
    return None

def get_file_extension(filename):
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()

def is_allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return get_file_extension(filename) in allowed_extensions

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def get_status_color(status):
    """Get Bootstrap color class for status"""
    color_map = {
        'pending': 'warning',
        'confirmed': 'info',
        'completed': 'success',
        'cancelled': 'danger',
        'approved': 'success',
        'fulfilled': 'success',
        'rejected': 'danger',
        'normal': 'secondary',
        'urgent': 'warning',
        'emergency': 'danger'
    }
    return color_map.get(status, 'secondary')

def get_notification_icon(notification_type):
    """Get Font Awesome icon for notification type"""
    icon_map = {
        'info': 'fa-info-circle',
        'success': 'fa-check-circle',
        'warning': 'fa-exclamation-triangle',
        'error': 'fa-times-circle'
    }
    return icon_map.get(notification_type, 'fa-bell')

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'

def get_pagination_info(page, per_page, total):
    """Get pagination information"""
    total_pages = (total + per_page - 1) // per_page
    start_item = (page - 1) * per_page + 1
    end_item = min(page * per_page, total)
    
    return {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'start_item': start_item,
        'end_item': end_item,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    } 