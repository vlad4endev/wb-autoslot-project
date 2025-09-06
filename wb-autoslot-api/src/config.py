"""
Configuration settings for WB AutoSlot API
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    
    # WB Service
    WB_BROWSER_HEADLESS = os.environ.get('WB_BROWSER_HEADLESS', 'true').lower() == 'true'
    WB_BROWSER_TIMEOUT = int(os.environ.get('WB_BROWSER_TIMEOUT', '30000'))
    WB_MAX_RETRIES = int(os.environ.get('WB_MAX_RETRIES', '3'))
    
    # Task Worker
    WORKER_CHECK_INTERVAL = int(os.environ.get('WORKER_CHECK_INTERVAL', '60'))  # seconds
    TASK_DEFAULT_INTERVAL = int(os.environ.get('TASK_DEFAULT_INTERVAL', '30'))  # minutes
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '3600'))  # seconds
    
    # Notifications
    NOTIFICATIONS_ENABLED = os.environ.get('NOTIFICATIONS_ENABLED', 'true').lower() == 'true'
    EMAIL_SMTP_SERVER = os.environ.get('EMAIL_SMTP_SERVER')
    EMAIL_SMTP_PORT = int(os.environ.get('EMAIL_SMTP_PORT', '587'))
    EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    EMAIL_FROM = os.environ.get('EMAIL_FROM')
    
    # Telegram (optional)
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Backup
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() == 'true'
    
    # Monitoring
    PROMETHEUS_ENABLED = os.environ.get('PROMETHEUS_ENABLED', 'true').lower() == 'true'
    METRICS_ENABLED = os.environ.get('METRICS_ENABLED', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_app.db'
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///prod_app.db'
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
