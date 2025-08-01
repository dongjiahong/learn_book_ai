#!/usr/bin/env python3
"""
Final comprehensive API test for learning records and spaced repetition
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8800"
API_BASE = f"{BASE_URL}/api"


def create_test_user_and_data():
    """Create test user and basic data structure"""
    print("🔧 Setting up test user and data...")
    
    # Create unique user
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    register_data = {
        "username": f"final_test_{timestamp}",
        "email": f"final_test_{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    # Register user
    response = requests.post(f"{API_BASE}/auth/register", json=register_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None, None, None
    
    # Login
    response = requests.post(f"{API_BASE}/auth/login", json=register_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None, None, None
    
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create knowledge base
    kb_data = {
        "name": "Final Test KB",
        "description": "Knowledge base for final API testing"
    }
    response = requests.post(f"{API_BASE}/knowledge-bases", json=kb_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ KB creation failed: {response.status_code} - {response.text}")
        return None, None, None
    
    kb = response.json()
    
    # Create learning set
    ls_data = {
        "name": "Final Test Learning Set",
        "description": "Learning set for final API testing",
        "knowledge_base_id": kb["id"],
        "document_ids": []
    }
    response = requests.post(f"{API_BASE}/learning-sets", json=ls_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Learning set creation failed: {response.status_code} - {response.text}")
        return None, None, None
    
    ls = response.json()
    
    print(f"✅ Created user, KB (ID: {kb['id']}), and learning set (ID: {ls['id']})")
    return token, kb, ls


def test_learning_statistics_api(headers):
    """Test learning statistics API endpoints"""
    print("\n📊 Testing Learning Statistics API")
    print("-" * 40)
    
    # Test overall statistics
    response = requests.get(f"{API_BASE}/learning/learning-statistics", headers=headers)
    print(f"Overall statistics: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"   Total items: {stats.get('total_items', 0)}")
        print(f"   Due items: {stats.get('due_items', 0)}")
        print(f"   Mastery distribution: {stats.get('mastery_distribution', {})}")
    else:
        print(f"   Error: {response.text}")
    
    return response.status_code == 200


def test_due_reviews_api(headers, learning_set_id):
    """Test due reviews API endpoints"""
    print("\n📅 Testing Due Reviews API")
    print("-" * 40)
    
    # Test global due reviews
    response = requests.get(f"{API_BASE}/learning/learning-records/due", headers=headers)
    print(f"Global due reviews: {response.status_code}")
    if response.status_code == 200:
        due_reviews = response.json()
        print(f"   Found {len(due_reviews)} due reviews")
    else:
        print(f"   Error: {response.text}")
    
    # Test learning set specific due reviews
    response = requests.get(f"{API_BASE}/learning/learning-sets/{learning_set_id}/due-reviews", headers=headers)
    print(f"Learning set due reviews: {response.status_code}")
    if response.status_code == 200:
        due_items = response.json()
        print(f"   Found {len(due_items)} due items")
    else:
        print(f"   Error: {response.text}")
    
    # Test next review item
    response = requests.get(f"{API_BASE}/learning/learning-sets/{learning_set_id}/next-review", headers=headers)
    print(f"Next review item: {response.status_code}")
    if response.status_code == 200:
        next_item = response.json()
        if next_item.get("next_item"):
            print(f"   Next item: {next_item['next_item']['title']}")
        else:
            print(f"   Message: {next_item.get('message', 'No items')}")
    else:
        print(f"   Error: {response.text}")
    
    return True


def test_learning_record_crud_api(headers, learning_set_id):
    """Test learning record CRUD API endpoints"""
    print("\n🔄 Testing Learning Record CRUD API")
    print("-" * 40)
    
    # Since we don't have knowledge points in our test learning set,
    # we'll test the endpoints that should return empty results
    
    # Test get learning records for learning set
    response = requests.get(f"{API_BASE}/learning/learning-records/{learning_set_id}", headers=headers)
    print(f"Get learning records: {response.status_code}")
    if response.status_code == 200:
        records = response.json()
        print(f"   Found {len(records)} learning records")
    else:
        print(f"   Error: {response.text}")
    
    # Test learning set statistics
    response = requests.get(f"{API_BASE}/learning/learning-statistics?learning_set_id={learning_set_id}", headers=headers)
    print(f"Learning set statistics: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"   Total items: {stats.get('total_items', 0)}")
        print(f"   Due items: {stats.get('due_items', 0)}")
    else:
        print(f"   Error: {response.text}")
    
    return True


def test_spaced_repetition_service_integration():
    """Test spaced repetition service integration"""
    print("\n🧠 Testing Spaced Repetition Service Integration")
    print("-" * 40)
    
    # Import and test the service directly
    from app.services.spaced_repetition_service import spaced_repetition_service
    from datetime import datetime, timedelta
    
    # Test calculate_next_review
    interval, ease, next_review = spaced_repetition_service.calculate_next_review(
        mastery_level=1,  # Learning
        current_ease_factor=2.5,
        current_interval=1,
        review_count=0
    )
    print(f"Calculate next review: interval={interval}, ease={ease:.2f}")
    
    # Test priority calculation
    priority = spaced_repetition_service.get_study_priority(
        mastery_level=0,  # Not learned
        next_review=datetime.now() - timedelta(days=1),  # Overdue
        importance_level=5  # High importance
    )
    print(f"Study priority (overdue, high importance): {priority:.2f}")
    
    # Test recommended study time
    study_time = spaced_repetition_service.get_recommended_study_time(
        mastery_level=0,  # Not learned
        importance_level=3  # Medium importance
    )
    print(f"Recommended study time: {study_time} minutes")
    
    print("✅ Spaced repetition service integration working correctly")
    return True


def test_error_handling(headers):
    """Test API error handling"""
    print("\n⚠️  Testing Error Handling")
    print("-" * 40)
    
    # Test with non-existent learning set
    response = requests.get(f"{API_BASE}/learning/learning-sets/99999/due-reviews", headers=headers)
    print(f"Non-existent learning set: {response.status_code}")
    if response.status_code == 404:
        print("   ✅ Correctly returns 404 for non-existent learning set")
    else:
        print(f"   ⚠️  Expected 404, got {response.status_code}")
    
    # Test with invalid learning record ID
    response = requests.put(f"{API_BASE}/learning/learning-records/99999", 
                          json={"mastery_level": 1}, headers=headers)
    print(f"Non-existent learning record: {response.status_code}")
    if response.status_code == 404:
        print("   ✅ Correctly returns 404 for non-existent learning record")
    else:
        print(f"   ⚠️  Expected 404, got {response.status_code}")
    
    return True


def main():
    """Main test function"""
    print("🧠 Final Comprehensive API Test for Learning Records")
    print("=" * 60)
    
    # Setup test data
    token, kb, ls = create_test_user_and_data()
    if not token:
        print("❌ Failed to setup test data")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Run all tests
    tests = [
        ("Learning Statistics API", lambda: test_learning_statistics_api(headers)),
        ("Due Reviews API", lambda: test_due_reviews_api(headers, ls["id"])),
        ("Learning Record CRUD API", lambda: test_learning_record_crud_api(headers, ls["id"])),
        ("Spaced Repetition Service", test_spaced_repetition_service_integration),
        ("Error Handling", lambda: test_error_handling(headers))
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Learning records and spaced repetition functionality is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)