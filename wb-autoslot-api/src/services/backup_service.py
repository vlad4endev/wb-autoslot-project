"""
Backup service for database and files
"""

import os
import shutil
import sqlite3
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import gzip
import json

logger = logging.getLogger(__name__)

class BackupService:
    """Service for creating and managing backups"""
    
    def __init__(self):
        self.app = None
        self.backup_dir = None
        self.retention_days = 30
    
    def init_app(self, app):
        """Initialize backup service with Flask app"""
        self.app = app
        self.backup_dir = os.path.join(app.instance_path, 'backups')
        self.retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        logger.info(f"Backup service initialized. Backup directory: {self.backup_dir}")
    
    def create_database_backup(self, backup_type='manual'):
        """Create a database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"database_backup_{backup_type}_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Get database path from config
            db_url = self.app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_url.startswith('sqlite:///'):
                db_path = db_url.replace('sqlite:///', '')
            else:
                # For PostgreSQL, we'll use pg_dump
                return self._create_postgresql_backup(backup_type)
            
            # Copy SQLite database
            shutil.copy2(db_path, backup_path)
            
            # Compress the backup
            compressed_path = f"{backup_path}.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            os.remove(backup_path)
            
            # Create backup metadata
            metadata = {
                'type': 'database',
                'backup_type': backup_type,
                'timestamp': timestamp,
                'database_url': db_url,
                'file_size': os.path.getsize(compressed_path),
                'created_at': datetime.now().isoformat()
            }
            
            metadata_path = f"{compressed_path}.meta"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Database backup created: {compressed_path}")
            return {
                'success': True,
                'backup_path': compressed_path,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_postgresql_backup(self, backup_type):
        """Create PostgreSQL backup using pg_dump"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"postgresql_backup_{backup_type}_{timestamp}.sql"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Parse database URL
            db_url = self.app.config.get('SQLALCHEMY_DATABASE_URI', '')
            # Extract connection details from URL
            # Format: postgresql://user:password@host:port/database
            
            # Run pg_dump
            cmd = ['pg_dump', db_url]
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            # Compress the backup
            compressed_path = f"{backup_path}.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            os.remove(backup_path)
            
            # Create backup metadata
            metadata = {
                'type': 'database',
                'backup_type': backup_type,
                'timestamp': timestamp,
                'database_url': db_url,
                'file_size': os.path.getsize(compressed_path),
                'created_at': datetime.now().isoformat()
            }
            
            metadata_path = f"{compressed_path}.meta"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"PostgreSQL backup created: {compressed_path}")
            return {
                'success': True,
                'backup_path': compressed_path,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating PostgreSQL backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_files_backup(self, backup_type='manual'):
        """Create a backup of important files"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"files_backup_{backup_type}_{timestamp}.tar.gz"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Define directories to backup
            backup_dirs = [
                'logs',
                'database',
                'static'
            ]
            
            # Create tar.gz archive
            cmd = ['tar', '-czf', backup_path] + backup_dirs
            result = subprocess.run(cmd, cwd=self.app.instance_path, 
                                 stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"tar failed: {result.stderr}")
            
            # Create backup metadata
            metadata = {
                'type': 'files',
                'backup_type': backup_type,
                'timestamp': timestamp,
                'directories': backup_dirs,
                'file_size': os.path.getsize(backup_path),
                'created_at': datetime.now().isoformat()
            }
            
            metadata_path = f"{backup_path}.meta"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Files backup created: {backup_path}")
            return {
                'success': True,
                'backup_path': backup_path,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating files backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_full_backup(self, backup_type='manual'):
        """Create a full backup (database + files)"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.backup_dir, f"full_backup_{backup_type}_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create database backup
            db_result = self.create_database_backup(backup_type)
            if db_result['success']:
                # Move database backup to full backup directory
                db_backup_path = db_result['backup_path']
                db_backup_name = os.path.basename(db_backup_path)
                shutil.move(db_backup_path, os.path.join(backup_dir, db_backup_name))
                shutil.move(f"{db_backup_path}.meta", os.path.join(backup_dir, f"{db_backup_name}.meta"))
            
            # Create files backup
            files_result = self.create_files_backup(backup_type)
            if files_result['success']:
                # Move files backup to full backup directory
                files_backup_path = files_result['backup_path']
                files_backup_name = os.path.basename(files_backup_path)
                shutil.move(files_backup_path, os.path.join(backup_dir, files_backup_name))
                shutil.move(f"{files_backup_path}.meta", os.path.join(backup_dir, f"{files_backup_name}.meta"))
            
            # Create full backup metadata
            metadata = {
                'type': 'full',
                'backup_type': backup_type,
                'timestamp': timestamp,
                'database_backup': db_result.get('metadata', {}),
                'files_backup': files_result.get('metadata', {}),
                'created_at': datetime.now().isoformat()
            }
            
            metadata_path = os.path.join(backup_dir, 'backup_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create tar.gz of the full backup directory
            full_backup_path = f"{backup_dir}.tar.gz"
            cmd = ['tar', '-czf', full_backup_path, os.path.basename(backup_dir)]
            result = subprocess.run(cmd, cwd=self.backup_dir, 
                                 stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"tar failed: {result.stderr}")
            
            # Remove the directory
            shutil.rmtree(backup_dir)
            
            logger.info(f"Full backup created: {full_backup_path}")
            return {
                'success': True,
                'backup_path': full_backup_path,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating full backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                # Skip directories
                if os.path.isdir(file_path):
                    continue
                
                # Check if file is older than retention period
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    removed_count += 1
                    
                    # Also remove metadata file if it exists
                    metadata_path = f"{file_path}.meta"
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
            
            logger.info(f"Cleaned up {removed_count} old backups")
            return {
                'success': True,
                'removed_count': removed_count
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self):
        """List all available backups"""
        try:
            backups = []
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                # Skip directories
                if os.path.isdir(file_path):
                    continue
                
                # Skip metadata files
                if filename.endswith('.meta'):
                    continue
                
                # Get file info
                file_stat = os.stat(file_path)
                file_size = file_stat.st_size
                created_at = datetime.fromtimestamp(file_stat.st_ctime)
                
                # Try to load metadata
                metadata_path = f"{file_path}.meta"
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    except:
                        pass
                
                backups.append({
                    'filename': filename,
                    'file_path': file_path,
                    'file_size': file_size,
                    'created_at': created_at.isoformat(),
                    'metadata': metadata
                })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                'success': True,
                'backups': backups
            }
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def restore_backup(self, backup_path):
        """Restore from a backup"""
        try:
            # This is a basic implementation
            # In production, you'd want more sophisticated restore logic
            
            if not os.path.exists(backup_path):
                raise Exception("Backup file not found")
            
            # Extract backup
            extract_dir = os.path.join(self.backup_dir, 'restore_temp')
            os.makedirs(extract_dir, exist_ok=True)
            
            cmd = ['tar', '-xzf', backup_path, '-C', extract_dir]
            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Extract failed: {result.stderr}")
            
            # Find database backup in extracted files
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.db') or file.endswith('.sql'):
                        db_backup_path = os.path.join(root, file)
                        
                        # Restore database
                        if file.endswith('.db'):
                            # SQLite restore
                            db_url = self.app.config.get('SQLALCHEMY_DATABASE_URI', '')
                            if db_url.startswith('sqlite:///'):
                                target_db = db_url.replace('sqlite:///', '')
                                shutil.copy2(db_backup_path, target_db)
                        elif file.endswith('.sql'):
                            # PostgreSQL restore
                            cmd = ['psql', self.app.config.get('SQLALCHEMY_DATABASE_URI', '')]
                            with open(db_backup_path, 'r') as f:
                                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
                            
                            if result.returncode != 0:
                                raise Exception(f"PostgreSQL restore failed: {result.stderr}")
            
            # Clean up
            shutil.rmtree(extract_dir)
            
            logger.info(f"Backup restored from: {backup_path}")
            return {
                'success': True,
                'message': 'Backup restored successfully'
            }
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global backup service instance
backup_service = BackupService()
