"""
Test script for the evaluation service
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.database import get_db, engine
from app.models.models import Base, User, KnowledgeBase, Document, Question
from app.services.evaluation_service import evaluation_service
from app.services.model_service import model_service
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
        # Create test user
        test_user = User(
            username="test_eval_user",
            email="test_eval@example.com",
            password_hash="hashed_password"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Create test knowledge base
        test_kb = KnowledgeBase(
            user_id=test_user.id,
            name="Test Knowledge Base",
            description="Test KB for evaluation"
        )
        db.add(test_kb)
        db.commit()
        db.refresh(test_kb)
        
        # Create test document
        test_doc = Document(
            knowledge_base_id=test_kb.id,
            filename="test_document.txt",
            file_path="/test/path/test_document.txt",
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
        
        print(f"Created test user: {test_user.id}")
        print(f"Created test question: {test_question.id}")
        
        return test_user.id, test_question.id
        
    except Exception as e:
        print(f"Error setting up test data: {e}")
        db.rollback()
        return None, None
    finally:
        db.close()


async def test_answer_evaluation():
    """Test answer evaluation functionality"""
    print("\n=== Testing Answer Evaluation ===")
    
    # Setup test data
    user_id, question_id = await setup_test_data()
    if not user_id or not question_id:
        print("Failed to setup test data")
        return
    
    db = TestingSessionLocal()
    try:
        # Test cases with different answer qualities
        test_cases = [
            {
                "name": "Good Answer",
                "answer": "机器学习是人工智能的一个重要分支，它让计算机能够通过数据和经验自动学习和改进，而不需要明确的编程指令。它包括监督学习、无监督学习和强化学习等方法。"
            },
            {
                "name": "Average Answer", 
                "answer": "机器学习就是让计算机自己学习的技术。"
            },
            {
                "name": "Poor Answer",
                "answer": "不知道。"
            }
        ]
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            print(f"Answer: {test_case['answer']}")
            
            # Evaluate answer
            result = await evaluation_service.evaluate_answer(
                db=db,
                user_id=user_id,
                question_id=question_id,
                user_answer=test_case['answer'],
                save_record=True
            )
            
            if result.get('success'):
                evaluation = result['evaluation']
                print(f"Score: {evaluation.get('score', 'N/A')}/10")
                print(f"Feedback: {evaluation.get('feedback', 'N/A')[:100]}...")
                print(f"Reference Answer: {evaluation.get('reference_answer', 'N/A')[:100]}...")
                
                if 'detailed_analysis' in evaluation:
                    analysis = evaluation['detailed_analysis']
                    print(f"Has detailed analysis: {bool(analysis.get('overall_analysis'))}")
                    print(f"Improvement suggestions: {len(analysis.get('improvement_suggestions', []))}")
                
                if 'record_id' in evaluation:
                    print(f"Saved as record ID: {evaluation['record_id']}")
            else:
                print(f"Evaluation failed: {result.get('error', 'Unknown error')}")
            
            print("-" * 50)
    
    except Exception as e:
        print(f"Error during evaluation testing: {e}")
    finally:
        db.close()


async def test_answer_records():
    """Test answer records retrieval"""
    print("\n=== Testing Answer Records ===")
    
    db = TestingSessionLocal()
    try:
        # Get first user for testing
        user = db.query(User).first()
        if not user:
            print("No test user found")
            return
        
        # Get answer records
        records = await evaluation_service.get_answer_records(
            db=db,
            user_id=user.id,
            skip=0,
            limit=10
        )
        
        print(f"Found {len(records)} answer records")
        
        for i, record in enumerate(records[:3]):  # Show first 3 records
            print(f"\nRecord {i+1}:")
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
    
    db = TestingSessionLocal()
    try:
        # Get first user for testing
        user = db.query(User).first()
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
    
    except Exception as e:
        print(f"Error testing statistics: {e}")
    finally:
        db.close()


async def test_batch_evaluation():
    """Test batch answer evaluation"""
    print("\n=== Testing Batch Evaluation ===")
    
    db = TestingSessionLocal()
    try:
        # Get test data
        user = db.query(User).first()
        question = db.query(Question).first()
        
        if not user or not question:
            print("No test data found")
            return
        
        # Prepare batch answers
        batch_answers = [
            {
                "question_id": question.id,
                "user_answer": "这是第一个批量测试答案。"
            },
            {
                "question_id": question.id,
                "user_answer": "这是第二个批量测试答案，内容更详细一些。"
            }
        ]
        
        # Batch evaluate
        result = await evaluation_service.batch_evaluate_answers(
            db=db,
            user_id=user.id,
            answers=batch_answers
        )
        
        if result.get('success'):
            print(f"Batch evaluation completed:")
            print(f"  Total processed: {result['total_processed']}")
            print(f"  Successful: {result['successful_evaluations']}")
            print(f"  Failed: {result['failed_evaluations']}")
        else:
            print(f"Batch evaluation failed: {result.get('error')}")
    
    except Exception as e:
        print(f"Error testing batch evaluation: {e}")
    finally:
        db.close()


async def main():
    """Main test function"""
    print("Starting Evaluation Service Tests")
    print("=" * 50)
    
    try:
        # Start model service
        await model_service.start()
        print("Model service started")
        
        # Run tests
        await test_answer_evaluation()
        await test_answer_records()
        await test_evaluation_statistics()
        await test_batch_evaluation()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"Test execution failed: {e}")
    finally:
        # Stop model service
        await model_service.stop()
        print("Model service stopped")


if __name__ == "__main__":
    asyncio.run(main())