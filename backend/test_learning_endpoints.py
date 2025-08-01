#!/usr/bin/env python3
"""
Test script for learning records API endpoints
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8800"
API_BASE = f"{BASE_URL}/api"


def test_auth():
    """Test authentication and get token"""
    print("Testing authentication...")
    
    # Try to register a new user
    register_data = {
        "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=register_data)
        if response.status_code in [200, 201]:
            print("✅ User registered successfully")
        else:
            print(f"Registration failed: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please make sure the backend is running on port 8800")
        return None
    
    # Login to get token
    login_data = {
        "username": register_data["username"],
        "password": register_data["password"]
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print("✅ Login successful")
            return token
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None


def test_learning_endpoints(token):
    """Test learning record endpoints"""
    if not token:
        print("❌ No token available, skipping API tests")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nTesting learning record endpoints...")
    
    # Test get learning statistics
    print("1. Testing GET /api/learning/learning-statistics")
    try:
        response = requests.get(f"{API_BASE}/learning/learning-statistics", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"Statistics: {json.dumps(stats, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test get all due reviews
    print("\n2. Testing GET /api/learning/learning-records/due")
    try:
        response = requests.get(f"{API_BASE}/learning/learning-records/due", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            due_reviews = response.json()
            print(f"Due reviews count: {len(due_reviews)}")
            if due_reviews:
                print(f"First due review: {json.dumps(due_reviews[0], indent=2, default=str)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test get learning sets (to get a learning set ID for further testing)
    print("\n3. Testing GET /api/learning-sets")
    try:
        response = requests.get(f"{API_BASE}/learning-sets", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            learning_sets = response.json()
            print(f"Learning sets count: {len(learning_sets)}")
            if learning_sets:
                learning_set_id = learning_sets[0]["id"]
                print(f"Using learning set ID: {learning_set_id}")
                
                # Test get due reviews for specific learning set
                print(f"\n4. Testing GET /api/learning/learning-sets/{learning_set_id}/due-reviews")
                response = requests.get(f"{API_BASE}/learning/learning-sets/{learning_set_id}/due-reviews", headers=headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    due_items = response.json()
                    print(f"Due items count: {len(due_items)}")
                    if due_items:
                        print(f"First due item: {json.dumps(due_items[0], indent=2, default=str)}")
                else:
                    print(f"Error: {response.text}")
                
                # Test get next review item
                print(f"\n5. Testing GET /api/learning/learning-sets/{learning_set_id}/next-review")
                response = requests.get(f"{API_BASE}/learning/learning-sets/{learning_set_id}/next-review", headers=headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    next_item = response.json()
                    print(f"Next review item: {json.dumps(next_item, indent=2, default=str)}")
                else:
                    print(f"Error: {response.text}")
                
                # Test learning statistics for specific learning set
                print(f"\n6. Testing GET /api/learning/learning-statistics?learning_set_id={learning_set_id}")
                response = requests.get(f"{API_BASE}/learning/learning-statistics?learning_set_id={learning_set_id}", headers=headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    stats = response.json()
                    print(f"Learning set statistics: {json.dumps(stats, indent=2)}")
                else:
                    print(f"Error: {response.text}")
            else:
                print("No learning sets found")
        else:
            print(f"Error getting learning sets: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main test function"""
    print("🧠 Testing Learning Records API Endpoints")
    print("=" * 50)
    
    # Test authentication
    token = test_auth()
    
    # Test learning endpoints
    test_learning_endpoints(token)
    
    print("\n✅ API endpoint tests completed!")


if __name__ == "__main__":
    main()