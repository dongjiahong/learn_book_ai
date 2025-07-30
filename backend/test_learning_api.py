"""
Test script for learning record management API endpoints
"""
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8800"

def test_learning_api():
    """Test learning record management API endpoints"""
    print("Testing Learning Record Management API...")
    
    # Test data
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    test_user = {
        "username": f"testuser_api_{unique_id}",
        "email": f"testapi_{unique_id}@example.com",
        "password": "testpassword123"
    }
    
    try:
        # 1. Register user
        print("\n1. Registering test user...")
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if register_response.status_code == 201:
            print("✓ User registered successfully")
        else:
            print(f"✗ User registration failed: {register_response.text}")
            return
        
        # 2. Login
        print("\n2. Logging in...")
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": test_user["username"],
                "password": test_user["password"]
            },
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            tokens = login_response.json()
            access_token = tokens["access_token"]
            print("✓ Login successful")
        else:
            print(f"✗ Login failed: {login_response.text}")
            return
        
        # Headers for authenticated requests
        auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 3. Test learning statistics endpoint
        print("\n3. Testing learning statistics...")
        stats_response = requests.get(
            f"{BASE_URL}/api/learning/statistics",
            headers=auth_headers
        )
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"✓ Statistics retrieved: {stats}")
        else:
            print(f"✗ Statistics failed: {stats_response.text}")
        
        # 4. Test learning progress endpoint
        print("\n4. Testing learning progress...")
        progress_response = requests.get(
            f"{BASE_URL}/api/learning/progress",
            headers=auth_headers
        )
        
        if progress_response.status_code == 200:
            progress = progress_response.json()
            print(f"✓ Progress retrieved: User ID {progress['user_id']}")
            print(f"  - Total questions answered: {progress['statistics']['total_questions_answered']}")
            print(f"  - Average score: {progress['statistics']['average_score']}")
            print(f"  - Due reviews: {len(progress['due_reviews'])}")
            print(f"  - Recent records: {len(progress['recent_records'])}")
        else:
            print(f"✗ Progress failed: {progress_response.text}")
        
        # 5. Test answer records endpoint
        print("\n5. Testing answer records...")
        records_response = requests.get(
            f"{BASE_URL}/api/learning/answer-records",
            headers=auth_headers
        )
        
        if records_response.status_code == 200:
            records = records_response.json()
            print(f"✓ Answer records retrieved: {len(records)} records")
        else:
            print(f"✗ Answer records failed: {records_response.text}")
        
        # 6. Test review records endpoint
        print("\n6. Testing review records...")
        review_response = requests.get(
            f"{BASE_URL}/api/learning/review-records",
            headers=auth_headers
        )
        
        if review_response.status_code == 200:
            reviews = review_response.json()
            print(f"✓ Review records retrieved: {len(reviews)} records")
        else:
            print(f"✗ Review records failed: {review_response.text}")
        
        # 7. Test due reviews endpoint
        print("\n7. Testing due reviews...")
        due_response = requests.get(
            f"{BASE_URL}/api/learning/review-records/due",
            headers=auth_headers
        )
        
        if due_response.status_code == 200:
            due_reviews = due_response.json()
            print(f"✓ Due reviews retrieved: {len(due_reviews)} records")
        else:
            print(f"✗ Due reviews failed: {due_response.text}")
        
        print("\n✓ All learning API tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("✗ Connection error: Make sure the backend server is running on localhost:8000")
    except Exception as e:
        print(f"✗ Test failed with error: {e}")

if __name__ == "__main__":
    test_learning_api()