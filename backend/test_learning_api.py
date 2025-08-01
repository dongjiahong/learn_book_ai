#!/usr/bin/env python3
"""
Test script for learning records API functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal, create_tables
from app.models.models import User, KnowledgeBase, Document, KnowledgePoint, LearningSet, LearningRecord
from app.models.crud import learning_record_crud, learning_set_crud
from app.schemas.learning import MasteryLevel
from datetime import datetime


def setup_test_data(db: Session):
    """Setup test data for learning records"""
    print("Setting up test data...")
    
    # Create test user with unique name
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.flush()
    
    # Create knowledge base
    kb = KnowledgeBase(
        user_id=user.id,
        name="Test Knowledge Base",
        description="Test KB for learning records"
    )
    db.add(kb)
    db.flush()
    
    # Create document
    doc = Document(
        knowledge_base_id=kb.id,
        filename="test.pdf",
        file_path="/test/test.pdf",
        file_type="pdf",
        file_size=1024,
        processed=True
    )
    db.add(doc)
    db.flush()
    
    # Create knowledge points
    kp1 = KnowledgePoint(
        document_id=doc.id,
        title="Python Variables",
        question="How do you define variables in Python?",
        content="In Python, variables are defined by simply assigning a value to a name.",
        importance_level=3
    )
    kp2 = KnowledgePoint(
        document_id=doc.id,
        title="Python Functions",
        question="How do you define functions in Python?",
        content="Functions in Python are defined using the 'def' keyword.",
        importance_level=4
    )
    db.add_all([kp1, kp2])
    db.flush()
    
    # Create learning set
    learning_set = LearningSet(
        user_id=user.id,
        knowledge_base_id=kb.id,
        name="Python Basics",
        description="Basic Python concepts"
    )
    db.add(learning_set)
    db.flush()
    
    db.commit()
    
    return user, kb, doc, [kp1, kp2], learning_set


def test_learning_record_crud(db: Session, user, knowledge_points, learning_set):
    """Test learning record CRUD operations"""
    print("\nTesting Learning Record CRUD operations...")
    
    kp1, kp2 = knowledge_points
    
    # Test get_or_create
    print("1. Testing get_or_create:")
    record1 = learning_record_crud.get_or_create(
        db=db,
        user_id=user.id,
        knowledge_point_id=kp1.id,
        learning_set_id=learning_set.id
    )
    print(f"Created record: ID={record1.id}, mastery_level={record1.mastery_level}")
    
    # Test getting existing record
    record1_again = learning_record_crud.get_or_create(
        db=db,
        user_id=user.id,
        knowledge_point_id=kp1.id,
        learning_set_id=learning_set.id
    )
    print(f"Got existing record: ID={record1_again.id}, same as before: {record1.id == record1_again.id}")
    
    # Test update_mastery
    print("\n2. Testing update_mastery:")
    
    # Update to learning (mastery_level = 1)
    updated_record = learning_record_crud.update_mastery(
        db=db,
        user_id=user.id,
        knowledge_point_id=kp1.id,
        learning_set_id=learning_set.id,
        mastery_level=1
    )
    print(f"Updated to learning: mastery={updated_record.mastery_level}, review_count={updated_record.review_count}")
    print(f"Next review: {updated_record.next_review}")
    print(f"Ease factor: {updated_record.ease_factor}")
    
    # Update to mastered (mastery_level = 2)
    updated_record = learning_record_crud.update_mastery(
        db=db,
        user_id=user.id,
        knowledge_point_id=kp1.id,
        learning_set_id=learning_set.id,
        mastery_level=2
    )
    print(f"Updated to mastered: mastery={updated_record.mastery_level}, review_count={updated_record.review_count}")
    print(f"Next review: {updated_record.next_review}")
    print(f"Ease factor: {updated_record.ease_factor}")
    
    # Create another record for kp2
    record2 = learning_record_crud.get_or_create(
        db=db,
        user_id=user.id,
        knowledge_point_id=kp2.id,
        learning_set_id=learning_set.id
    )
    
    # Test get_due_for_review
    print("\n3. Testing get_due_for_review:")
    due_records = learning_record_crud.get_due_for_review(
        db=db,
        user_id=user.id,
        learning_set_id=learning_set.id
    )
    print(f"Found {len(due_records)} due records")
    for record in due_records:
        print(f"  Record ID={record.id}, mastery={record.mastery_level}, next_review={record.next_review}")
    
    # Test get_statistics
    print("\n4. Testing get_statistics:")
    stats = learning_record_crud.get_statistics(
        db=db,
        user_id=user.id,
        learning_set_id=learning_set.id
    )
    print(f"Statistics: {stats}")
    
    return [record1, record2]


def test_learning_set_due_items(db: Session, user, learning_set):
    """Test learning set due items functionality"""
    print("\n5. Testing learning set due items:")
    
    due_items = learning_set_crud.get_due_items(
        db=db,
        learning_set_id=learning_set.id,
        user_id=user.id
    )
    
    print(f"Found {len(due_items)} due items")
    for knowledge_point, learning_record in due_items:
        mastery = learning_record.mastery_level if learning_record else 0
        next_review = learning_record.next_review if learning_record else "Never"
        print(f"  KP: {knowledge_point.title}, mastery: {mastery}, next_review: {next_review}")


def main():
    """Main test function"""
    print("🧠 Testing Learning Records API Functionality")
    print("=" * 50)
    
    # Create tables
    create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Setup test data
        user, kb, doc, knowledge_points, learning_set = setup_test_data(db)
        
        # Test CRUD operations
        records = test_learning_record_crud(db, user, knowledge_points, learning_set)
        
        # Test learning set functionality
        test_learning_set_due_items(db, user, learning_set)
        
        print("\n✅ All learning record API tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)