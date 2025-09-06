"""
Tests for backup service
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
from src.services.backup_service import BackupService

class TestBackupService(unittest.TestCase):
    """Test cases for BackupService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.backup_service = BackupService()
        self.app = MagicMock()
        self.app.instance_path = tempfile.mkdtemp()
        self.app.config = {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'
        }
        self.backup_service.init_app(self.app)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.app.instance_path):
            shutil.rmtree(self.app.instance_path)
    
    def test_init_app(self):
        """Test service initialization"""
        self.assertIsNotNone(self.backup_service.app)
        self.assertIsNotNone(self.backup_service.backup_dir)
        self.assertTrue(os.path.exists(self.backup_service.backup_dir))
    
    @patch('os.path.exists')
    @patch('shutil.copy2')
    @patch('gzip.open')
    def test_create_database_backup_sqlite(self, mock_gzip, mock_copy, mock_exists):
        """Test creating SQLite database backup"""
        mock_exists.return_value = True
        
        result = self.backup_service.create_database_backup('test')
        
        self.assertTrue(result['success'])
        self.assertIn('backup_path', result)
        self.assertIn('metadata', result)
    
    @patch('subprocess.run')
    def test_create_database_backup_postgresql(self, mock_run):
        """Test creating PostgreSQL database backup"""
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/db'
        mock_run.return_value = MagicMock(returncode=0, stderr='')
        
        result = self.backup_service.create_database_backup('test')
        
        self.assertTrue(result['success'])
        self.assertIn('backup_path', result)
        self.assertIn('metadata', result)
    
    @patch('subprocess.run')
    def test_create_files_backup(self, mock_run):
        """Test creating files backup"""
        mock_run.return_value = MagicMock(returncode=0, stderr='')
        
        result = self.backup_service.create_files_backup('test')
        
        self.assertTrue(result['success'])
        self.assertIn('backup_path', result)
        self.assertIn('metadata', result)
    
    def test_cleanup_old_backups(self):
        """Test cleaning up old backups"""
        # Create a test backup file
        test_file = os.path.join(self.backup_service.backup_dir, 'test_backup.db.gz')
        with open(test_file, 'w') as f:
            f.write('test')
        
        result = self.backup_service.cleanup_old_backups()
        
        self.assertTrue(result['success'])
        self.assertIn('removed_count', result)
    
    def test_list_backups(self):
        """Test listing backups"""
        # Create a test backup file
        test_file = os.path.join(self.backup_service.backup_dir, 'test_backup.db.gz')
        with open(test_file, 'w') as f:
            f.write('test')
        
        result = self.backup_service.list_backups()
        
        self.assertTrue(result['success'])
        self.assertIn('backups', result)
        self.assertIsInstance(result['backups'], list)

if __name__ == '__main__':
    unittest.main()
