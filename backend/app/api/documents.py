"""
API endpoints for document and knowledge base management
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os
from pathlib import Path

from ..core.middleware import get_current_user
from ..models.database import get_db
from ..models.crud import knowledge_base_crud, document_crud, knowledge_point_crud
from ..models.models import User
from ..schemas.documents import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
    KnowledgeBaseDetailResponse, KnowledgeBaseListResponse,
    DocumentResponse, DocumentListResponse, DocumentUploadResponse,
    DocumentProcessingStatus, DocumentUpdate, KnowledgeBaseStatistics
)
from ..services.file_service import file_service
from ..services.document_processor import document_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["documents"])


# Knowledge Base endpoints
@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    knowledge_base: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new knowledge base"""
    try:
        logger.info(f"Creating knowledge base for user {current_user.id}: {knowledge_base.dict()}")
        db_knowledge_base = knowledge_base_crud.create_for_user(
            db=db, obj_in=knowledge_base, user_id=current_user.id
        )
        logger.info(f"Successfully created knowledge base with id {db_knowledge_base.id}")
        return db_knowledge_base
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create knowledge base: {str(e)}")


@router.get("/knowledge-bases", response_model=KnowledgeBaseListResponse)
async def get_knowledge_bases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's knowledge bases with pagination and statistics"""
    try:
        # Get knowledge bases with document and knowledge point statistics
        kb_with_stats = knowledge_base_crud.get_with_statistics(
            db=db, user_id=current_user.id, skip=skip, limit=limit
        )
        
        # Convert to response format
        knowledge_bases = []
        for kb, doc_count, kp_count in kb_with_stats:
            kb_dict = kb.__dict__.copy()
            kb_dict['document_count'] = doc_count or 0
            kb_dict['knowledge_point_count'] = kp_count or 0
            knowledge_bases.append(KnowledgeBaseResponse(**kb_dict))
        
        total = knowledge_base_crud.count_by_user(db=db, user_id=current_user.id)
        
        return KnowledgeBaseListResponse(
            knowledge_bases=knowledge_bases,
            total=total,
            page=skip // limit + 1,
            page_size=limit
        )
    except Exception as e:
        logger.error(f"Error getting knowledge bases: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge bases")


@router.get("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseDetailResponse)
async def get_knowledge_base(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific knowledge base with its documents and knowledge point statistics"""
    try:
        # Get knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=knowledge_base_id)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Check ownership
        if knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
        
        # Get documents
        documents = document_crud.get_by_knowledge_base(db=db, knowledge_base_id=knowledge_base_id)
        
        # Get knowledge point count for each document
        documents_with_stats = []
        total_knowledge_points = 0
        for doc in documents:
            kp_count = knowledge_point_crud.count_by_document(db=db, document_id=doc.id)
            doc_dict = doc.__dict__.copy()
            doc_dict['knowledge_point_count'] = kp_count
            documents_with_stats.append(DocumentResponse(**doc_dict))
            total_knowledge_points += kp_count
        
        # Convert to response format
        kb_dict = knowledge_base.__dict__.copy()
        kb_dict['documents'] = documents_with_stats
        kb_dict['document_count'] = len(documents)
        kb_dict['knowledge_point_count'] = total_knowledge_points
        
        return KnowledgeBaseDetailResponse(**kb_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge base {knowledge_base_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge base")


@router.get("/knowledge-bases/{knowledge_base_id}/statistics", response_model=KnowledgeBaseStatistics)
async def get_knowledge_base_statistics(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a knowledge base"""
    try:
        # Get knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=knowledge_base_id)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Check ownership
        if knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
        
        # Get statistics
        stats = knowledge_base_crud.get_statistics(db=db, knowledge_base_id=knowledge_base_id)
        
        return KnowledgeBaseStatistics(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting statistics for knowledge base {knowledge_base_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge base statistics")


@router.put("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    knowledge_base_id: int,
    knowledge_base_update: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a knowledge base"""
    try:
        # Get knowledge base
        db_knowledge_base = knowledge_base_crud.get(db=db, id=knowledge_base_id)
        if not db_knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Check ownership
        if db_knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this knowledge base")
        
        # Update
        updated_kb = knowledge_base_crud.update(
            db=db, db_obj=db_knowledge_base, obj_in=knowledge_base_update
        )
        return updated_kb
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating knowledge base {knowledge_base_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update knowledge base")


@router.delete("/knowledge-bases/{knowledge_base_id}")
async def delete_knowledge_base(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a knowledge base and all its documents"""
    try:
        # Get knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=knowledge_base_id)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Check ownership
        if knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this knowledge base")
        
        # Get all documents to delete their files
        documents = document_crud.get_by_knowledge_base(db=db, knowledge_base_id=knowledge_base_id)
        
        # Delete files from disk
        for document in documents:
            file_service.delete_file(document.file_path)
        
        # Delete knowledge base (cascade will delete documents)
        deleted_kb = knowledge_base_crud.delete(db=db, id=knowledge_base_id)
        
        if deleted_kb:
            # Cleanup empty directories
            file_service.cleanup_empty_directories()
            return {"message": "Knowledge base deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge base {knowledge_base_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete knowledge base")


# Document endpoints
@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document to a knowledge base"""
    try:
        # Verify knowledge base exists and user owns it
        knowledge_base = knowledge_base_crud.get(db=db, id=knowledge_base_id)
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        if knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to upload to this knowledge base")
        
        # Save file
        file_info = await file_service.save_file(file, knowledge_base_id)
        
        if not file_info['success']:
            raise HTTPException(status_code=400, detail="Failed to save file")
        
        # Create document record
        document = document_crud.create_with_file_info(
            db=db,
            knowledge_base_id=knowledge_base_id,
            filename=file_info['original_filename'],
            file_path=file_info['file_path'],
            file_type=file_info['file_type'],
            file_size=file_info['file_size']
        )
        
        # Add document to processing queue
        document_processor.add_document(
            document_id=document.id,
            file_path=document.file_path,
            knowledge_base_id=knowledge_base_id
        )
        
        return DocumentUploadResponse(
            success=True,
            message="Document uploaded successfully and queued for processing",
            document=DocumentResponse(**document.__dict__)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    knowledge_base_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get documents, optionally filtered by knowledge base"""
    try:
        if knowledge_base_id:
            # Verify knowledge base exists and user owns it
            knowledge_base = knowledge_base_crud.get(db=db, id=knowledge_base_id)
            if not knowledge_base:
                raise HTTPException(status_code=404, detail="Knowledge base not found")
            
            if knowledge_base.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to access this knowledge base")
            
            # Get documents for specific knowledge base
            documents = document_crud.get_by_knowledge_base(
                db=db, knowledge_base_id=knowledge_base_id, skip=skip, limit=limit
            )
            total = document_crud.count_by_knowledge_base(db=db, knowledge_base_id=knowledge_base_id)
        else:
            # Get all user's documents
            documents = document_crud.get_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)
            # Count total documents for user (through knowledge base relationship)
            user_kbs = knowledge_base_crud.get_by_user(db=db, user_id=current_user.id)
            total = sum(document_crud.count_by_knowledge_base(db=db, knowledge_base_id=kb.id) for kb in user_kbs)
        
        return DocumentListResponse(
            documents=[DocumentResponse(**doc.__dict__) for doc in documents],
            total=total,
            page=skip // limit + 1,
            page_size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get documents")


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific document"""
    try:
        document = document_crud.get(db=db, id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership through knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=document.knowledge_base_id)
        if not knowledge_base or knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")
        
        return {
            "success": True,
            "document": DocumentResponse(**document.__dict__)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document")


@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a document"""
    try:
        document = document_crud.get(db=db, id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership through knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=document.knowledge_base_id)
        if not knowledge_base or knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this document")
        
        # Update document
        updated_document = document_crud.update(db=db, db_obj=document, obj_in=document_update)
        return DocumentResponse(**updated_document.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update document")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    try:
        document = document_crud.get(db=db, id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership through knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=document.knowledge_base_id)
        if not knowledge_base or knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")
        
        # Delete file from disk
        file_service.delete_file(document.file_path)
        
        # Delete document from database
        deleted_document = document_crud.delete(db=db, id=document_id)
        
        if deleted_document:
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get("/documents/{document_id}/processing-status", response_model=DocumentProcessingStatus)
async def get_document_processing_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document processing status"""
    try:
        document = document_crud.get(db=db, id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership through knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=document.knowledge_base_id)
        if not knowledge_base or knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")
        
        # Get processing status from document processor
        processing_task = document_processor.get_processing_status(document_id)
        
        if processing_task:
            return DocumentProcessingStatus(
                document_id=document.id,
                processed=document.processed,
                processing_progress=processing_task.progress,
                error_message=processing_task.error_message
            )
        else:
            # No processing task found, check database status
            return DocumentProcessingStatus(
                document_id=document.id,
                processed=document.processed,
                processing_progress=1.0 if document.processed else 0.0
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing status")


@router.get("/documents/{document_id}/preview")
async def preview_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview a document (download file)"""
    try:
        document = document_crud.get(db=db, id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership through knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=document.knowledge_base_id)
        if not knowledge_base or knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")
        
        # Check if file exists
        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Return file for download/preview
        return FileResponse(
            path=document.file_path,
            filename=document.filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview document")


@router.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document text content for preview (text files only)"""
    try:
        document = document_crud.get(db=db, id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership through knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=document.knowledge_base_id)
        if not knowledge_base or knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")
        
        # Only support text files for content preview
        if document.file_type not in ['txt', 'md']:
            raise HTTPException(
                status_code=400, 
                detail="Content preview only supported for text and markdown files"
            )
        
        # Check if file exists
        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Read file content
        try:
            with open(document.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(document.file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        return {
            "document_id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "content": content[:5000],  # Limit to first 5000 characters for preview
            "truncated": len(content) > 5000
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document content")

@router.post("/documents/{document_id}/process")
async def process_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger document processing"""
    try:
        document = document_crud.get(db=db, id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check ownership through knowledge base
        knowledge_base = knowledge_base_crud.get(db=db, id=document.knowledge_base_id)
        if not knowledge_base or knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to process this document")
        
        # Check if already processed
        if document.processed:
            return {"message": "Document is already processed"}
        
        # Add to processing queue
        success = document_processor.add_document(
            document_id=document.id,
            file_path=document.file_path,
            knowledge_base_id=document.knowledge_base_id
        )
        
        if success:
            return {"message": "Document added to processing queue"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add document to processing queue")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process document")


@router.get("/processing/queue-status")
async def get_processing_queue_status(
    current_user: User = Depends(get_current_user)
):
    """Get document processing queue status"""
    try:
        status = document_processor.get_queue_status()
        return status
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue status")