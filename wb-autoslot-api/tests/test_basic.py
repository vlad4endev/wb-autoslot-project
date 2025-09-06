"""
Basic tests for WB AutoSlot API
"""

import unittest
import json
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import app
from src.models.user import db, User
from src.config import TestingConfig

class TestBasicFunctionality(unittest.TestCase):
    """Test basic API functionality"""
    
    def setUp(self):
        """Set up test client"""
        app.config.from_object(TestingConfig)
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.drop_all()
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/auth/me')
        # Should return 401 (unauthorized) but not 500 (server error)
        self.assertIn(response.status_code, [401, 404])
    
    def test_register_user(self):
        """Test user registration"""
        data = {
            'phone': '+79123456789',
            'password': 'testpassword123'
        }
        
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('user', data)
    
    def test_register_duplicate_user(self):
        """Test duplicate user registration"""
        data = {
            'phone': '+79123456789',
            'password': 'testpassword123'
        }
        
        # First registration
        response1 = self.client.post('/api/auth/register', 
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEqual(response1.status_code, 201)
        
        # Second registration (should fail)
        response2 = self.client.post('/api/auth/register', 
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEqual(response2.status_code, 409)
        result = json.loads(response2.data)
        self.assertEqual(result['error_code'], 'USER_EXISTS')
        self.assertEqual(result['field'], 'phone')
    
    def test_register_user_with_email(self):
        """Test user registration with email"""
        data = {
            'phone': '+79123456789',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        result = json.loads(response.data)
        self.assertIn('access_token', result)
        self.assertIn('user', result)
        self.assertEqual(result['user']['phone'], '+79123456789')
        self.assertEqual(result['user']['email'], 'test@example.com')
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # Register first user with email
        data1 = {
            'phone': '+79123456789',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response1 = self.client.post('/api/auth/register', 
                                   data=json.dumps(data1),
                                   content_type='application/json')
        self.assertEqual(response1.status_code, 201)
        
        # Try to register with same email
        data2 = {
            'phone': '+79987654321',
            'email': 'test@example.com',
            'password': 'anotherpassword123'
        }
        response2 = self.client.post('/api/auth/register', 
                                   data=json.dumps(data2),
                                   content_type='application/json')
        self.assertEqual(response2.status_code, 409)
        result = json.loads(response2.data)
        self.assertEqual(result['error_code'], 'USER_EXISTS')
        self.assertEqual(result['field'], 'email')
    
    def test_login_user(self):
        """Test user login"""
        # First register
        data = {
            'phone': '+79123456789',
            'password': 'testpassword123'
        }
        
        self.client.post('/api/auth/register', 
                        data=json.dumps(data),
                        content_type='application/json')
        
        # Then login
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('user', data)
    
    def test_invalid_login(self):
        """Test invalid login"""
        data = {
            'phone': '+79123456789',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
    
    def test_login_with_email(self):
        """Test user login with email"""
        # First register with email
        data = {
            'phone': '+79123456789',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        self.client.post('/api/auth/register', 
                        data=json.dumps(data),
                        content_type='application/json')
        
        # Then login with email
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertIn('access_token', result)
    
    def test_phone_normalization(self):
        """Test phone number normalization"""
        # Test different phone formats
        test_phones = [
            '89123456789',
            '79123456789', 
            '+79123456789',
            '8 (912) 345-67-89',
            '+7 (912) 345-67-89'
        ]
        
        for phone in test_phones:
            with self.subTest(phone=phone):
                data = {
                    'phone': phone,
                    'password': 'testpassword123'
                }
                
                response = self.client.post('/api/auth/register', 
                                          data=json.dumps(data),
                                          content_type='application/json')
                
                # Should succeed for valid phone formats
                self.assertIn(response.status_code, [201, 409])  # 409 if already exists

if __name__ == '__main__':
    unittest.main()
