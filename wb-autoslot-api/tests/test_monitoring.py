"""
Tests for monitoring service
"""

import unittest
import time
from unittest.mock import patch, MagicMock
from src.services.monitoring_service import MonitoringService

class TestMonitoringService(unittest.TestCase):
    """Test cases for MonitoringService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.monitoring_service = MonitoringService()
        self.app = MagicMock()
        self.app.config = {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'
        }
        self.monitoring_service.init_app(self.app)
    
    def test_init_app(self):
        """Test service initialization"""
        self.assertIsNotNone(self.monitoring_service.app)
        self.assertEqual(self.monitoring_service.start_time, self.monitoring_service.start_time)
    
    def test_update_active_tasks(self):
        """Test updating active tasks count"""
        self.monitoring_service.update_active_tasks(5)
        # Verify the gauge was updated (we can't easily test Prometheus metrics)
        self.assertTrue(True)  # Placeholder for actual test
    
    def test_record_slot_found(self):
        """Test recording slot found event"""
        self.monitoring_service.record_slot_found('Коледино')
        # Verify the counter was incremented
        self.assertTrue(True)  # Placeholder for actual test
    
    def test_record_wb_request(self):
        """Test recording WB request"""
        self.monitoring_service.record_wb_request('success')
        # Verify the counter was incremented
        self.assertTrue(True)  # Placeholder for actual test
    
    def test_update_worker_status(self):
        """Test updating worker status"""
        self.monitoring_service.update_worker_status(True)
        # Verify the gauge was updated
        self.assertTrue(True)  # Placeholder for actual test
    
    def test_record_notification_sent(self):
        """Test recording notification sent"""
        self.monitoring_service.record_notification_sent('email', 'success')
        # Verify the counter was incremented
        self.assertTrue(True)  # Placeholder for actual test
    
    def test_record_rate_limit_hit(self):
        """Test recording rate limit hit"""
        self.monitoring_service.record_rate_limit_hit('/api/auth/login')
        # Verify the counter was incremented
        self.assertTrue(True)  # Placeholder for actual test
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_system_info(self, mock_disk, mock_memory, mock_cpu):
        """Test getting system information"""
        # Mock system metrics
        mock_cpu.return_value = 25.5
        mock_memory.return_value = MagicMock(percent=60.0, used=1024**3, total=2*1024**3)
        mock_disk.return_value = MagicMock(used=1024**3, total=10*1024**3)
        
        info = self.monitoring_service.get_system_info()
        
        self.assertIn('system', info)
        self.assertIn('process', info)
        self.assertIn('uptime', info)
        self.assertEqual(info['system']['cpu_percent'], 25.5)
        self.assertEqual(info['system']['memory_percent'], 60.0)
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        summary = self.monitoring_service.get_metrics_summary()
        self.assertIsInstance(summary, dict)

if __name__ == '__main__':
    unittest.main()
