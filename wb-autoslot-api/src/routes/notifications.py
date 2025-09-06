from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User
from src.services.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)
notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications/test', methods=['POST'])
@jwt_required()
def test_notifications():
    """Test notification system"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Send test notification
        success = notification_service.send_test_notification(user)
        
        if success:
            return jsonify({
                'message': 'Test notification sent successfully'
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send test notification'
            }), 500
        
    except Exception as e:
        logger.error(f"Error testing notifications: {e}")
        return jsonify({'error': 'Failed to test notifications'}), 500

@notifications_bp.route('/notifications/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """Get notification settings"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        settings = {
            'email_enabled': notification_service.email_enabled,
            'telegram_enabled': notification_service.telegram_enabled,
            'notifications_enabled': notification_service.app.config.get('NOTIFICATIONS_ENABLED', False) if notification_service.app else False
        }
        
        return jsonify(settings), 200
        
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        return jsonify({'error': 'Failed to get notification settings'}), 500
