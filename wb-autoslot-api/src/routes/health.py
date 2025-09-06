from flask import Blueprint, jsonify
from src.models.user import db, User, Task, WBAccount
from src.services.task_worker import task_worker
from src.services.wb_service import wb_service
from src.services.notification_service import notification_service
import logging
import psutil
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'wb-autoslot-api'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with system metrics"""
    try:
        # Database health
        db_healthy = True
        db_error = None
        try:
            with db.engine.connect() as conn:
                conn.execute("SELECT 1")
        except Exception as e:
            db_healthy = False
            db_error = str(e)
        
        # Worker health
        worker_status = task_worker.get_status()
        
        # WB Service health
        wb_service_healthy = wb_service.is_running if hasattr(wb_service, 'is_running') else True
        
        # Notification service health
        notification_healthy = (
            notification_service.email_enabled or 
            notification_service.telegram_enabled or 
            not notification_service.app.config.get('NOTIFICATIONS_ENABLED', False)
        )
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database statistics
        db_stats = {}
        if db_healthy:
            try:
                db_stats = {
                    'users_count': User.query.count(),
                    'tasks_count': Task.query.count(),
                    'active_tasks_count': Task.query.filter_by(status='active').count(),
                    'wb_accounts_count': WBAccount.query.count(),
                    'recent_tasks': Task.query.filter(
                        Task.created_at >= datetime.utcnow() - timedelta(hours=24)
                    ).count()
                }
            except Exception as e:
                db_stats = {'error': str(e)}
        
        health_data = {
            'status': 'healthy' if all([db_healthy, wb_service_healthy, notification_healthy]) else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'wb-autoslot-api',
            'version': '1.0.0',
            'components': {
                'database': {
                    'status': 'healthy' if db_healthy else 'unhealthy',
                    'error': db_error
                },
                'worker': {
                    'status': 'healthy' if worker_status['running'] else 'unhealthy',
                    'active_tasks': worker_status['active_tasks'],
                    'details': worker_status
                },
                'wb_service': {
                    'status': 'healthy' if wb_service_healthy else 'unhealthy'
                },
                'notifications': {
                    'status': 'healthy' if notification_healthy else 'unhealthy',
                    'email_enabled': notification_service.email_enabled,
                    'telegram_enabled': notification_service.telegram_enabled
                }
            },
            'system': {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
            },
            'database_stats': db_stats
        }
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness check for Kubernetes"""
    try:
        # Check if all critical services are ready
        ready = True
        checks = {}
        
        # Database check
        try:
            with db.engine.connect() as conn:
                conn.execute("SELECT 1")
            checks['database'] = 'ready'
        except Exception as e:
            checks['database'] = f'not ready: {str(e)}'
            ready = False
        
        # Worker check
        if task_worker.running:
            checks['worker'] = 'ready'
        else:
            checks['worker'] = 'not ready'
            ready = False
        
        status_code = 200 if ready else 503
        return jsonify({
            'status': 'ready' if ready else 'not ready',
            'checks': checks,
            'timestamp': datetime.utcnow().isoformat()
        }), status_code
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'status': 'not ready',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """Liveness check for Kubernetes"""
    try:
        return jsonify({
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return jsonify({
            'status': 'dead',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
