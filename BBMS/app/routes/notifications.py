from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.common import Notification
from app.utils.helpers import role_required

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications')
@login_required
def notifications():
    """Redirect to role-specific notifications"""
    return redirect(url_for(current_user.role + '.notifications'))

@notifications_bp.route('/notifications/mark-read/<int:notification_id>')
@login_required
def mark_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        flash('Invalid notification.', 'danger')
        return redirect(url_for('notifications.notifications'))
    
    notification.is_read = True
    db.session.commit()
    
    flash('Notification marked as read.', 'success')
    return redirect(url_for('notifications.notifications'))

@notifications_bp.route('/notifications/mark-all-read')
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    unread_notifications = current_user.notifications.filter_by(is_read=False).all()
    
    for notification in unread_notifications:
        notification.is_read = True
    
    db.session.commit()
    
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.notifications'))

@notifications_bp.route('/api/notifications/unread-count')
@login_required
def unread_count():
    """Get unread notification count for AJAX"""
    count = current_user.notifications.filter_by(is_read=False).count()
    return jsonify({'count': count})

@notifications_bp.route('/api/notifications/recent')
@login_required
def recent_notifications():
    """Get recent notifications for AJAX"""
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).limit(5).all()
    
    notification_list = []
    for notification in notifications:
        notification_list.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'notifications': notification_list}) 