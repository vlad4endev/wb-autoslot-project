"""
Backup management routes
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.backup_service import backup_service
from src.middleware.rate_limiter import rate_limit
import os

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/create', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window_seconds=3600)  # 5 backups per hour
def create_backup():
    """Create a new backup"""
    try:
        data = request.get_json() or {}
        backup_type = data.get('type', 'manual')  # manual, scheduled, on-demand
        
        if backup_type not in ['manual', 'scheduled', 'on-demand']:
            return jsonify({'error': 'Invalid backup type'}), 400
        
        # Create backup based on type
        if backup_type == 'database':
            result = backup_service.create_database_backup(backup_type)
        elif backup_type == 'files':
            result = backup_service.create_files_backup(backup_type)
        else:
            result = backup_service.create_full_backup(backup_type)
        
        if result['success']:
            return jsonify({
                'message': 'Backup created successfully',
                'backup': result
            }), 201
        else:
            return jsonify({
                'error': 'Failed to create backup',
                'details': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@backup_bp.route('/list', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
def list_backups():
    """List all available backups"""
    try:
        result = backup_service.list_backups()
        
        if result['success']:
            return jsonify({
                'backups': result['backups'],
                'count': len(result['backups'])
            }), 200
        else:
            return jsonify({
                'error': 'Failed to list backups',
                'details': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@backup_bp.route('/download/<path:filename>', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=5, window_seconds=300)  # 5 downloads per 5 minutes
def download_backup(filename):
    """Download a backup file"""
    try:
        # Security check - ensure filename is safe
        if '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        backup_path = os.path.join(backup_service.backup_dir, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup not found'}), 404
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@backup_bp.route('/restore', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=2, window_seconds=3600)  # 2 restores per hour
def restore_backup():
    """Restore from a backup"""
    try:
        data = request.get_json()
        
        if not data or 'backup_path' not in data:
            return jsonify({'error': 'Backup path is required'}), 400
        
        backup_path = data['backup_path']
        
        # Security check
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        # Confirm restore
        confirm = data.get('confirm', False)
        if not confirm:
            return jsonify({
                'error': 'Restore confirmation required',
                'message': 'This action will overwrite current data. Set confirm=true to proceed.'
            }), 400
        
        result = backup_service.restore_backup(backup_path)
        
        if result['success']:
            return jsonify({
                'message': 'Backup restored successfully',
                'result': result
            }), 200
        else:
            return jsonify({
                'error': 'Failed to restore backup',
                'details': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@backup_bp.route('/cleanup', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=3, window_seconds=3600)  # 3 cleanups per hour
def cleanup_backups():
    """Clean up old backups"""
    try:
        result = backup_service.cleanup_old_backups()
        
        if result['success']:
            return jsonify({
                'message': f"Cleaned up {result['removed_count']} old backups",
                'removed_count': result['removed_count']
            }), 200
        else:
            return jsonify({
                'error': 'Failed to cleanup backups',
                'details': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@backup_bp.route('/status', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
def backup_status():
    """Get backup service status"""
    try:
        # Get backup directory info
        backup_dir = backup_service.backup_dir
        if not os.path.exists(backup_dir):
            return jsonify({
                'status': 'not_initialized',
                'message': 'Backup directory not found'
            }), 404
        
        # Get directory size
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1
        
        # Get retention policy
        retention_days = backup_service.retention_days
        
        return jsonify({
            'status': 'active',
            'backup_directory': backup_dir,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'retention_days': retention_days
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
