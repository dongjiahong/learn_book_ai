#!/usr/bin/env python3
"""
Setup test data for learning records testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8800"
API_BASE = f"{BASE_URL}/api"


def create_test_user():
    """Create a test user and return token"""
    print("Creating test user...")
    
    # Register user
    register_data = {
        "username": "learning_test_user",
        "email": "learning_test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=register_data)
        if response.status_code in [200, 201]:
            print("✅ User registered successfully")
        elif response.status_code == 400 and "already exists" in response.text:
            print("✅ User already exists")
        else:
            print(f"Registration failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Registration error: {e}")
        return None
    
    # Login
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


def create_knowledge_base(token):
    """Create a knowledge base"""
    headers = {"Authorization": f"Bearer {token}"}
    
    kb_data = {
        "name": "Learning Test KB",
        "description": "Knowledge base for testing learning records"
    }
    
    try:
        response = requests.post(f"{API_BASE}/knowledge-bases", json=kb_data, headers=headers)
        if response.status_code in [200, 201]:
            kb = response.json()
            print(f"✅ Knowledge base created: {kb['name']} (ID: {kb['id']})")
            return kb
        else:
            print(f"KB creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"KB creation error: {e}")
        return None


def create_learning_set(token, kb_id):
    """Create a learning set"""
    headers = {"Authorization": f"Bearer {token}"}
    
    ls_data = {
        "name": "Python Basics Learning Set",
        "description": "Basic Python concepts for learning",
        "knowledge_base_id": kb_id,
        "document_ids": []  # Empty for now
    }
    
    try:
        response = requests.post(f"{API_BASE}/learning-sets", json=ls_data, headers=headers)
        if response.status_code in [200, 201]:
            ls = response.json()
            print(f"✅ Learning set created: {ls['name']} (ID: {ls['id']})")
            return ls
        else:
            print(f"Learning set creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Learning set creation error: {e}")
        return None


def test_learning_record_creation(token, learning_set_id):
    """Test creating learning records"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\nTesting learning record creation for learning set {learning_set_id}...")
    
    # First, let's see if there are any knowledge points in the learning set
    try:
        response = requests.get(f"{API_BASE}/learning-sets/{learning_set_id}/items", headers=headers)
        if response.status_code == 200:
            items = response.json()
            print(f"Learning set has {len(items)} items")
            
            if items:
                # Test creating a learning record for the first knowledge point
                kp_id = items[0]["knowledge_point_id"]
                
                record_data = {
                    "knowledge_point_id": kp_id,
                    "learning_set_id": learning_set_id
                }
                
                response = requests.post(f"{API_BASE}/learning/learning-records", json=record_data, headers=headers)
                if response.status_code in [200, 201]:
                    record = response.json()
                    print(f"✅ Learning record created: ID={record['id']}, mastery_level={record['mastery_level']}")
                    
                    # Test answering (updating mastery)
                    answer_data = {
                        "knowledge_point_id": kp_id,
                        "learning_set_id": learning_set_id,
                        "mastery_level": 1  # Learning
                    }
                    
                    response = requests.post(f"{API_BASE}/learning/learning-records/answer", json=answer_data, headers=headers)
                    if response.status_code == 200:
                        updated_record = response.json()
                        print(f"✅ Learning record updated: mastery_level={updated_record['mastery_level']}, review_count={updated_record['review_count']}")
                    else:
                        print(f"Answer recording failed: {response.status_code} - {response.text}")
                else:
                    print(f"Learning record creation failed: {response.status_code} - {response.text}")
            else:
                print("No knowledge points found in learning set")
        else:
            print(f"Failed to get learning set items: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error testing learning records: {e}")


def main():
    """Main setup function"""
    print("🧠 Setting up test data for learning records")
    print("=" * 50)
    
    # Create user and get token
    token = create_test_user()
    if not token:
        print("❌ Failed to create user or get token")
        return
    
    # Create knowledge base
    kb = create_knowledge_base(token)
    if not kb:
        print("❌ Failed to create knowledge base")
        return
    
    # Create learning set
    ls = create_learning_set(token, kb["id"])
    if not ls:
        print("❌ Failed to create learning set")
        return
    
    # Test learning record functionality
    test_learning_record_creation(token, ls["id"])
    
    print("\n✅ Test data setup completed!")
    print(f"Knowledge Base ID: {kb['id']}")
    print(f"Learning Set ID: {ls['id']}")


if __name__ == "__main__":
    main()