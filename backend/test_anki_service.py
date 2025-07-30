"""
Test script for Anki service functionality
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.models.database import Base
from app.models.models import User, KnowledgeBase, Document, Question, AnswerRecord, KnowledgePoint
from app.services.anki_service import AnkiService


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_anki.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_data():
    """Set up test data"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db.add(user)
        db.flush()
        
        # Create knowledge base
        kb = KnowledgeBase(
            user_id=user.id,
            name="Test Knowledge Base",
            description="Test description"
        )
        db.add(kb)
        db.flush()
        
        # Create document
        doc = Document(
            knowledge_base_id=kb.id,
            filename="test.pdf",
            file_path="/test/path/test.pdf",
            file_type="pdf",
            file_size=1024,
            processed=True
        )
        db.add(doc)
        db.flush()
        
        # Create questions
        question1 = Question(
            document_id=doc.id,
            question_text="What is the main concept?",
            context="This is the context for the question",
            difficulty_level=2
        )
        question2 = Question(
            document_id=doc.id,
            question_text="How does this work?",
            context="Another context",
            difficulty_level=3
        )
        db.add_all([question1, question2])
        db.flush()
        
        # Create answer records
        answer1 = AnswerRecord(
            user_id=user.id,
            question_id=question1.id,
            user_answer="The main concept is about learning",
            reference_answer="The main concept is about machine learning and AI",
            score=8.5,
            feedback="Good answer, but could be more specific"
        )
        answer2 = AnswerRecord(
            user_id=user.id,
            question_id=question2.id,
            user_answer="It works through algorithms",
            reference_answer="It works through neural networks and deep learning algorithms",
            score=7.0,
            feedback="Correct but needs more detail"
        )
        db.add_all([answer1, answer2])
        db.flush()
        
        # Create knowledge points
        kp1 = KnowledgePoint(
            document_id=doc.id,
            title="Machine Learning Basics",
            content="Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data",
            importance_level=5
        )
        kp2 = KnowledgePoint(
            document_id=doc.id,
            title="Neural Networks",
            content="Neural networks are computing systems inspired by biological neural networks",
            importance_level=4
        )
        db.add_all([kp1, kp2])
        
        db.commit()
        return user.id, kb.id
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def test_anki_service():
    """Test Anki service functionality"""
    print("Setting up test data...")
    user_id, kb_id = setup_test_data()
    
    print("Initializing Anki service...")
    anki_service = AnkiService()
    
    db = TestingSessionLocal()
    
    try:
        print("Testing deck generation from knowledge base...")
        file_path = anki_service.generate_deck_from_knowledge_base(
            user_id=user_id,
            knowledge_base_id=kb_id,
            include_qa=True,
            include_kp=True,
            db=db
        )
        
        print(f"Generated deck file: {file_path}")
        assert os.path.exists(file_path), "Deck file should exist"
        assert file_path.endswith('.apkg'), "File should have .apkg extension"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size} bytes")
        assert file_size > 0, "File should not be empty"
        
        print("Testing custom deck generation...")
        custom_file_path = anki_service.generate_custom_deck(
            user_id=user_id,
            deck_name="Custom Test Deck",
            answer_record_ids=[1, 2],
            knowledge_point_ids=[1, 2],
            db=db
        )
        
        print(f"Generated custom deck file: {custom_file_path}")
        assert os.path.exists(custom_file_path), "Custom deck file should exist"
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(custom_file_path):
            os.remove(custom_file_path)
        
        print("All tests passed!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise e
    finally:
        db.close()


def cleanup_test_db():
    """Clean up test database"""
    if os.path.exists("test_anki.db"):
        os.remove("test_anki.db")


if __name__ == "__main__":
    try:
        test_anki_service()
        print("✅ Anki service test completed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        cleanup_test_db()