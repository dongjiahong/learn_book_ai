#!/usr/bin/env python3
"""
Simple test script to verify authentication API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_register():
    """Test user registration"""
    print("Testing user registration...")
    
    data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    print(f"Register response: {response.status_code}")
    
    if response.status_code == 201:
        user_data = response.json()
        print(f"User created: {user_data['username']} ({user_data['email']})")
        return True
    else:
        print(f"Registration failed: {response.text}")
        return False

def test_login():
    """Test user login"""
    print("\nTesting user login...")
    
    data = {
        "username": "testuser2",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
    print(f"Login response: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print("Login successful!")
        print(f"Access token: {token_data['access_token'][:50]}...")
        return token_data['access_token']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_protected_endpoint(token):
    """Test accessing protected endpoint"""
    print("\nTesting protected endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"Protected endpoint response: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"Current user: {user_data['username']} ({user_data['email']})")
        return True
    else:
        print(f"Protected endpoint failed: {response.text}")
        return False

def main():
    print("=== Authentication API Test ===")
    
    # Test registration
    if test_register():
        # Test login
        token = test_login()
        if token:
            # Test protected endpoint
            test_protected_endpoint(token)
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()