"""
Database initialization script
"""
import logging
from sqlalchemy.exc import SQLAlchemyError

from .database import engine, create_tables, drop_tables, SessionLocal
from .models import User, KnowledgeBase, Document, Question, AnswerRecord, KnowledgePoint, ReviewRecord

logger = logging.getLogger(__name__)


def init_database(drop_existing: bool = False):
    """
    Initialize the database with tables
    
    Args:
        drop_existing: Whether to drop existing tables first
    """
    try:
        if drop_existing:
            logger.info("Dropping existing database tables...")
            drop_tables()
        
        logger.info("Creating database tables...")
        create_tables()
        
        logger.info("Database initialization completed successfully")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def create_sample_data():
    """
    Create sample data for testing purposes
    """
    db = SessionLocal()
    try:
        # Check if sample data already exists
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            logger.info("Sample data already exists, skipping creation")
            return True
        
        # Create sample user
        sample_user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "secret"
        )
        db.add(sample_user)
        db.commit()
        db.refresh(sample_user)
        
        # Create sample knowledge base
        sample_kb = KnowledgeBase(
            user_id=sample_user.id,
            name="Sample Knowledge Base",
            description="A sample knowledge base for testing"
        )
        db.add(sample_kb)
        db.commit()
        db.refresh(sample_kb)
        
        logger.info("Sample data created successfully")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to create sample data: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def verify_database():
    """
    Verify that all tables exist and are accessible
    """
    db = SessionLocal()
    try:
        # Test each model
        models_to_test = [User, KnowledgeBase, Document, Question, AnswerRecord, KnowledgePoint, ReviewRecord]
        
        for model in models_to_test:
            count = db.query(model).count()
            logger.info(f"{model.__name__} table: {count} records")
        
        logger.info("Database verification completed successfully")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database verification failed: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    if init_database():
        # Create sample data
        create_sample_data()
        
        # Verify database
        verify_database()
    else:
        logger.error("Database initialization failed")