"""
Base CRUD operations for database models
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from .database import Base

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