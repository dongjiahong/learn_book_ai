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
        target_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract knowledge points from a specific document (incremental)
        
        Args:
            db: Database session
            document_id: ID of the document to process
            target_count: Target number of knowledge points to extract
            
        Returns:
            Dictionary with extraction results
        """
        try:
            # Get document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document with ID {document_id} not found")
            
            # 移除重复检查逻辑，每次都允许提取新的知识点
            
            # Read document content
            content = await self._read_document_content(document.file_path)
            if not content:
                raise ValueError(f"Could not read content from document {document.filename}")
            
            # Extract knowledge points using AI model
            extracted_kps = await model_service.extract_knowledge_points(content, target_count)
            
            # 不删除现有知识点，直接添加新的知识点
            
            # Save to database
            saved_kps = []
            for kp_data in extracted_kps:
                kp = KnowledgePoint(
                    document_id=document_id,
                    title=kp_data['title'],
                    question=kp_data.get('question'),  # 新增：支持question字段
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
            
            # 获取文档的所有知识点（包括之前的和新增的）
            all_kps = db.query(KnowledgePoint).filter(
                KnowledgePoint.document_id == document_id
            ).all()
            
            # Calculate extraction stages info
            extraction_stages = 1
            if target_count and target_count > 15:
                extraction_stages = (target_count + 14) // 15
            
            # Create success message
            if target_count:
                message = f"成功新增了 {len(saved_kps)} 个知识点（目标：{target_count}个），文档现共有 {len(all_kps)} 个知识点"
                if extraction_stages > 1:
                    message += f"，分{extraction_stages}个阶段完成"
            else:
                message = f"成功新增了 {len(saved_kps)} 个知识点，文档现共有 {len(all_kps)} 个知识点"
            
            # Return enriched response with success information
            return {
                "knowledge_points": kp_dicts,
                "count": len(saved_kps),
                "document_id": document_id,
                "success": True,
                "message": message,
                "total_requested": target_count,
                "extraction_stages": extraction_stages
            }
            
        except Exception as e:
            logger.error(f"Failed to extract knowledge points from document {document_id}: {e}")
            db.rollback()
            raise
    
    async def extract_knowledge_points_from_knowledge_base(
        self, 
        db: Session, 
        knowledge_base_id: int,
        target_count_per_document: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract knowledge points from all documents in a knowledge base (incremental)
        
        Args:
            db: Database session
            knowledge_base_id: ID of the knowledge base
            target_count_per_document: Target number of knowledge points per document
            
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
                    result = await self.extract_knowledge_points_from_document(
                        db, document.id, target_count_per_document
                    )
                    # Handle both old and new return formats
                    if isinstance(result, dict) and "knowledge_points" in result:
                        total_kps += result["count"]
                    else:
                        total_kps += len(result)
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
            
            # Order by creation date (newest first), then by importance
            query = query.order_by(
                KnowledgePoint.created_at.desc(),
                KnowledgePoint.importance_level.desc()
            )
            
            # Apply pagination
            knowledge_points = query.offset(skip).limit(limit).all()
            
            return [self._knowledge_point_to_dict(kp) for kp in knowledge_points]
            
        except Exception as e:
            logger.error(f"Failed to get knowledge points: {e}")
            raise
    
    def get_knowledge_points_count(
        self,
        db: Session,
        document_id: Optional[int] = None,
        knowledge_base_id: Optional[int] = None,
        importance_level: Optional[int] = None,
        search_query: Optional[str] = None
    ) -> int:
        """
        Get total count of knowledge points with filtering options
        
        Args:
            db: Database session
            document_id: Filter by document ID
            knowledge_base_id: Filter by knowledge base ID
            importance_level: Filter by minimum importance level
            search_query: Search in title and content
            
        Returns:
            Total count of knowledge points matching the filters
        """
        try:
            query = db.query(KnowledgePoint)
            
            # Apply filters (same as get_knowledge_points)
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
            
            return query.count()
            
        except Exception as e:
            logger.error(f"Failed to get knowledge points count: {e}")
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
        question: Optional[str] = None,
        content: Optional[str] = None,
        importance_level: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a knowledge point
        
        Args:
            db: Database session
            kp_id: Knowledge point ID
            title: New title (optional)
            question: New question (optional)
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
            if question is not None:
                kp.question = question
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
                    level: count for level, count in importance_stats
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
            "question": kp.question,  # 新增：包含question字段
            "content": kp.content,
            "importance_level": kp.importance_level,
            "created_at": kp.created_at.isoformat() if kp.created_at else None
        }


# Global service instance
knowledge_point_service = KnowledgePointService()