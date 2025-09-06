#!/usr/bin/env python3
"""
Backup scheduler script for automated backups
"""

import os
import sys
import time
import schedule
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.backup_service import backup_service
from src.config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BackupScheduler:
    """Scheduler for automated backups"""
    
    def __init__(self):
        self.app = None
        self.running = False
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        backup_service.init_app(app)
    
    def create_daily_backup(self):
        """Create daily full backup"""
        try:
            logger.info("Starting daily backup...")
            result = backup_service.create_full_backup('scheduled')
            
            if result['success']:
                logger.info(f"Daily backup completed: {result['backup_path']}")
            else:
                logger.error(f"Daily backup failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in daily backup: {e}")
    
    def create_weekly_backup(self):
        """Create weekly full backup"""
        try:
            logger.info("Starting weekly backup...")
            result = backup_service.create_full_backup('scheduled')
            
            if result['success']:
                logger.info(f"Weekly backup completed: {result['backup_path']}")
            else:
                logger.error(f"Weekly backup failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in weekly backup: {e}")
    
    def cleanup_old_backups(self):
        """Clean up old backups"""
        try:
            logger.info("Starting backup cleanup...")
            result = backup_service.cleanup_old_backups()
            
            if result['success']:
                logger.info(f"Backup cleanup completed: {result['removed_count']} files removed")
            else:
                logger.error(f"Backup cleanup failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in backup cleanup: {e}")
    
    def start_scheduler(self):
        """Start the backup scheduler"""
        logger.info("Starting backup scheduler...")
        
        # Schedule daily backups at 2 AM
        schedule.every().day.at("02:00").do(self.create_daily_backup)
        
        # Schedule weekly backups on Sunday at 3 AM
        schedule.every().sunday.at("03:00").do(self.create_weekly_backup)
        
        # Schedule cleanup every day at 4 AM
        schedule.every().day.at("04:00").do(self.cleanup_old_backups)
        
        self.running = True
        
        logger.info("Backup scheduler started. Scheduled jobs:")
        logger.info("- Daily backup: 02:00")
        logger.info("- Weekly backup: Sunday 03:00")
        logger.info("- Cleanup: 04:00")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Backup scheduler stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Error in backup scheduler: {e}")
            self.running = False
    
    def stop_scheduler(self):
        """Stop the backup scheduler"""
        logger.info("Stopping backup scheduler...")
        self.running = False

def main():
    """Main function"""
    # Create Flask app
    from flask import Flask
    app = Flask(__name__)
    
    # Load configuration
    config_name = os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize scheduler
    scheduler = BackupScheduler()
    scheduler.init_app(app)
    
    # Start scheduler
    scheduler.start_scheduler()

if __name__ == "__main__":
    main()
