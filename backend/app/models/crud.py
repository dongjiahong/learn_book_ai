"""
Base CRUD operations for database models
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
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


# Create instances
knowledge_base_crud = CRUDKnowledgeBase(KnowledgeBase)
document_crud = CRUDDocument(Document)
question_crud = CRUDQuestion(Question)