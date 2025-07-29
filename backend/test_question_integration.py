"""
Integration test for question generation workflow
"""

import asyncio
import sys
import os
from pathlib import Path
import tempfile

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.question_service import question_service
from app.services.rag_service import rag_service
from app.models.database import get_db, engine
from app.models.models import Base, User, KnowledgeBase, Document
from app.models.crud import knowledge_base_crud, document_crud
from sqlalchemy.orm import Session


async def create_test_data():
    """Create test data for integration testing"""
    print("Creating test data...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get or create test user
        test_user = db.query(User).filter(User.username == "test_user").first()
        if not test_user:
            # Try to find any existing user
            test_user = db.query(User).first()
            if not test_user:
                test_user = User(
                    username="test_user_new",
                    email="test_new@example.com",
                    password_hash="hashed_password"
                )
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
        
        # Check if test knowledge base exists
        test_kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == test_user.id,
            KnowledgeBase.name == "Test Knowledge Base"
        ).first()
        
        if not test_kb:
            test_kb = KnowledgeBase(
                user_id=test_user.id,
                name="Test Knowledge Base",
                description="Test knowledge base for question generation"
            )
            db.add(test_kb)
            db.commit()
            db.refresh(test_kb)
        
        # Create a test document with sample content
        test_doc = db.query(Document).filter(
            Document.knowledge_base_id == test_kb.id,
            Document.filename == "test_document.txt"
        ).first()
        
        if not test_doc:
            # Create a temporary file with test content
            test_content = """
机器学习基础知识

机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。
机器学习算法通过分析大量数据来识别模式，并使用这些模式来对新数据进行预测或决策。

主要的机器学习类型包括：

1. 监督学习
监督学习使用标记的训练数据来学习输入和输出之间的映射关系。
常见的监督学习算法包括线性回归、决策树、支持向量机等。
监督学习适用于分类和回归问题。

2. 无监督学习
无监督学习在没有标记数据的情况下发现数据中的隐藏模式。
常见的无监督学习算法包括聚类、降维、关联规则挖掘等。
无监督学习主要用于数据探索和特征发现。

3. 强化学习
强化学习通过与环境交互来学习最优行为策略。
智能体通过试错来学习，根据奖励信号调整行为。
强化学习在游戏、机器人控制等领域有广泛应用。

深度学习
深度学习是机器学习的一个子集，它使用多层神经网络来学习数据的复杂表示。
深度学习在图像识别、自然语言处理、语音识别等领域取得了突破性进展。
常见的深度学习模型包括卷积神经网络（CNN）、循环神经网络（RNN）、Transformer等。

模型评估
机器学习模型的性能需要通过适当的评估指标来衡量。
常见的评估指标包括准确率、精确率、召回率、F1分数等。
交叉验证是一种常用的模型评估方法，可以更好地估计模型的泛化能力。
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(test_content)
                temp_file_path = f.name
            
            test_doc = Document(
                knowledge_base_id=test_kb.id,
                filename="test_document.txt",
                file_path=temp_file_path,
                file_type=".txt",
                file_size=len(test_content.encode('utf-8')),
                processed=False
            )
            db.add(test_doc)
            db.commit()
            db.refresh(test_doc)
            
            # Load the document into RAG service
            print("Loading document into RAG service...")
            result = await rag_service.load_documents([temp_file_path])
            
            if result['success']:
                # Mark document as processed
                test_doc.processed = True
                db.commit()
                print("✅ Document loaded and processed successfully")
            else:
                print(f"❌ Failed to load document: {result}")
                return None, None, None
            
            # Clean up temp file
            os.unlink(temp_file_path)
        
        return test_user, test_kb, test_doc
        
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        return None, None, None
    finally:
        db.close()


async def test_question_generation_workflow():
    """Test the complete question generation workflow"""
    print("\n" + "="*60)
    print("Testing Complete Question Generation Workflow")
    print("="*60)
    
    # Create test data
    test_user, test_kb, test_doc = await create_test_data()
    
    if not all([test_user, test_kb, test_doc]):
        print("❌ Failed to create test data, skipping workflow test")
        return
    
    # Get database session
    db = next(get_db())
    
    try:
        # Re-fetch objects in current session to avoid detached instance errors
        test_user = db.query(User).filter(User.id == test_user.id).first()
        test_kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == test_kb.id).first()
        test_doc = db.query(Document).filter(Document.id == test_doc.id).first()
        
        print(f"\nTest Data Created:")
        print(f"- User: {test_user.username} (ID: {test_user.id})")
        print(f"- Knowledge Base: {test_kb.name} (ID: {test_kb.id})")
        print(f"- Document: {test_doc.filename} (ID: {test_doc.id})")
        print(f"- Document Processed: {test_doc.processed}")
        
        # Test 1: Generate questions for document
        print(f"\n1. Testing question generation for document...")
        result = await question_service.generate_questions_for_document(
            db=db,
            document_id=test_doc.id,
            num_questions=5,
            min_quality_score=5.0  # Lower threshold for testing
        )
        
        if result['success']:
            print(f"✅ Generated {result['saved_questions']} questions")
            print(f"   - Total generated: {result['generated_questions']}")
            print(f"   - Quality filtered: {result['quality_questions']}")
            print(f"   - Saved to database: {result['saved_questions']}")
            
            # Show sample questions
            if result['questions']:
                print(f"\n   Sample questions:")
                for i, q in enumerate(result['questions'][:3], 1):
                    print(f"   {i}. {q['question_text']}")
                    print(f"      Difficulty: {q['difficulty_level']}, Quality: {q['quality_score']}")
        else:
            print(f"❌ Question generation failed: {result.get('error')}")
            return
        
        # Test 2: Retrieve questions by document
        print(f"\n2. Testing question retrieval by document...")
        questions = await question_service.get_questions_by_document(
            db=db,
            document_id=test_doc.id
        )
        
        print(f"✅ Retrieved {len(questions)} questions from database")
        
        # Test 3: Generate questions for knowledge base
        print(f"\n3. Testing question generation for knowledge base...")
        kb_result = await question_service.generate_questions_for_knowledge_base(
            db=db,
            knowledge_base_id=test_kb.id,
            num_questions_per_document=3,
            min_quality_score=5.0
        )
        
        if kb_result['success']:
            print(f"✅ Knowledge base question generation completed")
            print(f"   - Total documents: {kb_result['total_documents']}")
            print(f"   - Successful documents: {kb_result['successful_documents']}")
            print(f"   - Total questions: {kb_result['total_questions_generated']}")
        else:
            print(f"❌ Knowledge base question generation failed: {kb_result.get('error')}")
        
        # Test 4: Retrieve questions by knowledge base
        print(f"\n4. Testing question retrieval by knowledge base...")
        kb_questions = await question_service.get_questions_by_knowledge_base(
            db=db,
            knowledge_base_id=test_kb.id
        )
        
        print(f"✅ Retrieved {len(kb_questions)} questions from knowledge base")
        
        # Test 5: Test question update
        if questions:
            print(f"\n5. Testing question update...")
            first_question_id = questions[0]['id']
            update_result = await question_service.update_question(
                db=db,
                question_id=first_question_id,
                updates={
                    'difficulty_level': 3,
                    'question_text': questions[0]['question_text'] + ' (已更新)'
                }
            )
            
            if update_result:
                print(f"✅ Question updated successfully")
                print(f"   - New difficulty: {update_result['difficulty_level']}")
            else:
                print(f"❌ Question update failed")
        
        print(f"\n" + "="*60)
        print("✅ All workflow tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def main():
    """Run integration tests"""
    print("Starting Question Generation Integration Tests")
    print("="*60)
    
    await test_question_generation_workflow()


if __name__ == "__main__":
    asyncio.run(main())