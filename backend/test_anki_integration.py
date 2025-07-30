"""
Simple integration test for Anki functionality
"""
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.models.database import Base
from app.models.models import User, KnowledgeBase, Document, Question, AnswerRecord, KnowledgePoint
from app.services.anki_service import AnkiService


def test_anki_integration():
    """Test Anki service integration with real data"""
    
    # Create test database
    TEST_DATABASE_URL = "sqlite:///./test_anki_integration.db"
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    try:
        print("Creating test data...")
        
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create knowledge base
        kb = KnowledgeBase(
            user_id=user.id,
            name="Machine Learning Basics",
            description="Introduction to ML concepts"
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        
        # Create document
        doc = Document(
            knowledge_base_id=kb.id,
            filename="ml_intro.pdf",
            file_path="/uploads/ml_intro.pdf",
            file_type="pdf",
            file_size=2048,
            processed=True
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Create questions
        questions = [
            Question(
                document_id=doc.id,
                question_text="What is machine learning?",
                context="Machine learning is a method of data analysis that automates analytical model building.",
                difficulty_level=1
            ),
            Question(
                document_id=doc.id,
                question_text="What are the main types of machine learning?",
                context="There are three main types: supervised, unsupervised, and reinforcement learning.",
                difficulty_level=2
            ),
            Question(
                document_id=doc.id,
                question_text="How does neural network training work?",
                context="Neural networks learn through backpropagation and gradient descent optimization.",
                difficulty_level=3
            )
        ]
        
        for q in questions:
            db.add(q)
        db.commit()
        
        for q in questions:
            db.refresh(q)
        
        # Create answer records
        answers = [
            AnswerRecord(
                user_id=user.id,
                question_id=questions[0].id,
                user_answer="Machine learning is a way for computers to learn from data without being explicitly programmed.",
                reference_answer="Machine learning is a method of data analysis that automates analytical model building using algorithms that iteratively learn from data.",
                score=9.0,
                feedback="Excellent understanding of the core concept!"
            ),
            AnswerRecord(
                user_id=user.id,
                question_id=questions[1].id,
                user_answer="Supervised learning uses labeled data, unsupervised finds patterns in unlabeled data.",
                reference_answer="The three main types are: supervised learning (uses labeled data), unsupervised learning (finds patterns in unlabeled data), and reinforcement learning (learns through interaction with environment).",
                score=7.5,
                feedback="Good answer, but missed reinforcement learning."
            ),
            AnswerRecord(
                user_id=user.id,
                question_id=questions[2].id,
                user_answer="Neural networks use backpropagation to adjust weights based on errors.",
                reference_answer="Neural networks learn through backpropagation, which calculates gradients of the loss function and uses gradient descent to optimize weights and biases.",
                score=8.0,
                feedback="Correct understanding of backpropagation process."
            )
        ]
        
        for a in answers:
            db.add(a)
        db.commit()
        
        # Create knowledge points
        knowledge_points = [
            KnowledgePoint(
                document_id=doc.id,
                title="Definition of Machine Learning",
                content="Machine learning is a subset of artificial intelligence (AI) that provides systems the ability to automatically learn and improve from experience without being explicitly programmed.",
                importance_level=5
            ),
            KnowledgePoint(
                document_id=doc.id,
                title="Supervised Learning",
                content="Supervised learning uses labeled training data to learn a mapping function from input variables to output variables. Examples include classification and regression.",
                importance_level=4
            ),
            KnowledgePoint(
                document_id=doc.id,
                title="Unsupervised Learning",
                content="Unsupervised learning finds hidden patterns or intrinsic structures in input data without labeled examples. Examples include clustering and dimensionality reduction.",
                importance_level=4
            ),
            KnowledgePoint(
                document_id=doc.id,
                title="Neural Networks",
                content="Neural networks are computing systems vaguely inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information using connectionist approaches.",
                importance_level=3
            )
        ]
        
        for kp in knowledge_points:
            db.add(kp)
        db.commit()
        
        print("Test data created successfully!")
        
        # Test Anki service
        print("Testing Anki service...")
        anki_service = AnkiService()
        
        # Test 1: Generate deck from knowledge base
        print("1. Testing knowledge base export...")
        kb_deck_path = anki_service.generate_deck_from_knowledge_base(
            user_id=user.id,
            knowledge_base_id=kb.id,
            include_qa=True,
            include_kp=True,
            db=db
        )
        
        print(f"   Generated deck: {kb_deck_path}")
        assert os.path.exists(kb_deck_path), "Knowledge base deck file should exist"
        
        file_size = os.path.getsize(kb_deck_path)
        print(f"   File size: {file_size} bytes")
        assert file_size > 1000, "Deck file should be substantial"
        
        # Test 2: Generate custom deck
        print("2. Testing custom deck export...")
        custom_deck_path = anki_service.generate_custom_deck(
            user_id=user.id,
            deck_name="Selected ML Content",
            answer_record_ids=[1, 2],  # First two answers
            knowledge_point_ids=[1, 4],  # Definition and Neural Networks
            db=db
        )
        
        print(f"   Generated custom deck: {custom_deck_path}")
        assert os.path.exists(custom_deck_path), "Custom deck file should exist"
        
        custom_file_size = os.path.getsize(custom_deck_path)
        print(f"   File size: {custom_file_size} bytes")
        assert custom_file_size > 500, "Custom deck file should contain data"
        
        # Test 3: Generate Q&A only deck
        print("3. Testing Q&A only deck...")
        qa_deck_path = anki_service.generate_deck_from_knowledge_base(
            user_id=user.id,
            knowledge_base_id=kb.id,
            include_qa=True,
            include_kp=False,
            db=db
        )
        
        print(f"   Generated Q&A deck: {qa_deck_path}")
        assert os.path.exists(qa_deck_path), "Q&A deck file should exist"
        
        # Test 4: Generate knowledge points only deck
        print("4. Testing knowledge points only deck...")
        kp_deck_path = anki_service.generate_deck_from_knowledge_base(
            user_id=user.id,
            knowledge_base_id=kb.id,
            include_qa=False,
            include_kp=True,
            db=db
        )
        
        print(f"   Generated KP deck: {kp_deck_path}")
        assert os.path.exists(kp_deck_path), "Knowledge points deck file should exist"
        
        print("All tests passed! ✅")
        
        # Cleanup generated files
        for path in [kb_deck_path, custom_deck_path, qa_deck_path, kp_deck_path]:
            if os.path.exists(path):
                os.remove(path)
                # Remove temp directory if empty
                temp_dir = os.path.dirname(path)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
        
        print("Cleanup completed!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise e
    finally:
        db.close()
        # Cleanup test database
        if os.path.exists("test_anki_integration.db"):
            os.remove("test_anki_integration.db")


if __name__ == "__main__":
    test_anki_integration()
    print("🎉 Anki integration test completed successfully!")