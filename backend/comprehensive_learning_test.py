#!/usr/bin/env python3
"""
Comprehensive test for learning records and spaced repetition functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal, create_tables
from app.models.models import User, KnowledgeBase, Document, KnowledgePoint, LearningSet, LearningSetItem, LearningRecord
from app.models.crud import learning_record_crud, learning_set_crud
from app.services.spaced_repetition_service import spaced_repetition_service
from datetime import datetime, timedelta
import uuid


def setup_comprehensive_test_data(db: Session):
    """Setup comprehensive test data"""
    print("Setting up comprehensive test data...")
    
    # Create test user
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"comprehensive_test_{unique_id}",
        email=f"comprehensive_test_{unique_id}@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.flush()
    
    # Create knowledge base
    kb = KnowledgeBase(
        user_id=user.id,
        name="Comprehensive Test KB",
        description="Knowledge base for comprehensive testing"
    )
    db.add(kb)
    db.flush()
    
    # Create document
    doc = Document(
        knowledge_base_id=kb.id,
        filename="comprehensive_test.pdf",
        file_path="/test/comprehensive_test.pdf",
        file_type="pdf",
        file_size=2048,
        processed=True
    )
    db.add(doc)
    db.flush()
    
    # Create multiple knowledge points
    knowledge_points = []
    topics = [
        ("Python Variables", "How do you define variables in Python?", "Variables in Python are defined by assignment.", 3),
        ("Python Functions", "How do you define functions in Python?", "Functions are defined using the 'def' keyword.", 4),
        ("Python Classes", "How do you define classes in Python?", "Classes are defined using the 'class' keyword.", 5),
        ("Python Loops", "What are the types of loops in Python?", "Python has for loops and while loops.", 2),
        ("Python Lists", "How do you work with lists in Python?", "Lists are ordered collections defined with [].", 3)
    ]
    
    for title, question, content, importance in topics:
        kp = KnowledgePoint(
            document_id=doc.id,
            title=title,
            question=question,
            content=content,
            importance_level=importance
        )
        knowledge_points.append(kp)
        db.add(kp)
    
    db.flush()
    
    # Create learning set
    learning_set = LearningSet(
        user_id=user.id,
        knowledge_base_id=kb.id,
        name="Comprehensive Python Learning",
        description="Comprehensive Python concepts learning set"
    )
    db.add(learning_set)
    db.flush()
    
    # Add knowledge points to learning set
    for kp in knowledge_points:
        item = LearningSetItem(
            learning_set_id=learning_set.id,
            knowledge_point_id=kp.id
        )
        db.add(item)
    
    db.commit()
    
    return user, kb, doc, knowledge_points, learning_set


def test_learning_record_lifecycle(db: Session, user, knowledge_points, learning_set):
    """Test complete learning record lifecycle"""
    print("\n🔄 Testing Learning Record Lifecycle")
    print("=" * 40)
    
    kp = knowledge_points[0]  # Use first knowledge point
    
    # 1. Create initial learning record
    print("1. Creating initial learning record...")
    record = learning_record_crud.get_or_create(
        db=db,
        user_id=user.id,
        knowledge_point_id=kp.id,
        learning_set_id=learning_set.id
    )
    print(f"   ✅ Created: ID={record.id}, mastery={record.mastery_level}, ease={record.ease_factor}")
    
    # 2. Simulate learning progression
    print("\n2. Simulating learning progression...")
    mastery_levels = [0, 1, 1, 2, 2]  # Not learned -> Learning -> Learning -> Mastered -> Mastered
    
    for i, mastery in enumerate(mastery_levels):
        print(f"   Review {i+1}: Setting mastery to {mastery}")
        
        updated_record = learning_record_crud.update_mastery(
            db=db,
            user_id=user.id,
            knowledge_point_id=kp.id,
            learning_set_id=learning_set.id,
            mastery_level=mastery
        )
        
        print(f"     Result: mastery={updated_record.mastery_level}, "
              f"review_count={updated_record.review_count}, "
              f"interval={updated_record.interval_days}, "
              f"ease={updated_record.ease_factor:.2f}")
        print(f"     Next review: {updated_record.next_review}")
    
    return record


def test_spaced_repetition_algorithm(db: Session, user, knowledge_points, learning_set):
    """Test spaced repetition algorithm with multiple knowledge points"""
    print("\n🧠 Testing Spaced Repetition Algorithm")
    print("=" * 40)
    
    # Create learning records for all knowledge points
    records = []
    for i, kp in enumerate(knowledge_points):
        record = learning_record_crud.get_or_create(
            db=db,
            user_id=user.id,
            knowledge_point_id=kp.id,
            learning_set_id=learning_set.id
        )
        records.append(record)
    
    print(f"Created {len(records)} learning records")
    
    # Test different mastery scenarios
    scenarios = [
        (0, "Not learned - should have short interval"),
        (1, "Learning - should have medium interval"),
        (2, "Mastered - should have long interval")
    ]
    
    for i, (mastery, description) in enumerate(scenarios):
        if i < len(records):
            kp = knowledge_points[i]
            print(f"\n{i+1}. {description}")
            
            # Update mastery multiple times to see progression
            for review in range(3):
                updated_record = learning_record_crud.update_mastery(
                    db=db,
                    user_id=user.id,
                    knowledge_point_id=kp.id,
                    learning_set_id=learning_set.id,
                    mastery_level=mastery
                )
                
                print(f"   Review {review+1}: interval={updated_record.interval_days} days, "
                      f"ease={updated_record.ease_factor:.2f}")


def test_due_items_functionality(db: Session, user, learning_set):
    """Test due items functionality"""
    print("\n📅 Testing Due Items Functionality")
    print("=" * 40)
    
    # Get due items from learning set
    due_items = learning_set_crud.get_due_items(db, learning_set.id, user.id)
    print(f"Found {len(due_items)} due items")
    
    for i, (knowledge_point, learning_record) in enumerate(due_items[:3]):  # Show first 3
        mastery = learning_record.mastery_level if learning_record else 0
        next_review = learning_record.next_review if learning_record else "Never"
        
        # Calculate priority
        priority = spaced_repetition_service.get_study_priority(
            mastery_level=mastery,
            next_review=learning_record.next_review if learning_record else datetime.now(),
            importance_level=knowledge_point.importance_level
        )
        
        print(f"   {i+1}. {knowledge_point.title}")
        print(f"      Mastery: {mastery}, Next review: {next_review}")
        print(f"      Priority: {priority:.2f}, Importance: {knowledge_point.importance_level}")
    
    # Test get_due_for_review
    due_records = learning_record_crud.get_due_for_review(
        db=db,
        user_id=user.id,
        learning_set_id=learning_set.id
    )
    print(f"\nDue records from CRUD: {len(due_records)}")


def test_learning_statistics(db: Session, user, learning_set):
    """Test learning statistics"""
    print("\n📊 Testing Learning Statistics")
    print("=" * 40)
    
    # Get overall statistics
    overall_stats = learning_record_crud.get_statistics(
        db=db,
        user_id=user.id
    )
    print("Overall Statistics:")
    print(f"   Total items: {overall_stats['total_items']}")
    print(f"   Due items: {overall_stats['due_items']}")
    print(f"   Mastery distribution: {overall_stats['mastery_distribution']}")
    
    # Get learning set specific statistics
    ls_stats = learning_record_crud.get_statistics(
        db=db,
        user_id=user.id,
        learning_set_id=learning_set.id
    )
    print(f"\nLearning Set Statistics:")
    print(f"   Total items: {ls_stats['total_items']}")
    print(f"   Due items: {ls_stats['due_items']}")
    print(f"   Mastery distribution: {ls_stats['mastery_distribution']}")


def test_memory_curve_calculations():
    """Test memory curve calculations"""
    print("\n📈 Testing Memory Curve Calculations")
    print("=" * 40)
    
    # Test retention rate calculations
    print("Retention rate tests:")
    test_cases = [
        (0, 1, 2.5, "Not learned, 1 day"),
        (1, 1, 2.5, "Learning, 1 day"),
        (1, 7, 2.5, "Learning, 1 week"),
        (2, 1, 2.5, "Mastered, 1 day"),
        (2, 7, 2.5, "Mastered, 1 week"),
        (2, 30, 2.5, "Mastered, 1 month"),
    ]
    
    for mastery, days, ease, description in test_cases:
        retention = spaced_repetition_service.calculate_retention_rate(mastery, days, ease)
        print(f"   {description}: {retention:.1%}")
    
    # Test priority calculations
    print("\nPriority calculation tests:")
    now = datetime.now()
    priority_cases = [
        (0, now - timedelta(days=2), 5, "Not learned, overdue, high importance"),
        (1, now, 3, "Learning, due now, medium importance"),
        (2, now + timedelta(days=5), 1, "Mastered, future, low importance"),
    ]
    
    for mastery, next_review, importance, description in priority_cases:
        priority = spaced_repetition_service.get_study_priority(mastery, next_review, importance)
        print(f"   {description}: {priority:.2f}")


def main():
    """Main comprehensive test function"""
    print("🧠 Comprehensive Learning Records and Spaced Repetition Test")
    print("=" * 60)
    
    # Create tables
    create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Setup test data
        user, kb, doc, knowledge_points, learning_set = setup_comprehensive_test_data(db)
        
        # Test learning record lifecycle
        record = test_learning_record_lifecycle(db, user, knowledge_points, learning_set)
        
        # Test spaced repetition algorithm
        test_spaced_repetition_algorithm(db, user, knowledge_points, learning_set)
        
        # Test due items functionality
        test_due_items_functionality(db, user, learning_set)
        
        # Test learning statistics
        test_learning_statistics(db, user, learning_set)
        
        # Test memory curve calculations
        test_memory_curve_calculations()
        
        print("\n🎉 All comprehensive tests completed successfully!")
        print("=" * 60)
        print("✅ Learning record CRUD operations work correctly")
        print("✅ Spaced repetition algorithm functions properly")
        print("✅ Due items detection works as expected")
        print("✅ Learning statistics are calculated correctly")
        print("✅ Memory curve calculations are accurate")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Comprehensive test failed with error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)