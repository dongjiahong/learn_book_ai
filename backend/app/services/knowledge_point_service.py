"""
Knowledge point extraction and management service
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.models import KnowledgePoint, Document, KnowledgeBase
from ..models.database import get_db
from ..services.model_service import model_service
from ..services.vector_store import get_vector_store
from ..services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class KnowledgePointService:
    """Service for managing knowledge point extraction and operations"""
    
    def __init__(self):
        self.vector_store = None
        self.document_processor = None
    
    def _get_vector_store(self):
        """Lazy initialization of vector store"""
        if self.vector_store is None:
            self.vector_store = get_vector_store()
        return self.vector_store
    
    def _get_document_processor(self):
        """Lazy initialization of document processor"""
        if self.document_processor is None:
            self.document_processor = DocumentProcessor()
        return self.document_processor
    
    async def extract_knowledge_points_from_document(
        self, 
        db: Session, 
        document_id: int,
        force_regenerate: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract knowledge points from a specific document
        
        Args:
            db: Database session
            document_id: ID of the document to process
            force_regenerate: Whether to regenerate existing knowledge points
            
        Returns:
            List of extracted knowledge points
        """
        try:
            # Get document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document with ID {document_id} not found")
            
            # Check if knowledge points already exist and not forcing regeneration
            if not force_regenerate:
                existing_kps = db.query(KnowledgePoint).filter(
                    KnowledgePoint.document_id == document_id
                ).all()
                if existing_kps:
                    logger.info(f"Knowledge points already exist for document {document_id}")
                    return [self._knowledge_point_to_dict(kp) for kp in existing_kps]
            
            # Read document content
            content = await self._read_document_content(document.file_path)
            if not content:
                raise ValueError(f"Could not read content from document {document.filename}")
            
            # Extract knowledge points using AI model
            extracted_kps = await model_service.extract_knowledge_points(content)
            
            # Save to database
            saved_kps = []
            for kp_data in extracted_kps:
                # Delete existing knowledge points if regenerating
                if force_regenerate:
                    db.query(KnowledgePoint).filter(
                        KnowledgePoint.document_id == document_id
                    ).delete()
                
                # Create new knowledge point
                kp = KnowledgePoint(
                    document_id=document_id,
                    title=kp_data['title'],
                    content=kp_data['content'],
                    importance_level=kp_data.get('importance_level', 1)
                )
                db.add(kp)
                db.flush()  # Get the ID
                saved_kps.append(kp)
            
            db.commit()
            
            # Add to vector store
            kp_dicts = [self._knowledge_point_to_dict(kp) for kp in saved_kps]
            self._get_vector_store().add_knowledge_points(kp_dicts)
            
            logger.info(f"Extracted and saved {len(saved_kps)} knowledge points for document {document_id}")
            return kp_dicts
            
        except Exception as e:
            logger.error(f"Failed to extract knowledge points from document {document_id}: {e}")
            db.rollback()
            raise
    
    async def extract_knowledge_points_from_knowledge_base(
        self, 
        db: Session, 
        knowledge_base_id: int,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Extract knowledge points from all documents in a knowledge base
        
        Args:
            db: Database session
            knowledge_base_id: ID of the knowledge base
            force_regenerate: Whether to regenerate existing knowledge points
            
        Returns:
            Summary of extraction results
        """
        try:
            # Get all documents in the knowledge base
            documents = db.query(Document).filter(
                Document.knowledge_base_id == knowledge_base_id,
                Document.processed == True
            ).all()
            
            if not documents:
                return {
                    "success": False,
                    "message": "No processed documents found in knowledge base",
                    "total_documents": 0,
                    "total_knowledge_points": 0
                }
            
            total_kps = 0
            processed_docs = 0
            errors = []
            
            for document in documents:
                try:
                    kps = await self.extract_knowledge_points_from_document(
                        db, document.id, force_regenerate
                    )
                    total_kps += len(kps)
                    processed_docs += 1
                except Exception as e:
                    errors.append(f"Document {document.filename}: {str(e)}")
                    logger.error(f"Failed to process document {document.id}: {e}")
            
            return {
                "success": True,
                "total_documents": len(documents),
                "processed_documents": processed_docs,
                "total_knowledge_points": total_kps,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Failed to extract knowledge points from knowledge base {knowledge_base_id}: {e}")
            raise
    
    def get_knowledge_points(
        self,
        db: Session,
        document_id: Optional[int] = None,
        knowledge_base_id: Optional[int] = None,
        importance_level: Optional[int] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get knowledge points with filtering options
        
        Args:
            db: Database session
            document_id: Filter by document ID
            knowledge_base_id: Filter by knowledge base ID
            importance_level: Filter by minimum importance level
            search_query: Search in title and content
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of knowledge points
        """
        try:
            query = db.query(KnowledgePoint)
            
            # Apply filters
            if document_id:
                query = query.filter(KnowledgePoint.document_id == document_id)
            
            if knowledge_base_id:
                query = query.join(Document).filter(
                    Document.knowledge_base_id == knowledge_base_id
                )
            
            if importance_level:
                query = query.filter(KnowledgePoint.importance_level >= importance_level)
            
            if search_query:
                search_term = f"%{search_query}%"
                query = query.filter(
                    or_(
                        KnowledgePoint.title.ilike(search_term),
                        KnowledgePoint.content.ilike(search_term)
                    )
                )
            
            # Order by importance and creation date
            query = query.order_by(
                KnowledgePoint.importance_level.desc(),
                KnowledgePoint.created_at.desc()
            )
            
            # Apply pagination
            knowledge_points = query.offset(skip).limit(limit).all()
            
            return [self._knowledge_point_to_dict(kp) for kp in knowledge_points]
            
        except Exception as e:
            logger.error(f"Failed to get knowledge points: {e}")
            raise
    
    def get_knowledge_point_by_id(self, db: Session, kp_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific knowledge point by ID"""
        try:
            kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
            if kp:
                return self._knowledge_point_to_dict(kp)
            return None
        except Exception as e:
            logger.error(f"Failed to get knowledge point {kp_id}: {e}")
            raise
    
    def update_knowledge_point(
        self,
        db: Session,
        kp_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        importance_level: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a knowledge point
        
        Args:
            db: Database session
            kp_id: Knowledge point ID
            title: New title (optional)
            content: New content (optional)
            importance_level: New importance level (optional)
            
        Returns:
            Updated knowledge point or None if not found
        """
        try:
            kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
            if not kp:
                return None
            
            # Update fields
            if title is not None:
                kp.title = title
            if content is not None:
                kp.content = content
            if importance_level is not None:
                kp.importance_level = max(1, min(5, importance_level))  # Ensure 1-5 range
            
            db.commit()
            
            # Update vector store
            kp_dict = self._knowledge_point_to_dict(kp)
            self._get_vector_store().add_knowledge_points([kp_dict])
            
            logger.info(f"Updated knowledge point {kp_id}")
            return kp_dict
            
        except Exception as e:
            logger.error(f"Failed to update knowledge point {kp_id}: {e}")
            db.rollback()
            raise
    
    def delete_knowledge_point(self, db: Session, kp_id: int) -> bool:
        """
        Delete a knowledge point
        
        Args:
            db: Database session
            kp_id: Knowledge point ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
            if not kp:
                return False
            
            # Delete from vector store first
            try:
                self._get_vector_store().knowledge_point_collection.delete(ids=[f"kp_{kp_id}"])
            except Exception as e:
                logger.warning(f"Failed to delete knowledge point from vector store: {e}")
            
            # Delete from database
            db.delete(kp)
            db.commit()
            
            logger.info(f"Deleted knowledge point {kp_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge point {kp_id}: {e}")
            db.rollback()
            raise
    

    def search_knowledge_points(
        self,
        query: str,
        document_id: Optional[int] = None,
        importance_level: Optional[int] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge points using vector similarity
        
        Args:
            query: Search query
            document_id: Optional document filter
            importance_level: Optional minimum importance level
            n_results: Number of results to return
            
        Returns:
            List of similar knowledge points
        """
        try:
            results = self._get_vector_store().search_knowledge_points(
                query=query,
                document_id=document_id,
                importance_level=importance_level,
                n_results=n_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search knowledge points: {e}")
            raise
    
    def get_knowledge_point_statistics(
        self,
        db: Session,
        knowledge_base_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about knowledge points
        
        Args:
            db: Database session
            knowledge_base_id: Optional knowledge base filter
            
        Returns:
            Statistics dictionary
        """
        try:
            query = db.query(KnowledgePoint)
            
            if knowledge_base_id:
                query = query.join(Document).filter(
                    Document.knowledge_base_id == knowledge_base_id
                )
            
            # Total count
            total_count = query.count()
            
            # Count by importance level
            importance_stats = (
                query.with_entities(
                    KnowledgePoint.importance_level,
                    func.count(KnowledgePoint.id).label('count')
                )
                .group_by(KnowledgePoint.importance_level)
                .all()
            )
            
            # Count by document
            document_stats = (
                query.join(Document)
                .with_entities(
                    Document.filename,
                    func.count(KnowledgePoint.id).label('count')
                )
                .group_by(Document.id, Document.filename)
                .order_by(func.count(KnowledgePoint.id).desc())
                .limit(10)
                .all()
            )
            
            return {
                "total_knowledge_points": total_count,
                "by_importance_level": {
                    str(level): count for level, count in importance_stats
                },
                "top_documents": [
                    {"filename": filename, "count": count}
                    for filename, count in document_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get knowledge point statistics: {e}")
            raise
    
    async def _read_document_content(self, file_path: str) -> str:
        """Read content from document file"""
        try:
            return await self._get_document_processor().extract_text_from_file(file_path)
        except Exception as e:
            logger.error(f"Failed to read document content from {file_path}: {e}")
            return ""
    
    def _knowledge_point_to_dict(self, kp: KnowledgePoint) -> Dict[str, Any]:
        """Convert KnowledgePoint model to dictionary"""
        return {
            "id": kp.id,
            "document_id": kp.document_id,
            "title": kp.title,
            "content": kp.content,
            "importance_level": kp.importance_level,
            "created_at": kp.created_at.isoformat() if kp.created_at else None
        }


# Global service instance
knowledge_point_service = KnowledgePointService()