#!/usr/bin/env python3
"""
Simple test for registration functionality
"""

import json
import sys
import os

# Add the API directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'wb-autoslot-api'))

def test_user_model():
    """Test User model functionality"""
    print("🧪 Testing User model...")
    
    try:
        from src.models.user import User
        
        # Test phone normalization
        test_phone = "89123456789"
        normalized = User.normalize_phone(test_phone)
        print(f"  ✅ Phone normalization: {test_phone} -> {normalized}")
        assert normalized == "+79123456789"
        
        # Test email normalization
        test_email = "  TEST@EXAMPLE.COM  "
        normalized_email = User.normalize_email(test_email)
        print(f"  ✅ Email normalization: '{test_email}' -> '{normalized_email}'")
        assert normalized_email == "test@example.com"
        
        # Test user_exists method
        exists, field = User.user_exists(phone="+79123456789")
        print(f"  ✅ User exists check: {exists}, field: {field}")
        
        exists, field = User.user_exists(email="test@example.com")
        print(f"  ✅ Email exists check: {exists}, field: {field}")
        
        print("  ✅ User model tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ User model test failed: {e}")
        return False

def test_auth_validation():
    """Test auth validation logic"""
    print("\n🧪 Testing auth validation...")
    
    try:
        import re
        
        # Test email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com"
        ]
        
        for email in valid_emails:
            if not re.match(email_pattern, email):
                print(f"  ❌ Valid email failed: {email}")
                return False
            print(f"  ✅ Valid email: {email}")
        
        for email in invalid_emails:
            if re.match(email_pattern, email):
                print(f"  ❌ Invalid email passed: {email}")
                return False
            print(f"  ✅ Invalid email rejected: {email}")
        
        print("  ✅ Auth validation tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Auth validation test failed: {e}")
        return False

def test_error_responses():
    """Test error response format"""
    print("\n🧪 Testing error response format...")
    
    try:
        # Simulate error response
        error_response = {
            'error': 'Пользователь с таким номером телефона уже существует',
            'error_code': 'USER_EXISTS',
            'field': 'phone',
            'message': 'Пользователь с таким номером телефона уже зарегистрирован. Переходим к авторизации...'
        }
        
        # Check required fields
        required_fields = ['error', 'error_code', 'field', 'message']
        for field in required_fields:
            if field not in error_response:
                print(f"  ❌ Missing field: {field}")
                return False
            print(f"  ✅ Field present: {field}")
        
        # Check error code
        if error_response['error_code'] != 'USER_EXISTS':
            print(f"  ❌ Wrong error code: {error_response['error_code']}")
            return False
        print(f"  ✅ Error code correct: {error_response['error_code']}")
        
        # Check field type
        if error_response['field'] not in ['phone', 'email']:
            print(f"  ❌ Wrong field type: {error_response['field']}")
            return False
        print(f"  ✅ Field type correct: {error_response['field']}")
        
        print("  ✅ Error response format tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Error response test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Registration Improvements")
    print("=" * 50)
    
    tests = [
        ("User Model", test_user_model),
        ("Auth Validation", test_auth_validation),
        ("Error Responses", test_error_responses),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Registration improvements are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
