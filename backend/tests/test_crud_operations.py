"""
Unit tests for CRUD operations
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.crud import (
    CRUDKnowledgeBase, CRUDDocument, CRUDQuestion, 
    CRUDAnswerRecord, CRUDReviewRecord
)
from app.models.models import (
    User, KnowledgeBase, Document, Question, 
    AnswerRecord, KnowledgePoint, ReviewRecord
)
from app.schemas.documents import KnowledgeBaseCreate, KnowledgeBaseUpdate


class TestCRUDKnowledgeBase:
    """Test CRUD operations for KnowledgeBase"""
    
    def test_create_knowledge_base(self, db_session: Session, test_user: User):
        """Test creating a knowledge base"""
        crud = CRUDKnowledgeBase(KnowledgeBase)
        kb_data = KnowledgeBaseCreate(
            name="Test KB",
            description="Test description"
        )
        
        kb = crud.create_for_user(db_session, obj_in=kb_data, user_id=test_user.id)
        
        assert kb.id is not None
        assert kb.name == "Test KB"
        assert kb.description == "Test description"
        assert kb.user_id == test_user.id
    
    def test_get_knowledge_base_by_user(self, db_session: Session, test_knowledge_base: KnowledgeBase):
        """Test getting knowledge bases by user"""
        crud = CRUDKnowledgeBase(KnowledgeBase)
        
        kbs = crud.get_by_user(db_session, user_id=test_knowledge_base.user_id)
        
        assert len(kbs) == 1
        assert kbs[0].id == test_knowledge_base.id
    
    def test_count_by_user(self, db_session: Session, test_knowledge_base: KnowledgeBase):
        """Test counting knowledge bases by user"""
        crud = CRUDKnowledgeBase(KnowledgeBase)
        
        count = crud.count_by_user(db_session, user_id=test_knowledge_base.user_id)
        
        assert count == 1
    
    def test_update_knowledge_base(self, db_session: Session, test_knowledge_base: KnowledgeBase):
        """Test updating a knowledge base"""
        crud = CRUDKnowledgeBase(KnowledgeBase)
        update_data = KnowledgeBaseUpdate(name="Updated KB")
        
        updated_kb = crud.update(db_session, db_obj=test_knowledge_base, obj_in=update_data)
        
        assert updated_kb.name == "Updated KB"
        assert updated_kb.id == test_knowledge_base.id


class TestCRUDDocument:
    """Test CRUD operations for Document"""
    
    def test_create_document_with_file_info(self, db_session: Session, test_knowledge_base: KnowledgeBase):
        """Test creating a document with file information"""
        crud = CRUDDocument(Document)
        
        doc = crud.create_with_file_info(
            db_session,
            knowledge_base_id=test_knowledge_base.id,
            filename="test.pdf",
            file_path="/path/test.pdf",
            file_type="pdf",
            file_size=1024
        )
        
        assert doc.id is not None
        assert doc.filename == "test.pdf"
        assert doc.processed is False
    
    def test_get_documents_by_knowledge_base(self, db_session: Session, test_document: Document):
        """Test getting documents by knowledge base"""
        crud = CRUDDocument(Document)
        
        docs = crud.get_by_knowledge_base(db_session, knowledge_base_id=test_document.knowledge_base_id)
        
        assert len(docs) == 1
        assert docs[0].id == test_document.id
    
    def test_mark_as_processed(self, db_session: Session, test_document: Document):
        """Test marking document as processed"""
        crud = CRUDDocument(Document)
        
        # Initially not processed
        assert test_document.processed is True  # From fixture
        
        # Create unprocessed document
        unprocessed_doc = crud.create_with_file_info(
            db_session,
            knowledge_base_id=test_document.knowledge_base_id,
            filename="unprocessed.pdf",
            file_path="/path/unprocessed.pdf",
            file_type="pdf",
            file_size=512
        )
        
        assert unprocessed_doc.processed is False
        
        # Mark as processed
        processed_doc = crud.mark_as_processed(db_session, document_id=unprocessed_doc.id)
        
        assert processed_doc.processed is True


class TestCRUDQuestion:
    """Test CRUD operations for Question"""
    
    def test_get_questions_by_document(self, db_session: Session, test_question: Question):
        """Test getting questions by document"""
        crud = CRUDQuestion(Question)
        
        questions = crud.get_by_document(db_session, document_id=test_question.document_id)
        
        assert len(questions) == 1
        assert questions[0].id == test_question.id
    
    def test_get_questions_by_difficulty(self, db_session: Session, test_question: Question):
        """Test getting questions by difficulty level"""
        crud = CRUDQuestion(Question)
        
        questions = crud.get_by_difficulty(db_session, difficulty_level=test_question.difficulty_level)
        
        assert len(questions) == 1
        assert questions[0].difficulty_level == test_question.difficulty_level
    
    def test_count_questions_by_document(self, db_session: Session, test_question: Question):
        """Test counting questions by document"""
        crud = CRUDQuestion(Question)
        
        count = crud.count_by_document(db_session, document_id=test_question.document_id)
        
        assert count == 1


class TestCRUDAnswerRecord:
    """Test CRUD operations for AnswerRecord"""
    
    def test_get_answer_records_by_user(self, db_session: Session, test_answer_record: AnswerRecord):
        """Test getting answer records by user"""
        crud = CRUDAnswerRecord(AnswerRecord)
        
        records = crud.get_by_user(db_session, user_id=test_answer_record.user_id)
        
        assert len(records) == 1
        assert records[0].id == test_answer_record.id
    
    def test_get_answer_records_by_score_range(self, db_session: Session, test_answer_record: AnswerRecord):
        """Test getting answer records by score range"""
        crud = CRUDAnswerRecord(AnswerRecord)
        
        # Test within range
        records = crud.get_by_score_range(
            db_session, 
            user_id=test_answer_record.user_id,
            min_score=8.0,
            max_score=9.0
        )
        
        assert len(records) == 1
        assert records[0].score == test_answer_record.score
        
        # Test outside range
        records = crud.get_by_score_range(
            db_session,
            user_id=test_answer_record.user_id,
            min_score=9.0,
            max_score=10.0
        )
        
        assert len(records) == 0
    
    def test_get_statistics(self, db_session: Session, test_answer_record: AnswerRecord):
        """Test getting learning statistics"""
        crud = CRUDAnswerRecord(AnswerRecord)
        
        stats = crud.get_statistics(db_session, user_id=test_answer_record.user_id)
        
        assert stats["total_questions_answered"] == 1
        assert stats["average_score"] == test_answer_record.score
        assert isinstance(stats["scores_by_date"], list)
        assert isinstance(stats["knowledge_base_progress"], list)
    
    def test_search_records(self, db_session: Session, test_answer_record: AnswerRecord):
        """Test searching answer records with filters"""
        crud = CRUDAnswerRecord(AnswerRecord)
        
        # Search by query text
        results = crud.search_records(
            db_session,
            user_id=test_answer_record.user_id,
            query="machine learning"
        )
        
        assert len(results) == 1
        
        # Search with score filter
        results = crud.search_records(
            db_session,
            user_id=test_answer_record.user_id,
            score_min=8.0
        )
        
        assert len(results) == 1
    
    def test_bulk_delete(self, db_session: Session, test_user: User, test_question: Question):
        """Test bulk deleting answer records"""
        crud = CRUDAnswerRecord(AnswerRecord)
        
        # Create multiple records
        records = []
        for i in range(3):
            record = AnswerRecord(
                user_id=test_user.id,
                question_id=test_question.id,
                user_answer=f"Answer {i}",
                score=float(i + 7)
            )
            db_session.add(record)
            records.append(record)
        
        db_session.commit()
        
        # Bulk delete
        record_ids = [r.id for r in records[:2]]
        deleted_count = crud.bulk_delete(db_session, user_id=test_user.id, record_ids=record_ids)
        
        assert deleted_count == 2
        
        # Verify deletion
        remaining_records = crud.get_by_user(db_session, user_id=test_user.id)
        assert len(remaining_records) == 1


class TestCRUDReviewRecord:
    """Test CRUD operations for ReviewRecord"""
    
    def test_get_due_reviews(self, db_session: Session, test_user: User, test_question: Question):
        """Test getting due reviews"""
        crud = CRUDReviewRecord(ReviewRecord)
        
        # Create overdue review
        overdue_review = ReviewRecord(
            user_id=test_user.id,
            content_id=test_question.id,
            content_type="question",
            next_review=datetime.now() - timedelta(hours=1)
        )
        db_session.add(overdue_review)
        
        # Create future review
        future_review = ReviewRecord(
            user_id=test_user.id,
            content_id=test_question.id,
            content_type="knowledge_point",
            next_review=datetime.now() + timedelta(hours=1)
        )
        db_session.add(future_review)
        
        db_session.commit()
        
        # Get due reviews
        due_reviews = crud.get_due_reviews(db_session, user_id=test_user.id)
        
        assert len(due_reviews) == 1
        assert due_reviews[0].id == overdue_review.id
    
    def test_get_by_content(self, db_session: Session, test_review_record: ReviewRecord):
        """Test getting review record by content"""
        crud = CRUDReviewRecord(ReviewRecord)
        
        record = crud.get_by_content(
            db_session,
            user_id=test_review_record.user_id,
            content_id=test_review_record.content_id,
            content_type=test_review_record.content_type
        )
        
        assert record is not None
        assert record.id == test_review_record.id
    
    def test_update_review_schedule(self, db_session: Session, test_review_record: ReviewRecord):
        """Test updating review schedule"""
        crud = CRUDReviewRecord(ReviewRecord)
        
        original_interval = test_review_record.interval_days
        original_ease = test_review_record.ease_factor
        
        # Good quality response (should increase interval)
        updated_record = crud.update_review_schedule(
            db_session,
            test_review_record,
            quality=4
        )
        
        assert updated_record.interval_days > original_interval
        assert updated_record.ease_factor >= original_ease


class TestCRUDErrorHandling:
    """Test error handling in CRUD operations"""
    
    def test_get_nonexistent_record(self, db_session: Session):
        """Test getting a non-existent record"""
        crud = CRUDKnowledgeBase(KnowledgeBase)
        
        result = crud.get(db_session, id=99999)
        
        assert result is None
    
    def test_delete_nonexistent_record(self, db_session: Session):
        """Test deleting a non-existent record"""
        crud = CRUDKnowledgeBase(KnowledgeBase)
        
        result = crud.delete(db_session, id=99999)
        
        assert result is None
    
    def test_invalid_field_query(self, db_session: Session):
        """Test querying by invalid field"""
        crud = CRUDKnowledgeBase(KnowledgeBase)
        
        with pytest.raises((AttributeError, SQLAlchemyError)):
            crud.get_by_field(db_session, field_name="nonexistent_field", field_value="test")


class TestCRUDPerformance:
    """Test CRUD performance with larger datasets"""
    
    def test_pagination_performance(self, db_session: Session, performance_test_data):
        """Test pagination with large datasets"""
        crud = CRUDKnowledgeBase(KnowledgeBase)
        user_id = performance_test_data['knowledge_bases'][0].user_id
        
        # Test different page sizes
        page_sizes = [5, 10, 20]
        
        for page_size in page_sizes:
            kbs = crud.get_by_user(db_session, user_id=user_id, skip=0, limit=page_size)
            assert len(kbs) <= page_size
    
    def test_bulk_operations_performance(self, db_session: Session, test_user: User):
        """Test performance of bulk operations"""
        crud = CRUDAnswerRecord(AnswerRecord)
        
        # Create many records for bulk deletion test
        record_ids = []
        for i in range(100):
            record = AnswerRecord(
                user_id=test_user.id,
                question_id=1,  # Assuming question exists
                user_answer=f"Bulk answer {i}",
                score=float(i % 10)
            )
            db_session.add(record)
        
        db_session.commit()
        
        # Get all record IDs
        records = crud.get_by_user(db_session, user_id=test_user.id, limit=100)
        record_ids = [r.id for r in records]
        
        # Bulk delete should be efficient
        deleted_count = crud.bulk_delete(db_session, user_id=test_user.id, record_ids=record_ids)
        
        assert deleted_count == len(record_ids)