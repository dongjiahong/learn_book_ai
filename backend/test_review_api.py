"""
Test review API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.models.database import get_db, engine
from app.models.models import Base, User, Question, KnowledgeBase, Document
from app.core.auth import auth_manager


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user_and_token(db_session):
    """Create test user and auth token"""
    user = User(
        username="testuser_review",
        email="test_review@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    token = auth_manager.create_access_token(data={"sub": str(user.id)})
    return user, token


@pytest.fixture
def test_question(db_session, test_user_and_token):
    """Create test question"""
    user, _ = test_user_and_token
    
    # Create knowledge base and document
    kb = KnowledgeBase(
        user_id=user.id,
        name="Test KB",
        description="Test knowledge base"
    )
    db_session.add(kb)
    db_session.commit()
    
    doc = Document(
        knowledge_base_id=kb.id,
        filename="test.txt",
        file_path="/test/test.txt",
        file_type="txt",
        file_size=1000,
        processed=True
    )
    db_session.add(doc)
    db_session.commit()
    
    question = Question(
        document_id=doc.id,
        question_text="What is the capital of France?",
        context="Geography question about France",
        difficulty_level=1
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


def test_get_due_reviews_empty(client, test_user_and_token):
    """Test getting due reviews when none exist"""
    user, token = test_user_and_token
    
    response = client.get(
        "/api/review/due",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_schedule_item_for_review(client, test_user_and_token, test_question):
    """Test scheduling an item for review"""
    user, token = test_user_and_token
    
    response = client.post(
        "/api/review/schedule",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content_id": test_question.id,
            "content_type": "question"
        }
    )
    
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "review_record_id" in data
    assert "next_review" in data


def test_get_review_statistics(client, test_user_and_token):
    """Test getting review statistics"""
    user, token = test_user_and_token
    
    response = client.get(
        "/api/review/statistics",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_items" in data
    assert "due_today" in data
    assert "due_this_week" in data
    assert "completed_today" in data
    assert "average_ease_factor" in data
    assert "learning_streak" in data


def test_complete_review(client, test_user_and_token, test_question):
    """Test completing a review"""
    user, token = test_user_and_token
    
    # First schedule the item
    schedule_response = client.post(
        "/api/review/schedule",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content_id": test_question.id,
            "content_type": "question"
        }
    )
    assert schedule_response.status_code == 200
    
    # Then complete the review
    response = client.post(
        "/api/review/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content_id": test_question.id,
            "content_type": "question",
            "quality": 4
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "next_review" in data
    assert "interval_days" in data
    assert "ease_factor" in data


def test_get_upcoming_reviews(client, test_user_and_token):
    """Test getting upcoming reviews"""
    user, token = test_user_and_token
    
    response = client.get(
        "/api/review/upcoming?days=7",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_daily_summary(client, test_user_and_token):
    """Test getting daily summary"""
    user, token = test_user_and_token
    
    response = client.get(
        "/api/review/daily-summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "date" in data
    assert "completed_today" in data
    assert "due_today" in data
    assert "completion_rate" in data


def test_get_weekly_summary(client, test_user_and_token):
    """Test getting weekly summary"""
    user, token = test_user_and_token
    
    response = client.get(
        "/api/review/weekly-summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "week_start" in data
    assert "total_completed" in data
    assert "daily_breakdown" in data
    assert "average_per_day" in data


def test_invalid_quality_rating(client, test_user_and_token, test_question):
    """Test completing review with invalid quality rating"""
    user, token = test_user_and_token
    
    response = client.post(
        "/api/review/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content_id": test_question.id,
            "content_type": "question",
            "quality": 6  # Invalid - should be 0-5
        }
    )
    
    assert response.status_code == 400


def test_invalid_content_type(client, test_user_and_token, test_question):
    """Test scheduling with invalid content type"""
    user, token = test_user_and_token
    
    response = client.post(
        "/api/review/schedule",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content_id": test_question.id,
            "content_type": "invalid_type"
        }
    )
    
    assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])