"""
Test spaced repetition service and API endpoints
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.database import get_db, engine
from app.models.models import Base, User, Question, KnowledgePoint, ReviewRecord, Document, KnowledgeBase
from app.services.spaced_repetition_service import SpacedRepetitionService
from app.services.notification_service import NotificationService


@pytest.fixture
def db_session():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_question(db_session, test_user):
    """Create a test question"""
    # Create knowledge base and document first
    kb = KnowledgeBase(
        user_id=test_user.id,
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


def test_calculate_next_review():
    """Test the SM-2 algorithm implementation"""
    service = SpacedRepetitionService(None)
    
    # Test successful recall (quality >= 3)
    ease_factor, interval = service.calculate_next_review(2.5, 1, 4)
    assert interval == 6  # First successful review should be 6 days
    assert ease_factor >= 2.5  # Ease factor should be maintained or increased for good recall
    
    # Test failed recall (quality < 3)
    ease_factor, interval = service.calculate_next_review(2.5, 16, 2)
    assert interval == 1  # Failed recall resets to 1 day
    assert ease_factor == 2.5  # Ease factor unchanged for failed recall
    
    # Test second successful review
    ease_factor, interval = service.calculate_next_review(2.5, 6, 4)
    assert interval == 16  # Second successful review should be 16 days
    
    # Test subsequent reviews
    ease_factor, interval = service.calculate_next_review(2.5, 16, 4)
    assert interval == int(16 * 2.5)  # Should multiply by ease factor


def test_create_review_record(db_session, test_user, test_question):
    """Test creating a new review record"""
    service = SpacedRepetitionService(db_session)
    
    # Create new review record
    record = service.get_or_create_review_record(
        test_user.id, 
        test_question.id, 
        'question'
    )
    
    assert record.user_id == test_user.id
    assert record.content_id == test_question.id
    assert record.content_type == 'question'
    assert record.review_count == 0
    assert record.ease_factor == 2.5
    assert record.interval_days == 1
    assert record.next_review is not None


def test_update_review_record(db_session, test_user, test_question):
    """Test updating a review record after review"""
    service = SpacedRepetitionService(db_session)
    
    # Create initial record
    initial_record = service.get_or_create_review_record(
        test_user.id, 
        test_question.id, 
        'question'
    )
    
    # Update with successful review
    updated_record = service.update_review_record(
        test_user.id,
        test_question.id,
        'question',
        4  # Good quality
    )
    
    assert updated_record.review_count == 1
    assert updated_record.interval_days == 6  # First successful review
    assert updated_record.last_reviewed is not None
    assert updated_record.next_review > datetime.utcnow()


def test_get_due_reviews(db_session, test_user, test_question):
    """Test getting due reviews"""
    service = SpacedRepetitionService(db_session)
    
    # Create a review record that's due
    record = service.get_or_create_review_record(
        test_user.id, 
        test_question.id, 
        'question'
    )
    
    # Make it due by setting next_review to past
    record.next_review = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()
    
    # Get due reviews
    due_reviews = service.get_due_reviews(test_user.id)
    
    assert len(due_reviews) == 1
    assert due_reviews[0]['content_id'] == test_question.id
    assert due_reviews[0]['content_type'] == 'question'
    assert 'question_text' in due_reviews[0]


def test_get_review_statistics(db_session, test_user, test_question):
    """Test getting review statistics"""
    service = SpacedRepetitionService(db_session)
    
    # Create some review records
    service.get_or_create_review_record(test_user.id, test_question.id, 'question')
    
    # Get statistics
    stats = service.get_review_statistics(test_user.id)
    
    assert 'total_items' in stats
    assert 'due_today' in stats
    assert 'due_this_week' in stats
    assert 'completed_today' in stats
    assert 'average_ease_factor' in stats
    
    assert stats['total_items'] >= 1


def test_learning_streak(db_session, test_user, test_question):
    """Test learning streak calculation"""
    service = SpacedRepetitionService(db_session)
    
    # Create and update a review record
    record = service.update_review_record(
        test_user.id,
        test_question.id,
        'question',
        4
    )
    
    # Get learning streak
    streak = service.get_learning_streak(test_user.id)
    
    assert streak >= 1  # Should have at least 1 day streak


def test_notification_service(db_session, test_user, test_question):
    """Test notification service functionality"""
    notification_service = NotificationService(db_session)
    spaced_service = SpacedRepetitionService(db_session)
    
    # Create an overdue review
    record = spaced_service.get_or_create_review_record(
        test_user.id, 
        test_question.id, 
        'question'
    )
    record.next_review = datetime.utcnow() - timedelta(hours=2)
    db_session.commit()
    
    # Get reminders
    reminders = notification_service.get_due_reminders(test_user.id)
    
    assert len(reminders) >= 1
    overdue_reminder = next((r for r in reminders if r['type'] == 'overdue'), None)
    assert overdue_reminder is not None
    assert overdue_reminder['priority'] == 'high'


def test_daily_summary(db_session, test_user, test_question):
    """Test daily summary functionality"""
    notification_service = NotificationService(db_session)
    spaced_service = SpacedRepetitionService(db_session)
    
    # Complete a review today
    spaced_service.update_review_record(
        test_user.id,
        test_question.id,
        'question',
        4
    )
    
    # Get daily summary
    summary = notification_service.get_daily_summary(test_user.id)
    
    assert 'date' in summary
    assert 'completed_today' in summary
    assert 'due_today' in summary
    assert 'completion_rate' in summary
    
    assert summary['completed_today'] >= 1


def test_achievement_notifications(db_session, test_user):
    """Test achievement notification creation"""
    notification_service = NotificationService(db_session)
    
    # Test first review achievement
    achievement = notification_service.create_achievement_notification(
        test_user.id,
        'first_review',
        {}
    )
    
    assert achievement['type'] == 'achievement'
    assert achievement['achievement_type'] == 'first_review'
    assert '🎉' in achievement['title']
    
    # Test streak milestone
    streak_achievement = notification_service.create_achievement_notification(
        test_user.id,
        'streak_milestone',
        {'streak': 7}
    )
    
    assert '7 Day Streak' in streak_achievement['title']
    assert '🔥' in streak_achievement['title']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])