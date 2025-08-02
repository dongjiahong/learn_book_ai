"""
API endpoints for RAG (Retrieval-Augmented Generation) functionality
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Dict, Any, Optional
import tempfile
import os
from pathlib import Path

from ..core.middleware import get_current_user
from ..services.rag_service import rag_service
from ..models.models import User

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/upload-documents")
async def upload_documents(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Upload and process documents for RAG"""
    try:
        temp_files = []
        
        # Save uploaded files to temporary directory
        for file in files:
            # Check file type
            allowed_extensions = {'.pdf', '.epub', '.txt', '.md'}
            file_extension = Path(file.filename).suffix.lower()
            
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_extension}. Allowed types: {', '.join(allowed_extensions)}"
                )
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_files.append(temp_file.name)
        
        # Process documents
        result = await rag_service.load_documents(temp_files)
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except Exception as e:
                print(f"Warning: Failed to delete temp file {temp_file}: {e}")
        
        return result
        
    except Exception as e:
        # Clean up temporary files in case of error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Failed to upload documents: {str(e)}")


@router.post("/load-documents")
async def load_documents(
    file_paths: List[str],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Load documents from file paths"""
    try:
        result = await rag_service.load_documents(file_paths)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load documents: {str(e)}")


@router.post("/query")
async def query_rag(
    query: str = Form(...),
    top_k: int = Form(default=5),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Query the RAG system"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if top_k < 1 or top_k > 20:
            raise HTTPException(status_code=400, detail="top_k must be between 1 and 20")
        
        result = await rag_service.query(query.strip(), top_k)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/similar-documents")
async def get_similar_documents(
    query: str = Form(...),
    top_k: int = Form(default=5),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get similar documents without generating response"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if top_k < 1 or top_k > 20:
            raise HTTPException(status_code=400, detail="top_k must be between 1 and 20")
        
        similar_docs = await rag_service.get_similar_documents(query.strip(), top_k)
        
        return {
            "success": True,
            "query": query.strip(),
            "documents": similar_docs,
            "count": len(similar_docs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get similar documents: {str(e)}")


@router.get("/stats")
async def get_index_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get statistics about the RAG index"""
    try:
        stats = await rag_service.get_index_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/clear")
async def clear_index(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Clear all documents from the RAG index"""
    try:
        success = await rag_service.clear_index()
        
        if success:
            return {
                "success": True,
                "message": "Index cleared successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear index")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear index: {str(e)}")


@router.post("/extract-knowledge-points")
async def extract_knowledge_points_from_documents(
    query: str = Form(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Extract knowledge points from retrieved documents"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Get similar documents first
        similar_docs = await rag_service.get_similar_documents(query.strip(), top_k=5)
        
        if not similar_docs:
            return {
                "success": False,
                "error": "No relevant documents found",
                "knowledge_points": []
            }
        
        # Combine document content
        content = "\n\n".join([doc["content"] for doc in similar_docs])
        
        # Import model service to extract knowledge points
        from ..services.model_service import model_service
        knowledge_points = await model_service.extract_knowledge_points(content)
        
        return {
            "success": True,
            "knowledge_points": knowledge_points,
            "source_documents": len(similar_docs),
            "query": query.strip()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract knowledge points: {str(e)}")