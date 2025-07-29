"""
Test script for question generation functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.question_service import QuestionQualityEvaluator, QuestionDifficultyClassifier
from app.services.model_service import model_service
from app.models.database import get_db, engine
from app.models.models import Base, User, KnowledgeBase, Document
from sqlalchemy.orm import Session


async def test_quality_evaluator():
    """Test the question quality evaluator"""
    print("Testing Question Quality Evaluator...")
    
    evaluator = QuestionQualityEvaluator()
    
    # Test cases
    test_cases = [
        {
            'question': '什么是机器学习？',
            'context': '机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。',
            'expected_score_range': (6, 10)
        },
        {
            'question': '如何实现深度学习模型的训练过程？',
            'context': '深度学习模型训练包括前向传播、损失计算、反向传播和参数更新等步骤。',
            'expected_score_range': (7, 10)
        },
        {
            'question': '是否需要大量数据',  # Poor question - no question mark, too short
            'context': '深度学习通常需要大量的训练数据来获得良好的性能。',
            'expected_score_range': (0, 5)
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        result = evaluator.evaluate_question_quality(
            test_case['question'], 
            test_case['context']
        )
        
        print(f"\nTest Case {i}:")
        print(f"Question: {test_case['question']}")
        print(f"Quality Score: {result['score']}")
        print(f"Issues: {result['issues']}")
        print(f"Strengths: {result['strengths']}")
        
        # Check if score is in expected range
        min_score, max_score = test_case['expected_score_range']
        if min_score <= result['score'] <= max_score:
            print("✅ Score within expected range")
        else:
            print(f"❌ Score {result['score']} not in expected range {test_case['expected_score_range']}")


async def test_difficulty_classifier():
    """Test the question difficulty classifier"""
    print("\n" + "="*50)
    print("Testing Question Difficulty Classifier...")
    
    classifier = QuestionDifficultyClassifier()
    
    # Test cases
    test_cases = [
        {
            'question': '什么是神经网络？',
            'context': '神经网络是一种模拟人脑神经元连接的计算模型。',
            'expected_difficulty': 1  # Basic recall
        },
        {
            'question': '解释反向传播算法的工作原理。',
            'context': '反向传播是训练神经网络的核心算法，通过计算梯度来更新权重。',
            'expected_difficulty': 2  # Comprehension
        },
        {
            'question': '如何在实际项目中应用卷积神经网络进行图像分类？',
            'context': '卷积神经网络在图像处理中广泛应用，包括特征提取和分类。',
            'expected_difficulty': 3  # Application
        },
        {
            'question': '分析不同优化算法对模型收敛速度的影响。',
            'context': '优化算法如SGD、Adam等在训练过程中有不同的收敛特性。',
            'expected_difficulty': 4  # Analysis
        },
        {
            'question': '设计一个新的损失函数来解决类别不平衡问题。',
            'context': '类别不平衡是机器学习中的常见问题，需要特殊的损失函数设计。',
            'expected_difficulty': 5  # Synthesis
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        difficulty = classifier.classify_difficulty(
            test_case['question'], 
            test_case['context']
        )
        
        print(f"\nTest Case {i}:")
        print(f"Question: {test_case['question']}")
        print(f"Classified Difficulty: {difficulty}")
        print(f"Expected Difficulty: {test_case['expected_difficulty']}")
        
        # Allow some tolerance in difficulty classification
        if abs(difficulty - test_case['expected_difficulty']) <= 1:
            print("✅ Difficulty classification acceptable")
        else:
            print("❌ Difficulty classification may need adjustment")


async def test_model_service_integration():
    """Test integration with model service"""
    print("\n" + "="*50)
    print("Testing Model Service Integration...")
    
    try:
        # Test question generation
        sample_content = """
        机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。
        机器学习算法通过分析大量数据来识别模式，并使用这些模式来对新数据进行预测或决策。
        
        主要的机器学习类型包括：
        1. 监督学习：使用标记的训练数据来学习输入和输出之间的映射关系
        2. 无监督学习：在没有标记数据的情况下发现数据中的隐藏模式
        3. 强化学习：通过与环境交互来学习最优行为策略
        
        深度学习是机器学习的一个子集，它使用多层神经网络来学习数据的复杂表示。
        """
        
        print("Generating questions from sample content...")
        questions = await model_service.generate_questions(sample_content, num_questions=3)
        
        print(f"\nGenerated {len(questions)} questions:")
        for i, question in enumerate(questions, 1):
            print(f"{i}. {question}")
        
        if questions:
            print("✅ Question generation successful")
        else:
            print("❌ No questions generated")
            
    except Exception as e:
        print(f"❌ Model service integration failed: {e}")


async def test_database_integration():
    """Test database integration"""
    print("\n" + "="*50)
    print("Testing Database Integration...")
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        db = next(get_db())
        
        # Check if we can query the database
        user_count = db.query(User).count()
        kb_count = db.query(KnowledgeBase).count()
        doc_count = db.query(Document).count()
        
        print(f"Database connection successful:")
        print(f"- Users: {user_count}")
        print(f"- Knowledge Bases: {kb_count}")
        print(f"- Documents: {doc_count}")
        
        print("✅ Database integration successful")
        
    except Exception as e:
        print(f"❌ Database integration failed: {e}")
    finally:
        db.close()


async def main():
    """Run all tests"""
    print("Starting Question Generation Service Tests")
    print("="*50)
    
    await test_quality_evaluator()
    await test_difficulty_classifier()
    await test_model_service_integration()
    await test_database_integration()
    
    print("\n" + "="*50)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())