#!/usr/bin/env python3
"""
API Testing Script for WB AutoSlot
"""

import requests
import json
import time
import sys

API_BASE = "http://localhost:5000/api"

def test_health():
    """Test health endpoints"""
    print("🏥 Testing health endpoints...")
    
    try:
        # Basic health check
        response = requests.get(f"{API_BASE}/health")
        print(f"  Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ Service is healthy")
        else:
            print(f"  ❌ Service is unhealthy: {response.text}")
            return False
        
        # Detailed health check
        response = requests.get(f"{API_BASE}/health/detailed")
        print(f"  Detailed health: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  📊 Status: {data['status']}")
            print(f"  🗄️  Database: {data['components']['database']['status']}")
            print(f"  ⚙️  Worker: {data['components']['worker']['status']}")
        else:
            print(f"  ❌ Detailed health check failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return False

def test_auth():
    """Test authentication"""
    print("\n🔐 Testing authentication...")
    
    try:
        # Test registration
        user_data = {
            "phone": "+79123456789",
            "password": "testpassword123"
        }
        
        response = requests.post(f"{API_BASE}/auth/register", json=user_data)
        print(f"  Registration: {response.status_code}")
        
        if response.status_code == 201:
            print("  ✅ User registered successfully")
            data = response.json()
            token = data['access_token']
        elif response.status_code == 409:
            print("  ℹ️  User already exists, trying login...")
            # Try login instead
            response = requests.post(f"{API_BASE}/auth/login", json=user_data)
            if response.status_code == 200:
                data = response.json()
                token = data['access_token']
                print("  ✅ User logged in successfully")
            else:
                print(f"  ❌ Login failed: {response.text}")
                return False
        else:
            print(f"  ❌ Registration failed: {response.text}")
            return False
        
        # Test protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        print(f"  Protected endpoint: {response.status_code}")
        
        if response.status_code == 200:
            print("  ✅ Authentication working")
            return token
        else:
            print(f"  ❌ Protected endpoint failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Auth test failed: {e}")
        return False

def test_tasks(token):
    """Test tasks functionality"""
    print("\n📋 Testing tasks...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Get tasks
        response = requests.get(f"{API_BASE}/tasks", headers=headers)
        print(f"  Get tasks: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  📊 Found {data['count']} tasks")
        else:
            print(f"  ❌ Get tasks failed: {response.text}")
            return False
        
        # Create a test task
        task_data = {
            "name": "Test Task",
            "warehouse": "Коледино",
            "date_from": "2024-01-01",
            "date_to": "2024-01-31",
            "coefficient": 1.5,
            "packaging": "boxes",
            "auto_book": False
        }
        
        response = requests.post(f"{API_BASE}/tasks", json=task_data, headers=headers)
        print(f"  Create task: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            task_id = data['task']['id']
            print(f"  ✅ Task created with ID: {task_id}")
            
            # Test task actions
            response = requests.post(f"{API_BASE}/tasks/{task_id}/pause", headers=headers)
            print(f"  Pause task: {response.status_code}")
            
            response = requests.post(f"{API_BASE}/tasks/{task_id}/start", headers=headers)
            print(f"  Start task: {response.status_code}")
            
            # Clean up - delete task
            response = requests.delete(f"{API_BASE}/tasks/{task_id}", headers=headers)
            print(f"  Delete task: {response.status_code}")
            
            if response.status_code == 200:
                print("  ✅ Task deleted successfully")
            
            return True
        else:
            print(f"  ❌ Create task failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Tasks test failed: {e}")
        return False

def test_wb_accounts(token):
    """Test WB accounts functionality"""
    print("\n🏢 Testing WB accounts...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Get WB accounts
        response = requests.get(f"{API_BASE}/wb-accounts", headers=headers)
        print(f"  Get WB accounts: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  📊 Found {data['count']} WB accounts")
        else:
            print(f"  ❌ Get WB accounts failed: {response.text}")
            return False
        
        # Create a test WB account
        account_data = {
            "account_name": "Test Account",
            "cookies": ""
        }
        
        response = requests.post(f"{API_BASE}/wb-accounts", json=account_data, headers=headers)
        print(f"  Create WB account: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            account_id = data['account']['id']
            print(f"  ✅ WB account created with ID: {account_id}")
            
            # Clean up - delete account
            response = requests.delete(f"{API_BASE}/wb-accounts/{account_id}", headers=headers)
            print(f"  Delete WB account: {response.status_code}")
            
            if response.status_code == 200:
                print("  ✅ WB account deleted successfully")
            
            return True
        else:
            print(f"  ❌ Create WB account failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ WB accounts test failed: {e}")
        return False

def test_worker(token):
    """Test worker functionality"""
    print("\n⚙️ Testing worker...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Get worker status
        response = requests.get(f"{API_BASE}/worker/status", headers=headers)
        print(f"  Get worker status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  📊 Worker running: {data['running']}")
            print(f"  📊 Active tasks: {data['active_tasks']}")
            print("  ✅ Worker status retrieved")
            return True
        else:
            print(f"  ❌ Get worker status failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Worker test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting"""
    print("\n🚦 Testing rate limiting...")
    
    try:
        # Test auth rate limiting
        user_data = {
            "phone": "+79999999999",
            "password": "wrongpassword"
        }
        
        print("  Testing auth rate limiting...")
        for i in range(6):  # Try 6 times (limit is 5)
            response = requests.post(f"{API_BASE}/auth/login", json=user_data)
            print(f"    Attempt {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                print("  ✅ Rate limiting working")
                return True
        
        print("  ❌ Rate limiting not working")
        return False
        
    except Exception as e:
        print(f"  ❌ Rate limiting test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 WB AutoSlot API Testing")
    print("=" * 50)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not running or not healthy")
            print("Please start the API server first:")
            print("  cd wb-autoslot-api && python src/main.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API")
        print("Please start the API server first:")
        print("  cd wb-autoslot-api && python src/main.py")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Authentication", test_auth),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # If auth worked, test other endpoints
    auth_result = next((result for name, result in results if name == "Authentication"), False)
    if auth_result and isinstance(auth_result, str):  # auth returned token
        token = auth_result
        additional_tests = [
            ("Tasks", lambda: test_tasks(token)),
            ("WB Accounts", lambda: test_wb_accounts(token)),
            ("Worker", lambda: test_worker(token)),
        ]
        
        for test_name, test_func in additional_tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"  ❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
    
    # Print summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
