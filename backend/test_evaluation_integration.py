"""
Integration test for the complete answer evaluation system
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
from app.api.evaluation import router as evaluation_router
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Create test database session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def setup_test_data():
    """Set up comprehensive test data"""
    print("Setting up comprehensive test data...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        # Create test user
        test_user = User(
            username="integration_test_user",
            email="integration@example.com",
            password_hash="hashed_password"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Create test knowledge base
        test_kb = KnowledgeBase(
            user_id=test_user.id,
            name="Integration Test KB",
            description="Knowledge base for integration testing"
        )
        db.add(test_kb)
        db.commit()
        db.refresh(test_kb)
        
        # Create test document
        test_doc = Document(
            knowledge_base_id=test_kb.id,
            filename="integration_test.txt",
            file_path="/test/integration_test.txt",
            file_type="txt",
            file_size=2000,
            processed=True
        )
        db.add(test_doc)
        db.commit()
        db.refresh(test_doc)
        
        # Create multiple test questions
        test_questions = [
            Question(
                document_id=test_doc.id,
                question_text="什么是人工智能？",
                context="人工智能（AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。",
                difficulty_level=2
            ),
            Question(
                document_id=test_doc.id,
                question_text="机器学习的主要类型有哪些？",
                context="机器学习主要分为监督学习、无监督学习和强化学习三大类型。",
                difficulty_level=3
            ),
            Question(
                document_id=test_doc.id,
                question_text="深度学习与传统机器学习的区别是什么？",
                context="深度学习是机器学习的一个子集，使用多层神经网络来学习数据的复杂模式。",
                difficulty_level=4
            )
        ]
        
        for question in test_questions:
            db.add(question)
        
        db.commit()
        
        # Refresh questions to get IDs
        for question in test_questions:
            db.refresh(question)
        
        print(f"Created test user: {test_user.id}")
        print(f"Created test knowledge base: {test_kb.id}")
        print(f"Created test document: {test_doc.id}")
        print(f"Created {len(test_questions)} test questions")
        
        return test_user.id, [q.id for q in test_questions]
        
    except Exception as e:
        print(f"Error setting up test data: {e}")
        db.rollback()
        return None, []
    finally:
        db.close()


async def test_evaluation_service():
    """Test the evaluation service with different answer qualities"""
    print("\n=== Testing Evaluation Service ===")
    
    user_id, question_ids = await setup_test_data()
    if not user_id or not question_ids:
        print("Failed to setup test data")
        return False
    
    db = TestingSessionLocal()
    try:
        # Test different answer qualities for the first question
        test_cases = [
            {
                "name": "优秀答案",
                "answer": "人工智能是计算机科学的一个重要分支，它致力于创建能够模拟、扩展和辅助人类智能的计算机系统。AI系统能够执行感知、学习、推理、决策等通常需要人类智能的复杂任务，包括图像识别、自然语言处理、专家系统等应用领域。",
                "expected_score_range": (8, 10)
            },
            {
                "name": "良好答案",
                "answer": "人工智能是让计算机能够像人一样思考和学习的技术，可以用来解决复杂问题。",
                "expected_score_range": (6, 8)
            },
            {
                "name": "基础答案",
                "answer": "人工智能就是让机器变聪明的技术。",
                "expected_score_range": (3, 6)
            },
            {
                "name": "不完整答案",
                "answer": "AI",
                "expected_score_range": (0, 3)
            }
        ]
        
        results = []
        for i, test_case in enumerate(test_cases):
            print(f"\n测试案例 {i+1}: {test_case['name']}")
            print(f"答案: {test_case['answer']}")
            
            # Evaluate answer
            result = await evaluation_service.evaluate_answer(
                db=db,
                user_id=user_id,
                question_id=question_ids[0],
                user_answer=test_case['answer'],
                save_record=True
            )
            
            if result.get('success'):
                evaluation = result['evaluation']
                score = evaluation.get('score', 0)
                
                print(f"评分: {score}/10")
                print(f"反馈: {evaluation.get('feedback', 'N/A')[:100]}...")
                
                # Check if score is in expected range
                min_score, max_score = test_case['expected_score_range']
                if min_score <= score <= max_score:
                    print(f"✓ 评分在预期范围内 ({min_score}-{max_score})")
                    results.append(True)
                else:
                    print(f"✗ 评分超出预期范围 ({min_score}-{max_score})")
                    results.append(False)
                
                # Check if detailed analysis exists
                if evaluation.get('detailed_analysis'):
                    print("✓ 包含详细分析")
                else:
                    print("✗ 缺少详细分析")
                
            else:
                print(f"✗ 评估失败: {result.get('error', 'Unknown error')}")
                results.append(False)
            
            print("-" * 60)
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n评估服务测试成功率: {success_rate:.1f}%")
        
        return success_rate >= 75  # 75% success rate threshold
        
    except Exception as e:
        print(f"Error during evaluation testing: {e}")
        return False
    finally:
        db.close()


async def test_evaluation_statistics():
    """Test evaluation statistics functionality"""
    print("\n=== Testing Evaluation Statistics ===")
    
    db = TestingSessionLocal()
    try:
        # Get test user
        user = db.query(User).filter(User.username == "integration_test_user").first()
        if not user:
            print("No test user found")
            return False
        
        # Get statistics
        stats = await evaluation_service.get_evaluation_statistics(
            db=db,
            user_id=user.id
        )
        
        print(f"总答题数: {stats['total_answers']}")
        print(f"平均分: {stats['average_score']}")
        print(f"分数分布: {stats['score_distribution']}")
        print(f"最近表现记录数: {len(stats['recent_performance'])}")
        
        # Validate statistics
        if stats['total_answers'] > 0:
            print("✓ 统计数据正常")
            return True
        else:
            print("✗ 统计数据异常")
            return False
            
    except Exception as e:
        print(f"Error testing statistics: {e}")
        return False
    finally:
        db.close()


async def test_answer_records():
    """Test answer records functionality"""
    print("\n=== Testing Answer Records ===")
    
    db = TestingSessionLocal()
    try:
        # Get test user
        user = db.query(User).filter(User.username == "integration_test_user").first()
        if not user:
            print("No test user found")
            return False
        
        # Get answer records
        records = await evaluation_service.get_answer_records(
            db=db,
            user_id=user.id,
            skip=0,
            limit=10
        )
        
        print(f"找到 {len(records)} 条答题记录")
        
        if records:
            # Show sample record
            sample = records[0]
            print(f"示例记录:")
            print(f"  问题: {sample['question_text'][:50]}...")
            print(f"  用户答案: {sample['user_answer'][:50]}...")
            print(f"  评分: {sample['score']}")
            print(f"  时间: {sample['answered_at']}")
            print("✓ 答题记录功能正常")
            return True
        else:
            print("✗ 未找到答题记录")
            return False
            
    except Exception as e:
        print(f"Error testing answer records: {e}")
        return False
    finally:
        db.close()


async def main():
    """Main integration test function"""
    print("Starting Answer Evaluation System Integration Test")
    print("=" * 60)
    
    try:
        # Run all tests
        test_results = []
        
        # Test evaluation service
        result1 = await test_evaluation_service()
        test_results.append(("Evaluation Service", result1))
        
        # Test statistics
        result2 = await test_evaluation_statistics()
        test_results.append(("Evaluation Statistics", result2))
        
        # Test answer records
        result3 = await test_answer_records()
        test_results.append(("Answer Records", result3))
        
        # Summary
        print("\n" + "=" * 60)
        print("Integration Test Results:")
        print("-" * 60)
        
        passed = 0
        for test_name, result in test_results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print("-" * 60)
        print(f"Overall: {passed}/{len(test_results)} tests passed")
        
        if passed == len(test_results):
            print("🎉 All integration tests passed!")
            print("Answer Evaluation System is working correctly!")
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
        
        return passed == len(test_results)
        
    except Exception as e:
        print(f"Integration test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)