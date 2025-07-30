"""
Test script for Anki API endpoints
"""
import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from main import app
from app.models.database import Base, get_db
from app.models.models import User, KnowledgeBase, Document, Question, AnswerRecord, KnowledgePoint
from app.core.auth import auth_manager


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_anki_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def setup_test_data():
    """Set up test data"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db.add(user)
        db.flush()
        
        # Create knowledge base
        kb = KnowledgeBase(
            user_id=user.id,
            name="Test Knowledge Base",
            description="Test description"
        )
        db.add(kb)
        db.flush()
        
        # Create document
        doc = Document(
            knowledge_base_id=kb.id,
            filename="test.pdf",
            file_path="/test/path/test.pdf",
            file_type="pdf",
            file_size=1024,
            processed=True
        )
        db.add(doc)
        db.flush()
        
        # Create questions
        question1 = Question(
            document_id=doc.id,
            question_text="What is the main concept?",
            context="This is the context for the question",
            difficulty_level=2
        )
        question2 = Question(
            document_id=doc.id,
            question_text="How does this work?",
            context="Another context",
            difficulty_level=3
        )
        db.add_all([question1, question2])
        db.flush()
        
        # Create answer records
        answer1 = AnswerRecord(
            user_id=user.id,
            question_id=question1.id,
            user_answer="The main concept is about learning",
            reference_answer="The main concept is about machine learning and AI",
            score=8.5,
            feedback="Good answer, but could be more specific"
        )
        answer2 = AnswerRecord(
            user_id=user.id,
            question_id=question2.id,
            user_answer="It works through algorithms",
            reference_answer="It works through neural networks and deep learning algorithms",
            score=7.0,
            feedback="Correct but needs more detail"
        )
        db.add_all([answer1, answer2])
        db.flush()
        
        # Create knowledge points
        kp1 = KnowledgePoint(
            document_id=doc.id,
            title="Machine Learning Basics",
            content="Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data",
            importance_level=5
        )
        kp2 = KnowledgePoint(
            document_id=doc.id,
            title="Neural Networks",
            content="Neural networks are computing systems inspired by biological neural networks",
            importance_level=4
        )
        db.add_all([kp1, kp2])
        
        db.commit()
        return user, kb
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def test_anki_api():
    """Test Anki API endpoints"""
    print("Setting up test data...")
    user, kb = setup_test_data()
    
    # Create access token
    access_token = auth_manager.create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    client = TestClient(app)
    
    try:
        print("Testing knowledge base export...")
        response = client.post(
            f"/api/anki/export/knowledge-base/{kb.id}",
            headers=headers,
            params={"include_qa": True, "include_kp": True}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        export_data = response.json()
        assert "export_id" in export_data
        assert "deck_name" in export_data
        assert "file_path" in export_data
        
        export_id = export_data["export_id"]
        
        print("Testing export download...")
        download_response = client.get(
            f"/api/anki/download/{export_id}",
            headers=headers
        )
        
        print(f"Download response status: {download_response.status_code}")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"
        
        print("Testing custom export...")
        custom_response = client.post(
            "/api/anki/export/custom",
            headers=headers,
            json={
                "deck_name": "Custom Test Deck",
                "answer_record_ids": [1, 2],
                "knowledge_point_ids": [1, 2]
            }
        )
        
        print(f"Custom export response status: {custom_response.status_code}")
        print(f"Custom export response body: {custom_response.json()}")
        
        assert custom_response.status_code == 200
        
        print("Testing export list...")
        list_response = client.get("/api/anki/exports", headers=headers)
        
        print(f"List response status: {list_response.status_code}")
        print(f"List response body: {list_response.json()}")
        
        assert list_response.status_code == 200
        exports = list_response.json()["exports"]
        assert len(exports) >= 2  # Should have at least 2 exports
        
        print("All API tests passed!")
        
    except Exception as e:
        print(f"API test failed: {e}")
        raise e


def cleanup_test_db():
    """Clean up test database"""
    import os
    if os.path.exists("test_anki_api.db"):
        os.remove("test_anki_api.db")


if __name__ == "__main__":
    try:
        test_anki_api()
        print("✅ Anki API test completed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        cleanup_test_db()