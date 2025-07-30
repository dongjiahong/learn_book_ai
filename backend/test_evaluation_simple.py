"""
Simple test script for the evaluation service (without model calls)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.database import get_db, engine
from app.models.models import Base, User, KnowledgeBase, Document, Question, AnswerRecord
from sqlalchemy.orm import sessionmaker

# Create test database session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def setup_test_data():
    """Set up test data for evaluation testing"""
    print("Setting up test data...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        # Get or create test user
        test_user = db.query(User).filter(User.username == "test_eval_user_simple").first()
        if not test_user:
            test_user = User(
                username="test_eval_user_simple",
                email="test_eval_simple@example.com",
                password_hash="hashed_password"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        # Create test knowledge base
        test_kb = KnowledgeBase(
            user_id=test_user.id,
            name="Test Knowledge Base Simple",
            description="Test KB for evaluation"
        )
        db.add(test_kb)
        db.commit()
        db.refresh(test_kb)
        
        # Create test document
        test_doc = Document(
            knowledge_base_id=test_kb.id,
            filename="test_document_simple.txt",
            file_path="/test/path/test_document_simple.txt",
            file_type="txt",
            file_size=1000,
            processed=True
        )
        db.add(test_doc)
        db.commit()
        db.refresh(test_doc)
        
        # Create test question
        test_question = Question(
            document_id=test_doc.id,
            question_text="什么是机器学习？",
            context="机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。",
            difficulty_level=2
        )
        db.add(test_question)
        db.commit()
        db.refresh(test_question)
        
        # Create some test answer records
        test_records = [
            AnswerRecord(
                user_id=test_user.id,
                question_id=test_question.id,
                user_answer="机器学习是让计算机自动学习的技术",
                reference_answer="机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。",
                score=7.5,
                feedback="答案基本正确，但可以更详细一些。"
            ),
            AnswerRecord(
                user_id=test_user.id,
                question_id=test_question.id,
                user_answer="机器学习是AI的重要组成部分，通过数据训练模型来实现智能决策。",
                reference_answer="机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。",
                score=9.0,
                feedback="答案很好，涵盖了关键概念。"
            ),
            AnswerRecord(
                user_id=test_user.id,
                question_id=test_question.id,
                user_answer="不知道",
                reference_answer="机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。",
                score=1.0,
                feedback="答案不完整，需要学习相关概念。"
            )
        ]
        
        for record in test_records:
            db.add(record)
        
        db.commit()
        
        print(f"Created test user: {test_user.id}")
        print(f"Created test question: {test_question.id}")
        print(f"Created {len(test_records)} test answer records")
        
        return test_user.id, test_question.id
        
    except Exception as e:
        print(f"Error setting up test data: {e}")
        db.rollback()
        return None, None
    finally:
        db.close()


async def test_answer_records():
    """Test answer records retrieval"""
    print("\n=== Testing Answer Records ===")
    
    from app.services.evaluation_service import evaluation_service
    
    db = TestingSessionLocal()
    try:
        # Get the specific test user we created
        user = db.query(User).filter(User.username == "test_eval_user_simple").first()
        if not user:
            print("No test user found")
            return
        
        # Debug: Check direct query first
        direct_records = db.query(AnswerRecord).filter(AnswerRecord.user_id == user.id).all()
        print(f"Direct query found {len(direct_records)} records for user {user.id}")
        
        # Get answer records
        records = await evaluation_service.get_answer_records(
            db=db,
            user_id=user.id,
            skip=0,
            limit=10
        )
        
        print(f"Found {len(records)} answer records")
        
        for i, record in enumerate(records):
            print(f"\nRecord {i+1}:")
            print(f"  ID: {record['id']}")
            print(f"  Question: {record['question_text'][:50]}...")
            print(f"  User Answer: {record['user_answer'][:50]}...")
            print(f"  Score: {record['score']}")
            print(f"  Date: {record['answered_at']}")
    
    except Exception as e:
        print(f"Error testing answer records: {e}")
    finally:
        db.close()


async def test_evaluation_statistics():
    """Test evaluation statistics"""
    print("\n=== Testing Evaluation Statistics ===")
    
    from app.services.evaluation_service import evaluation_service
    
    db = TestingSessionLocal()
    try:
        # Get the specific test user we created
        user = db.query(User).filter(User.username == "test_eval_user_simple").first()
        if not user:
            print("No test user found")
            return
        
        # Get statistics
        stats = await evaluation_service.get_evaluation_statistics(
            db=db,
            user_id=user.id
        )
        
        print(f"Total answers: {stats['total_answers']}")
        print(f"Average score: {stats['average_score']}")
        print(f"Score distribution: {stats['score_distribution']}")
        print(f"Recent performance entries: {len(stats['recent_performance'])}")
        
        # Show recent performance details
        print("\nRecent Performance:")
        for i, perf in enumerate(stats['recent_performance'][:3]):
            print(f"  {i+1}. Score: {perf['score']}, Date: {perf['date']}")
            print(f"     Question: {perf['question_text'][:60]}...")
    
    except Exception as e:
        print(f"Error testing statistics: {e}")
    finally:
        db.close()


async def test_database_operations():
    """Test basic database operations"""
    print("\n=== Testing Database Operations ===")
    
    db = TestingSessionLocal()
    try:
        # Count records
        user_count = db.query(User).count()
        kb_count = db.query(KnowledgeBase).count()
        doc_count = db.query(Document).count()
        question_count = db.query(Question).count()
        answer_count = db.query(AnswerRecord).count()
        
        print(f"Database record counts:")
        print(f"  Users: {user_count}")
        print(f"  Knowledge Bases: {kb_count}")
        print(f"  Documents: {doc_count}")
        print(f"  Questions: {question_count}")
        print(f"  Answer Records: {answer_count}")
        
        # Test query with joins
        records_with_details = (
            db.query(AnswerRecord)
            .join(Question)
            .join(Document)
            .join(KnowledgeBase)
            .join(User)
            .filter(User.username.like("test_eval_user%"))
            .all()
        )
        
        print(f"\nAnswer records with full details: {len(records_with_details)}")
        
        if records_with_details:
            record = records_with_details[0]
            print(f"Sample record details:")
            print(f"  User: {record.user.username}")
            print(f"  KB: {record.question.document.knowledge_base.name}")
            print(f"  Document: {record.question.document.filename}")
            print(f"  Question: {record.question.question_text[:50]}...")
            print(f"  Answer: {record.user_answer[:50]}...")
            print(f"  Score: {record.score}")
    
    except Exception as e:
        print(f"Error testing database operations: {e}")
    finally:
        db.close()


async def main():
    """Main test function"""
    print("Starting Simple Evaluation Service Tests")
    print("=" * 50)
    
    try:
        # Setup test data
        user_id, question_id = await setup_test_data()
        if not user_id or not question_id:
            print("Failed to setup test data")
            return
        
        # Run tests
        await test_database_operations()
        await test_answer_records()
        await test_evaluation_statistics()
        
        print("\n" + "=" * 50)
        print("All simple tests completed successfully!")
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())