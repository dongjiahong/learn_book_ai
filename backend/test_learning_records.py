"""
Test script for learning record management functionality
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.models.database import get_db, engine
from app.models.models import User, KnowledgeBase, Document, Question, AnswerRecord, ReviewRecord
from app.models.crud import (
    answer_record_crud, 
    review_record_crud, 
    knowledge_base_crud, 
    document_crud, 
    question_crud
)
from app.schemas.learning import AnswerRecordCreate, ReviewRecordCreate, ContentType


def create_test_data(db: Session):
    """Create test data for learning records"""
    print("Creating test data...")
    
    # Create test user with unique username
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    test_user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        password_hash="hashed_password"
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Create test knowledge base
    kb_data = {
        "user_id": test_user.id,
        "name": "Test Knowledge Base",
        "description": "A test knowledge base for learning records"
    }
    knowledge_base = knowledge_base_crud.create_with_dict(db, obj_in=kb_data)
    
    # Create test document
    doc_data = {
        "knowledge_base_id": knowledge_base.id,
        "filename": "test_document.pdf",
        "file_path": "/test/path/test_document.pdf",
        "file_type": "pdf",
        "file_size": 1024,
        "processed": True
    }
    document = document_crud.create_with_dict(db, obj_in=doc_data)
    
    # Create test questions
    questions = []
    for i in range(3):
        question_data = {
            "document_id": document.id,
            "question_text": f"Test question {i+1}?",
            "context": f"Context for question {i+1}",
            "difficulty_level": (i % 3) + 1
        }
        question = question_crud.create_with_dict(db, obj_in=question_data)
        questions.append(question)
    
    print(f"Created test user (ID: {test_user.id})")
    print(f"Created knowledge base (ID: {knowledge_base.id})")
    print(f"Created document (ID: {document.id})")
    print(f"Created {len(questions)} questions")
    
    return test_user, knowledge_base, document, questions


def test_answer_records(db: Session, user: User, questions: list):
    """Test answer record CRUD operations"""
    print("\n=== Testing Answer Records ===")
    
    # Create answer records
    answer_records = []
    for i, question in enumerate(questions):
        record_data = {
            "user_id": user.id,
            "question_id": question.id,
            "user_answer": f"User answer for question {i+1}",
            "reference_answer": f"Reference answer for question {i+1}",
            "score": 7.5 + i * 0.5,
            "feedback": f"Good answer for question {i+1}",
            "answered_at": datetime.now() - timedelta(days=i)
        }
        record = answer_record_crud.create_with_dict(db, obj_in=record_data)
        answer_records.append(record)
        print(f"Created answer record {record.id} for question {question.id}")
    
    # Test get by user
    user_records = answer_record_crud.get_by_user(db, user.id)
    print(f"Found {len(user_records)} records for user {user.id}")
    
    # Test get with details
    records_with_details = answer_record_crud.get_with_details(db, user.id, limit=10)
    print(f"Found {len(records_with_details)} records with details")
    for record, question_text, filename, kb_name in records_with_details:
        print(f"  Record {record.id}: {question_text[:30]}... in {filename}")
    
    # Test statistics
    stats = answer_record_crud.get_statistics(db, user.id)
    print(f"Statistics: {stats}")
    
    # Test search
    search_results = answer_record_crud.search_records(
        db, user.id, query="question", limit=10
    )
    print(f"Search results: {len(search_results)} records found")
    
    # Test score range filter
    high_score_records = answer_record_crud.get_by_score_range(
        db, user.id, min_score=8.0
    )
    print(f"High score records (>=8.0): {len(high_score_records)}")
    
    return answer_records


def test_review_records(db: Session, user: User, questions: list):
    """Test review record CRUD operations"""
    print("\n=== Testing Review Records ===")
    
    # Create review records
    review_records = []
    for i, question in enumerate(questions):
        record_data = {
            "user_id": user.id,
            "content_id": question.id,
            "content_type": "question",
            "review_count": i,
            "ease_factor": 2.5,
            "interval_days": 1 + i,
            "last_reviewed": datetime.now() - timedelta(days=i+1),
            "next_review": datetime.now() - timedelta(hours=i*2)  # Some due, some not
        }
        record = review_record_crud.create_with_dict(db, obj_in=record_data)
        review_records.append(record)
        print(f"Created review record {record.id} for question {question.id}")
    
    # Test get by user
    user_reviews = review_record_crud.get_by_user(db, user.id)
    print(f"Found {len(user_reviews)} review records for user {user.id}")
    
    # Test get due reviews
    due_reviews = review_record_crud.get_due_reviews(db, user.id)
    print(f"Found {len(due_reviews)} due reviews")
    
    # Test update review schedule
    if review_records:
        test_record = review_records[0]
        print(f"Before update: interval={test_record.interval_days}, ease={test_record.ease_factor}")
        
        updated_record = review_record_crud.update_review_schedule(db, test_record, quality=4)
        print(f"After update: interval={updated_record.interval_days}, ease={updated_record.ease_factor}")
    
    return review_records


def test_bulk_operations(db: Session, user: User, answer_records: list):
    """Test bulk operations"""
    print("\n=== Testing Bulk Operations ===")
    
    if len(answer_records) >= 2:
        # Test bulk delete
        record_ids = [answer_records[0].id, answer_records[1].id]
        deleted_count = answer_record_crud.bulk_delete(db, user.id, record_ids)
        print(f"Bulk deleted {deleted_count} records")
        
        # Verify deletion
        remaining_records = answer_record_crud.get_by_user(db, user.id)
        print(f"Remaining records: {len(remaining_records)}")


def cleanup_test_data(db: Session, user: User):
    """Clean up test data"""
    print("\n=== Cleaning up test data ===")
    
    # Delete user (cascade will handle related records)
    db.delete(user)
    db.commit()
    print("Test data cleaned up")


def main():
    """Main test function"""
    print("Starting learning record management tests...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create test data
        user, knowledge_base, document, questions = create_test_data(db)
        
        # Test answer records
        answer_records = test_answer_records(db, user, questions)
        
        # Test review records
        review_records = test_review_records(db, user, questions)
        
        # Test bulk operations
        test_bulk_operations(db, user, answer_records)
        
        print("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        try:
            cleanup_test_data(db, user)
        except:
            pass
        db.close()


if __name__ == "__main__":
    main()