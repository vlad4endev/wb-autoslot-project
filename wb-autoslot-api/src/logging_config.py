"""
Logging configuration for WB AutoSlot API
"""

import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(app):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Get log level from config
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    log_file = os.path.join(log_dir, 'app.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # WB Service specific logger
    wb_logger = logging.getLogger('src.services.wb_service')
    wb_log_file = os.path.join(log_dir, 'wb_service.log')
    wb_handler = logging.handlers.RotatingFileHandler(
        wb_log_file, maxBytes=10*1024*1024, backupCount=3
    )
    wb_handler.setLevel(logging.INFO)
    wb_handler.setFormatter(detailed_formatter)
    wb_logger.addHandler(wb_handler)
    wb_logger.propagate = False
    
    # Task Worker specific logger
    worker_logger = logging.getLogger('src.services.task_worker')
    worker_log_file = os.path.join(log_dir, 'task_worker.log')
    worker_handler = logging.handlers.RotatingFileHandler(
        worker_log_file, maxBytes=10*1024*1024, backupCount=3
    )
    worker_handler.setLevel(logging.INFO)
    worker_handler.setFormatter(detailed_formatter)
    worker_logger.addHandler(worker_handler)
    worker_logger.propagate = False
    
    # Suppress some noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
    
    app.logger.info(f"Logging configured with level: {app.config.get('LOG_LEVEL', 'INFO')}")
    app.logger.info(f"Log files: {log_file}, {error_log_file}")

def log_api_request(request, response=None, user_id=None):
    """Log API request details"""
    logger = logging.getLogger('api_requests')
    
    log_data = {
        'method': request.method,
        'url': request.url,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if response:
        log_data.update({
            'status_code': response.status_code,
            'response_size': len(response.get_data()) if hasattr(response, 'get_data') else 0
        })
    
    logger.info(f"API Request: {log_data}")

def log_wb_action(action, account_id, task_id=None, details=None):
    """Log WB service actions"""
    logger = logging.getLogger('wb_actions')
    
    log_data = {
        'action': action,
        'account_id': account_id,
        'task_id': task_id,
        'details': details,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"WB Action: {log_data}")

def log_task_event(event_type, task_id, message, details=None):
    """Log task events"""
    logger = logging.getLogger('task_events')
    
    log_data = {
        'event_type': event_type,
        'task_id': task_id,
        'message': message,
        'details': details,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Task Event: {log_data}")
