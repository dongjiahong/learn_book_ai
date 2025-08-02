"""
Base CRUD operations for database models
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import datetime
import logging

from .database import Base
from .models import User, KnowledgeBase, Document, Question, AnswerRecord, KnowledgePoint, ReviewRecord
from ..schemas.documents import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate,
    DocumentCreate, DocumentUpdate
)

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base CRUD class with default methods to Create, Read, Update, Delete (CRUD)."""
    
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID"""
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} with id {id}: {e}")
            raise
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination"""
        try:
            return db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            raise
    
    def get_by_field(
        self, db: Session, field_name: str, field_value: Any
    ) -> Optional[ModelType]:
        """Get a single record by a specific field"""
        try:
            field = getattr(self.model, field_name)
            return db.query(self.model).filter(field == field_value).first()
        except (AttributeError, SQLAlchemyError) as e:
            logger.error(f"Error getting {self.model.__name__} by {field_name}: {e}")
            raise
    
    def get_multi_by_field(
        self, 
        db: Session, 
        field_name: str, 
        field_value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records by a specific field with pagination"""
        try:
            field = getattr(self.model, field_name)
            return (
                db.query(self.model)
                .filter(field == field_value)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except (AttributeError, SQLAlchemyError) as e:
            logger.error(f"Error getting multiple {self.model.__name__} by {field_name}: {e}")
            raise
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record"""
        try:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            db.rollback()
            raise
    
    def create_with_dict(self, db: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record from dictionary"""
        try:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__} with dict: {e}")
            db.rollback()
            raise
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing record"""
        try:
            obj_data = jsonable_encoder(db_obj)
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            db.rollback()
            raise
    
    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Delete a record by ID"""
        try:
            obj = db.query(self.model).get(id)
            if obj:
                db.delete(obj)
                db.commit()
                return obj
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {e}")
            db.rollback()
            raise
    
    def count(self, db: Session) -> int:
        """Count total records"""
        try:
            return db.query(self.model).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise
    
    def exists(self, db: Session, id: Any) -> bool:
        """Check if a record exists by ID"""
        try:
            return db.query(self.model).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model.__name__} with id {id}: {e}")
            raise


class CRUDKnowledgeBase(CRUDBase[KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate]):
    """CRUD operations for KnowledgeBase"""
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[KnowledgeBase]:
        """Get knowledge bases by user ID with pagination"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting knowledge bases for user {user_id}: {e}")
            raise
    
    def count_by_user(self, db: Session, user_id: int) -> int:
        """Count knowledge bases by user ID"""
        try:
            return db.query(self.model).filter(self.model.user_id == user_id).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting knowledge bases for user {user_id}: {e}")
            raise
    
    def get_with_document_count(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[tuple]:
        """Get knowledge bases with document count"""
        try:
            return (
                db.query(
                    self.model,
                    func.count(Document.id).label('document_count')
                )
                .outerjoin(Document)
                .filter(self.model.user_id == user_id)
                .group_by(self.model.id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting knowledge bases with document count for user {user_id}: {e}")
            raise
    
    def get_with_statistics(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[tuple]:
        """Get knowledge bases with document and knowledge point statistics"""
        try:
            return (
                db.query(
                    self.model,
                    func.count(func.distinct(Document.id)).label('document_count'),
                    func.count(func.distinct(KnowledgePoint.id)).label('knowledge_point_count')
                )
                .select_from(self.model)
                .outerjoin(Document, self.model.id == Document.knowledge_base_id)
                .outerjoin(KnowledgePoint, Document.id == KnowledgePoint.document_id)
                .filter(self.model.user_id == user_id)
                .group_by(self.model.id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting knowledge bases with statistics for user {user_id}: {e}")
            raise
    
    def get_statistics(self, db: Session, knowledge_base_id: int) -> Dict[str, Any]:
        """Get detailed statistics for a specific knowledge base"""
        try:
            # Get basic counts
            total_documents = (
                db.query(func.count(Document.id))
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .scalar()
            )
            
            total_knowledge_points = (
                db.query(func.count(KnowledgePoint.id))
                .join(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .scalar()
            )
            
            # Get document-level statistics
            document_stats = (
                db.query(
                    Document.id,
                    Document.filename,
                    func.count(KnowledgePoint.id).label('knowledge_point_count')
                )
                .outerjoin(KnowledgePoint)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .group_by(Document.id, Document.filename)
                .all()
            )
            
            return {
                "knowledge_base_id": knowledge_base_id,
                "total_documents": total_documents or 0,
                "total_knowledge_points": total_knowledge_points or 0,
                "documents": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "knowledge_point_count": doc.knowledge_point_count or 0
                    }
                    for doc in document_stats
                ]
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting statistics for knowledge base {knowledge_base_id}: {e}")
            raise
    
    def create_for_user(self, db: Session, *, obj_in: KnowledgeBaseCreate, user_id: int) -> KnowledgeBase:
        """Create a knowledge base for a specific user"""
        try:
            obj_in_data = jsonable_encoder(obj_in)
            obj_in_data['user_id'] = user_id
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Error creating knowledge base for user {user_id}: {e}")
            db.rollback()
            raise


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    """CRUD operations for Document"""
    
    def get_by_knowledge_base(
        self, 
        db: Session, 
        knowledge_base_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Document]:
        """Get documents by knowledge base ID with pagination"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.knowledge_base_id == knowledge_base_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting documents for knowledge base {knowledge_base_id}: {e}")
            raise
    
    def count_by_knowledge_base(self, db: Session, knowledge_base_id: int) -> int:
        """Count documents by knowledge base ID"""
        try:
            return db.query(self.model).filter(self.model.knowledge_base_id == knowledge_base_id).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting documents for knowledge base {knowledge_base_id}: {e}")
            raise
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Document]:
        """Get documents by user ID through knowledge base relationship"""
        try:
            return (
                db.query(self.model)
                .join(KnowledgeBase)
                .filter(KnowledgeBase.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting documents for user {user_id}: {e}")
            raise
    
    def get_unprocessed(self, db: Session, limit: int = 10) -> List[Document]:
        """Get unprocessed documents for background processing"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.processed == False)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting unprocessed documents: {e}")
            raise
    
    def mark_as_processed(self, db: Session, document_id: int) -> Optional[Document]:
        """Mark a document as processed"""
        try:
            document = db.query(self.model).filter(self.model.id == document_id).first()
            if document:
                document.processed = True
                db.commit()
                db.refresh(document)
                return document
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error marking document {document_id} as processed: {e}")
            db.rollback()
            raise
    
    def create_with_file_info(
        self, 
        db: Session, 
        *, 
        knowledge_base_id: int,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int
    ) -> Document:
        """Create a document with file information"""
        try:
            db_obj = self.model(
                knowledge_base_id=knowledge_base_id,
                filename=filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                processed=False
            )
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Error creating document with file info: {e}")
            db.rollback()
            raise


class CRUDQuestion(CRUDBase[Question, None, None]):
    """CRUD operations for Question"""
    
    def get_by_document(
        self, 
        db: Session, 
        document_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Question]:
        """Get questions by document ID with pagination"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.document_id == document_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting questions for document {document_id}: {e}")
            raise
    
    def get_by_knowledge_base(
        self, 
        db: Session, 
        knowledge_base_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Question]:
        """Get questions by knowledge base ID through document relationship"""
        try:
            return (
                db.query(self.model)
                .join(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting questions for knowledge base {knowledge_base_id}: {e}")
            raise
    
    def get_by_difficulty(
        self, 
        db: Session, 
        difficulty_level: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Question]:
        """Get questions by difficulty level"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.difficulty_level == difficulty_level)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting questions with difficulty {difficulty_level}: {e}")
            raise
    
    def count_by_document(self, db: Session, document_id: int) -> int:
        """Count questions by document ID"""
        try:
            return db.query(self.model).filter(self.model.document_id == document_id).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting questions for document {document_id}: {e}")
            raise
    
    def count_by_knowledge_base(self, db: Session, knowledge_base_id: int) -> int:
        """Count questions by knowledge base ID"""
        try:
            return (
                db.query(self.model)
                .join(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .count()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error counting questions for knowledge base {knowledge_base_id}: {e}")
            raise


class CRUDAnswerRecord(CRUDBase[AnswerRecord, None, None]):
    """CRUD operations for AnswerRecord"""
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AnswerRecord]:
        """Get answer records by user ID with pagination"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.user_id == user_id)
                .order_by(self.model.answered_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting answer records for user {user_id}: {e}")
            raise
    
    def get_by_question(
        self, 
        db: Session, 
        question_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AnswerRecord]:
        """Get answer records by question ID with pagination"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.question_id == question_id)
                .order_by(self.model.answered_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting answer records for question {question_id}: {e}")
            raise
    
    def get_by_knowledge_base(
        self, 
        db: Session, 
        user_id: int,
        knowledge_base_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AnswerRecord]:
        """Get answer records by knowledge base ID through document and question relationships"""
        try:
            return (
                db.query(self.model)
                .join(Question)
                .join(Document)
                .filter(
                    self.model.user_id == user_id,
                    Document.knowledge_base_id == knowledge_base_id
                )
                .order_by(self.model.answered_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting answer records for knowledge base {knowledge_base_id}: {e}")
            raise
    
    def get_by_score_range(
        self, 
        db: Session, 
        user_id: int,
        min_score: float = None,
        max_score: float = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[AnswerRecord]:
        """Get answer records by score range"""
        try:
            query = db.query(self.model).filter(self.model.user_id == user_id)
            
            if min_score is not None:
                query = query.filter(self.model.score >= min_score)
            if max_score is not None:
                query = query.filter(self.model.score <= max_score)
            
            return (
                query
                .order_by(self.model.answered_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting answer records by score range for user {user_id}: {e}")
            raise
    
    def get_by_date_range(
        self, 
        db: Session, 
        user_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[AnswerRecord]:
        """Get answer records by date range"""
        try:
            query = db.query(self.model).filter(self.model.user_id == user_id)
            
            if start_date:
                query = query.filter(self.model.answered_at >= start_date)
            if end_date:
                query = query.filter(self.model.answered_at <= end_date)
            
            return (
                query
                .order_by(self.model.answered_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting answer records by date range for user {user_id}: {e}")
            raise
    
    def get_with_details(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[tuple]:
        """Get answer records with question, document, and knowledge base details"""
        try:
            return (
                db.query(
                    self.model,
                    Question.question_text,
                    Document.filename,
                    KnowledgeBase.name.label('knowledge_base_name')
                )
                .select_from(self.model)
                .join(Question, self.model.question_id == Question.id)
                .join(Document, Question.document_id == Document.id)
                .join(KnowledgeBase, Document.knowledge_base_id == KnowledgeBase.id)
                .filter(self.model.user_id == user_id)
                .order_by(self.model.answered_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting answer records with details for user {user_id}: {e}")
            raise
    
    def get_statistics(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get learning statistics for a user"""
        try:
            # Basic statistics
            total_count = db.query(self.model).filter(self.model.user_id == user_id).count()
            
            if total_count == 0:
                return {
                    "total_questions_answered": 0,
                    "average_score": 0.0,
                    "scores_by_date": [],
                    "knowledge_base_progress": []
                }
            
            # Average score
            avg_score_result = (
                db.query(func.avg(self.model.score))
                .filter(self.model.user_id == user_id, self.model.score.isnot(None))
                .scalar()
            )
            avg_score = float(avg_score_result) if avg_score_result else 0.0
            
            # Scores by date (last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            scores_by_date = (
                db.query(
                    func.date(self.model.answered_at).label('date'),
                    func.avg(self.model.score).label('avg_score'),
                    func.count(self.model.id).label('count')
                )
                .filter(
                    self.model.user_id == user_id,
                    self.model.answered_at >= thirty_days_ago,
                    self.model.score.isnot(None)
                )
                .group_by(func.date(self.model.answered_at))
                .order_by(func.date(self.model.answered_at))
                .all()
            )
            
            # Knowledge base progress
            kb_progress = (
                db.query(
                    KnowledgeBase.name,
                    func.count(self.model.id).label('total_answered'),
                    func.avg(self.model.score).label('avg_score')
                )
                .join(Question)
                .join(Document)
                .join(KnowledgeBase)
                .filter(self.model.user_id == user_id)
                .group_by(KnowledgeBase.id, KnowledgeBase.name)
                .all()
            )
            
            return {
                "total_questions_answered": total_count,
                "average_score": round(avg_score, 2),
                "scores_by_date": [
                    {
                        "date": str(row.date),
                        "avg_score": round(float(row.avg_score), 2),
                        "count": row.count
                    }
                    for row in scores_by_date
                ],
                "knowledge_base_progress": [
                    {
                        "knowledge_base_name": row.name,
                        "total_answered": row.total_answered,
                        "avg_score": round(float(row.avg_score), 2) if row.avg_score else 0.0
                    }
                    for row in kb_progress
                ]
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting statistics for user {user_id}: {e}")
            raise
    
    def search_records(
        self,
        db: Session,
        user_id: int,
        query: str = None,
        knowledge_base_id: int = None,
        document_id: int = None,
        score_min: float = None,
        score_max: float = None,
        date_from: datetime = None,
        date_to: datetime = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "answered_at",
        sort_order: str = "desc"
    ) -> List[tuple]:
        """Search answer records with filters"""
        try:
            # Base query with explicit joins
            base_query = (
                db.query(
                    self.model,
                    Question.question_text,
                    Document.filename,
                    KnowledgeBase.name.label('knowledge_base_name')
                )
                .select_from(self.model)
                .join(Question, self.model.question_id == Question.id)
                .join(Document, Question.document_id == Document.id)
                .join(KnowledgeBase, Document.knowledge_base_id == KnowledgeBase.id)
                .filter(self.model.user_id == user_id)
            )
            
            # Apply filters
            if query:
                base_query = base_query.filter(
                    Question.question_text.contains(query) |
                    self.model.user_answer.contains(query) |
                    self.model.feedback.contains(query)
                )
            
            if knowledge_base_id:
                base_query = base_query.filter(Document.knowledge_base_id == knowledge_base_id)
            
            if document_id:
                base_query = base_query.filter(Question.document_id == document_id)
            
            if score_min is not None:
                base_query = base_query.filter(self.model.score >= score_min)
            
            if score_max is not None:
                base_query = base_query.filter(self.model.score <= score_max)
            
            if date_from:
                base_query = base_query.filter(self.model.answered_at >= date_from)
            
            if date_to:
                base_query = base_query.filter(self.model.answered_at <= date_to)
            
            # Apply sorting
            sort_field = getattr(self.model, sort_by, self.model.answered_at)
            if sort_order.lower() == "desc":
                base_query = base_query.order_by(sort_field.desc())
            else:
                base_query = base_query.order_by(sort_field.asc())
            
            return base_query.offset(skip).limit(limit).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error searching answer records for user {user_id}: {e}")
            raise
    
    def bulk_delete(self, db: Session, user_id: int, record_ids: List[int]) -> int:
        """Bulk delete answer records for a user"""
        try:
            deleted_count = (
                db.query(self.model)
                .filter(
                    self.model.user_id == user_id,
                    self.model.id.in_(record_ids)
                )
                .delete(synchronize_session=False)
            )
            db.commit()
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Error bulk deleting answer records for user {user_id}: {e}")
            db.rollback()
            raise
            db.rollback()
            raise


class CRUDReviewRecord(CRUDBase[ReviewRecord, None, None]):
    """CRUD operations for ReviewRecord"""
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ReviewRecord]:
        """Get review records by user ID with pagination"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.user_id == user_id)
                .order_by(self.model.next_review.asc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting review records for user {user_id}: {e}")
            raise
    
    def get_due_reviews(
        self, 
        db: Session, 
        user_id: int, 
        limit: int = 50
    ) -> List[ReviewRecord]:
        """Get reviews that are due for a user"""
        try:
            from datetime import datetime
            now = datetime.now()
            
            return (
                db.query(self.model)
                .filter(
                    self.model.user_id == user_id,
                    self.model.next_review <= now
                )
                .order_by(self.model.next_review.asc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting due reviews for user {user_id}: {e}")
            raise
    
    def get_by_content(
        self, 
        db: Session, 
        user_id: int,
        content_id: int,
        content_type: str
    ) -> Optional[ReviewRecord]:
        """Get review record by content ID and type"""
        try:
            return (
                db.query(self.model)
                .filter(
                    self.model.user_id == user_id,
                    self.model.content_id == content_id,
                    self.model.content_type == content_type
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting review record for content {content_id}: {e}")
            raise
    
    def update_review_schedule(
        self,
        db: Session,
        review_record: ReviewRecord,
        quality: int  # 0-5 quality rating
    ) -> ReviewRecord:
        """Update review schedule based on spaced repetition algorithm"""
        try:
            from datetime import datetime, timedelta
            
            # Simple spaced repetition algorithm (similar to Anki)
            if quality < 3:
                # Reset if quality is poor
                review_record.interval_days = 1
                review_record.ease_factor = max(1.3, review_record.ease_factor - 0.2)
            else:
                # Increase interval based on ease factor
                if review_record.review_count == 0:
                    review_record.interval_days = 1
                elif review_record.review_count == 1:
                    review_record.interval_days = 6
                else:
                    review_record.interval_days = int(
                        review_record.interval_days * review_record.ease_factor
                    )
                
                # Adjust ease factor based on quality
                review_record.ease_factor = max(
                    1.3,
                    review_record.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
                )
            
            # Update timestamps
            review_record.last_reviewed = datetime.now()
            review_record.next_review = datetime.now() + timedelta(days=review_record.interval_days)
            review_record.review_count += 1
            
            db.commit()
            db.refresh(review_record)
            return review_record
            
        except SQLAlchemyError as e:
            logger.error(f"Error updating review schedule: {e}")
            db.rollback()
            raise


class CRUDKnowledgePoint(CRUDBase[KnowledgePoint, None, None]):
    """CRUD operations for KnowledgePoint"""
    
    def get_by_document(
        self, 
        db: Session, 
        document_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[KnowledgePoint]:
        """Get knowledge points by document ID with pagination"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.document_id == document_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting knowledge points for document {document_id}: {e}")
            raise
    
    def count_by_document(self, db: Session, document_id: int) -> int:
        """Count knowledge points by document ID"""
        try:
            return db.query(self.model).filter(self.model.document_id == document_id).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting knowledge points for document {document_id}: {e}")
            raise
    
    def count_by_knowledge_base(self, db: Session, knowledge_base_id: int) -> int:
        """Count knowledge points by knowledge base ID"""
        try:
            return (
                db.query(self.model)
                .join(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .count()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error counting knowledge points for knowledge base {knowledge_base_id}: {e}")
            raise
    
    def get_by_knowledge_base(
        self, 
        db: Session, 
        knowledge_base_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[KnowledgePoint]:
        """Get knowledge points by knowledge base ID through document relationship"""
        try:
            return (
                db.query(self.model)
                .join(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting knowledge points for knowledge base {knowledge_base_id}: {e}")
            raise


# Create instances
knowledge_base_crud = CRUDKnowledgeBase(KnowledgeBase)
document_crud = CRUDDocument(Document)
question_crud = CRUDQuestion(Question)
answer_record_crud = CRUDAnswerRecord(AnswerRecord)
review_record_crud = CRUDReviewRecord(ReviewRecord)
knowledge_point_crud = CRUDKnowledgePoint(KnowledgePoint)


class CRUDKnowledgePoint(CRUDBase[KnowledgePoint, None, None]):
    """CRUD operations for KnowledgePoint"""
    
    def get_by_document(
        self, 
        db: Session, 
        document_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[KnowledgePoint]:
        """Get knowledge points by document ID with pagination"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.document_id == document_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting knowledge points for document {document_id}: {e}")
            raise
    
    def count_by_document(self, db: Session, document_id: int) -> int:
        """Count knowledge points by document ID"""
        try:
            return db.query(self.model).filter(self.model.document_id == document_id).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting knowledge points for document {document_id}: {e}")
            raise
    
    def get_by_knowledge_base(
        self, 
        db: Session, 
        knowledge_base_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[KnowledgePoint]:
        """Get knowledge points by knowledge base ID through document relationship"""
        try:
            return (
                db.query(self.model)
                .join(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting knowledge points for knowledge base {knowledge_base_id}: {e}")
            raise
    
    def get_by_documents(
        self, 
        db: Session, 
        document_ids: List[int], 
        skip: int = 0, 
        limit: int = 1000
    ) -> List[KnowledgePoint]:
        """Get knowledge points by multiple document IDs"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.document_id.in_(document_ids))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting knowledge points for documents {document_ids}: {e}")
            raise


class CRUDLearningSet(CRUDBase[None, None, None]):
    """CRUD operations for LearningSet"""
    
    def __init__(self):
        from .models import LearningSet, LearningSetItem, LearningRecord
        self.model = LearningSet
        self.item_model = LearningSetItem
        self.record_model = LearningRecord
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Any]:
        """Get learning sets by user ID with pagination"""
        try:
            return (
                db.query(self.model)
                .filter(self.model.user_id == user_id)
                .order_by(self.model.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting learning sets for user {user_id}: {e}")
            raise
    
    def count_by_user(self, db: Session, user_id: int) -> int:
        """Count learning sets by user ID"""
        try:
            return db.query(self.model).filter(self.model.user_id == user_id).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting learning sets for user {user_id}: {e}")
            raise
    
    def create_with_documents(
        self, 
        db: Session, 
        *, 
        user_id: int,
        knowledge_base_id: int,
        name: str,
        description: str = None,
        document_ids: List[int]
    ) -> Any:
        """Create a learning set with knowledge points from specified documents"""
        try:
            # Create learning set
            learning_set = self.model(
                user_id=user_id,
                knowledge_base_id=knowledge_base_id,
                name=name,
                description=description
            )
            db.add(learning_set)
            db.flush()  # Get the ID without committing
            
            # Get knowledge points from specified documents
            knowledge_points = (
                db.query(KnowledgePoint)
                .filter(KnowledgePoint.document_id.in_(document_ids))
                .all()
            )
            
            # Create learning set items
            for kp in knowledge_points:
                item = self.item_model(
                    learning_set_id=learning_set.id,
                    knowledge_point_id=kp.id
                )
                db.add(item)
                
                # Create initial learning record
                record = self.record_model(
                    user_id=user_id,
                    knowledge_point_id=kp.id,
                    learning_set_id=learning_set.id,
                    mastery_level=0,  # Not learned
                    review_count=0,
                    ease_factor=2.5,
                    interval_days=1
                )
                db.add(record)
            
            db.commit()
            db.refresh(learning_set)
            return learning_set
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating learning set with documents: {e}")
            db.rollback()
            raise
    
    def get_with_statistics(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[tuple]:
        """Get learning sets with statistics"""
        try:
            # 简化查询，先获取基本信息，然后单独计算统计
            learning_sets = (
                db.query(self.model, KnowledgeBase.name.label('knowledge_base_name'))
                .join(KnowledgeBase, self.model.knowledge_base_id == KnowledgeBase.id)
                .filter(self.model.user_id == user_id)
                .order_by(self.model.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            
            results = []
            for ls, kb_name in learning_sets:
                # 计算总项目数
                total_items = (
                    db.query(func.count(self.item_model.id))
                    .filter(self.item_model.learning_set_id == ls.id)
                    .scalar() or 0
                )
                
                # 计算各种掌握程度的数量
                mastered_items = (
                    db.query(func.count(self.record_model.id))
                    .filter(
                        self.record_model.learning_set_id == ls.id,
                        self.record_model.user_id == user_id,
                        self.record_model.mastery_level == 2
                    )
                    .scalar() or 0
                )
                
                learning_items = (
                    db.query(func.count(self.record_model.id))
                    .filter(
                        self.record_model.learning_set_id == ls.id,
                        self.record_model.user_id == user_id,
                        self.record_model.mastery_level == 1
                    )
                    .scalar() or 0
                )
                
                new_items = (
                    db.query(func.count(self.record_model.id))
                    .filter(
                        self.record_model.learning_set_id == ls.id,
                        self.record_model.user_id == user_id,
                        self.record_model.mastery_level == 0
                    )
                    .scalar() or 0
                )
                
                results.append((ls, total_items, mastered_items, learning_items, new_items, kb_name))
            
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting learning sets with statistics for user {user_id}: {e}")
            raise
    
    def get_items_with_progress(
        self, 
        db: Session, 
        learning_set_id: int, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[tuple]:
        """Get learning set items with progress information"""
        try:
            return (
                db.query(
                    self.item_model,
                    KnowledgePoint,
                    self.record_model.mastery_level,
                    self.record_model.review_count,
                    self.record_model.next_review,
                    self.record_model.last_reviewed
                )
                .select_from(self.item_model)
                .join(KnowledgePoint, self.item_model.knowledge_point_id == KnowledgePoint.id)
                .outerjoin(self.record_model, 
                          (self.item_model.knowledge_point_id == self.record_model.knowledge_point_id) &
                          (self.item_model.learning_set_id == self.record_model.learning_set_id) &
                          (self.record_model.user_id == user_id))
                .filter(self.item_model.learning_set_id == learning_set_id)
                .order_by(self.item_model.added_at)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting items with progress for learning set {learning_set_id}: {e}")
            raise
    
    def get_due_items(
        self, 
        db: Session, 
        learning_set_id: int, 
        user_id: int
    ) -> List[tuple]:
        """Get knowledge points due for review in a learning set"""
        try:
            from datetime import datetime
            now = datetime.now()
            
            return (
                db.query(
                    KnowledgePoint,
                    self.record_model
                )
                .select_from(self.item_model)
                .join(KnowledgePoint, self.item_model.knowledge_point_id == KnowledgePoint.id)
                .join(self.record_model, 
                      (self.item_model.knowledge_point_id == self.record_model.knowledge_point_id) &
                      (self.item_model.learning_set_id == self.record_model.learning_set_id) &
                      (self.record_model.user_id == user_id))
                .filter(
                    self.item_model.learning_set_id == learning_set_id,
                    func.coalesce(self.record_model.next_review, now) <= now
                )
                .order_by(self.record_model.next_review.asc().nullsfirst())
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting due items for learning set {learning_set_id}: {e}")
            raise
    
    def delete_with_items(self, db: Session, learning_set_id: int, user_id: int) -> bool:
        """Delete a learning set and all its items and records"""
        try:
            # Verify ownership
            learning_set = (
                db.query(self.model)
                .filter(self.model.id == learning_set_id, self.model.user_id == user_id)
                .first()
            )
            
            if not learning_set:
                return False
            
            # Delete learning records
            db.query(self.record_model).filter(
                self.record_model.learning_set_id == learning_set_id,
                self.record_model.user_id == user_id
            ).delete()
            
            # Delete learning set items
            db.query(self.item_model).filter(
                self.item_model.learning_set_id == learning_set_id
            ).delete()
            
            # Delete learning set
            db.delete(learning_set)
            db.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Error deleting learning set {learning_set_id}: {e}")
            db.rollback()
            raise


class CRUDLearningRecord(CRUDBase[None, None, None]):
    """CRUD operations for LearningRecord"""
    
    def __init__(self):
        from .models import LearningRecord
        self.model = LearningRecord
    
    def get_or_create(
        self, 
        db: Session, 
        *, 
        user_id: int,
        knowledge_point_id: int,
        learning_set_id: int
    ) -> Any:
        """Get existing learning record or create a new one"""
        try:
            # Try to get existing record
            record = (
                db.query(self.model)
                .filter(
                    self.model.user_id == user_id,
                    self.model.knowledge_point_id == knowledge_point_id,
                    self.model.learning_set_id == learning_set_id
                )
                .first()
            )
            
            if record:
                return record
            
            # Create new record
            record = self.model(
                user_id=user_id,
                knowledge_point_id=knowledge_point_id,
                learning_set_id=learning_set_id,
                mastery_level=0,
                review_count=0,
                ease_factor=2.5,
                interval_days=1
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting or creating learning record: {e}")
            db.rollback()
            raise
    
    def update_mastery(
        self, 
        db: Session, 
        *, 
        user_id: int,
        knowledge_point_id: int,
        learning_set_id: int,
        mastery_level: int
    ) -> Any:
        """Update mastery level and calculate next review time using SuperMemo SM-2 algorithm"""
        try:
            from datetime import datetime
            from ..services.spaced_repetition_service import SpacedRepetitionService
            
            record = self.get_or_create(
                db=db,
                user_id=user_id,
                knowledge_point_id=knowledge_point_id,
                learning_set_id=learning_set_id
            )
            
            # Update mastery level and review count
            record.mastery_level = mastery_level
            record.review_count += 1
            record.last_reviewed = datetime.now()
            
            # Calculate next review time using SuperMemo SM-2 algorithm
            new_interval, new_ease_factor, next_review = SpacedRepetitionService.calculate_next_review(
                mastery_level=mastery_level,
                current_ease_factor=record.ease_factor,
                current_interval=record.interval_days,
                review_count=record.review_count - 1  # Subtract 1 because we already incremented
            )
            
            # Update record with new values
            record.interval_days = new_interval
            record.ease_factor = new_ease_factor
            record.next_review = next_review
            
            db.commit()
            db.refresh(record)
            return record
            
        except SQLAlchemyError as e:
            logger.error(f"Error updating mastery for learning record: {e}")
            db.rollback()
            raise
    
    def get_due_for_review(
        self, 
        db: Session, 
        user_id: int, 
        learning_set_id: int = None,
        limit: int = 50
    ) -> List[Any]:
        """Get learning records due for review"""
        try:
            from datetime import datetime
            
            query = (
                db.query(self.model)
                .filter(
                    self.model.user_id == user_id,
                    func.coalesce(self.model.next_review, datetime.now()) <= datetime.now()
                )
            )
            
            if learning_set_id:
                query = query.filter(self.model.learning_set_id == learning_set_id)
            
            return (
                query
                .order_by(self.model.next_review.asc().nullsfirst())
                .limit(limit)
                .all()
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting due learning records for user {user_id}: {e}")
            raise
    
    def get_statistics(
        self, 
        db: Session, 
        user_id: int, 
        learning_set_id: int = None
    ) -> Dict[str, Any]:
        """Get learning statistics for a user"""
        try:
            query = db.query(self.model).filter(self.model.user_id == user_id)
            
            if learning_set_id:
                query = query.filter(self.model.learning_set_id == learning_set_id)
            
            # Count by mastery level
            mastery_counts = (
                query
                .with_entities(
                    self.model.mastery_level,
                    func.count(self.model.id).label('count')
                )
                .group_by(self.model.mastery_level)
                .all()
            )
            
            # Count due items
            from datetime import datetime
            due_count = (
                query
                .filter(func.coalesce(self.model.next_review, datetime.now()) <= datetime.now())
                .count()
            )
            
            # Total items
            total_count = query.count()
            
            # Build statistics
            stats = {
                "total_items": total_count,
                "due_items": due_count,
                "mastery_distribution": {
                    "not_learned": 0,
                    "learning": 0,
                    "mastered": 0
                }
            }
            
            mastery_labels = {0: "not_learned", 1: "learning", 2: "mastered"}
            for mastery_level, count in mastery_counts:
                label = mastery_labels.get(mastery_level, "unknown")
                stats["mastery_distribution"][label] = count
            
            return stats
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting learning statistics for user {user_id}: {e}")
            raise


# Create CRUD instances
knowledge_base_crud = CRUDKnowledgeBase(KnowledgeBase)
document_crud = CRUDDocument(Document)
question_crud = CRUDQuestion(Question)
answer_record_crud = CRUDAnswerRecord(AnswerRecord)
knowledge_point_crud = CRUDKnowledgePoint(KnowledgePoint)
learning_set_crud = CRUDLearningSet()
learning_record_crud = CRUDLearningRecord()