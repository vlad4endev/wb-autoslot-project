from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Task
from src.services.task_worker import task_worker
import logging

logger = logging.getLogger(__name__)
worker_bp = Blueprint('worker', __name__)

@worker_bp.route('/worker/status', methods=['GET'])
@jwt_required()
def get_worker_status():
    """Get worker status"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        status = task_worker.get_status()
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting worker status: {e}")
        return jsonify({'error': 'Failed to get worker status'}), 500

@worker_bp.route('/worker/tasks/<int:task_id>/start', methods=['POST'])
@jwt_required()
def start_task_worker(task_id):
    """Start a task in the worker"""
    try:
        current_user_id = get_jwt_identity()
        
        task = Task.query.filter_by(
            id=task_id,
            user_id=int(current_user_id)
        ).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        if task.status != 'active':
            return jsonify({'error': 'Task is not active'}), 400
        
        # Add task to worker
        interval = request.json.get('interval', 30) if request.json else 30
        task_worker.add_task(task_id, interval)
        
        return jsonify({
            'message': f'Task {task_id} added to worker with interval {interval} minutes'
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting task worker: {e}")
        return jsonify({'error': 'Failed to start task worker'}), 500

@worker_bp.route('/worker/tasks/<int:task_id>/stop', methods=['POST'])
@jwt_required()
def stop_task_worker(task_id):
    """Stop a task in the worker"""
    try:
        current_user_id = get_jwt_identity()
        
        task = Task.query.filter_by(
            id=task_id,
            user_id=int(current_user_id)
        ).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Remove task from worker
        task_worker.remove_task(task_id)
        
        return jsonify({
            'message': f'Task {task_id} removed from worker'
        }), 200
        
    except Exception as e:
        logger.error(f"Error stopping task worker: {e}")
        return jsonify({'error': 'Failed to stop task worker'}), 500

@worker_bp.route('/worker/cleanup', methods=['POST'])
@jwt_required()
def cleanup_worker():
    """Clean up completed tasks from worker"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Clean up old tasks
        task_worker.cleanup_old_tasks()
        
        return jsonify({
            'message': 'Worker cleanup completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up worker: {e}")
        return jsonify({'error': 'Failed to cleanup worker'}), 500

@worker_bp.route('/worker/restart', methods=['POST'])
@jwt_required()
def restart_worker():
    """Restart the worker"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Restart worker
        task_worker.stop()
        task_worker.start()
        
        return jsonify({
            'message': 'Worker restarted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error restarting worker: {e}")
        return jsonify({'error': 'Failed to restart worker'}), 500