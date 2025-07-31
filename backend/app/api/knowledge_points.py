"""
API endpoints for knowledge point management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.middleware import get_current_user
from ..models.database import get_db
from ..models.models import User
from ..services.knowledge_point_service import knowledge_point_service
from ..schemas.knowledge_points import KnowledgePointSearchRequest

router = APIRouter(prefix="/api/knowledge-points", tags=["knowledge-points"])


@router.post("/extract/document/{document_id}")
async def extract_knowledge_points_from_document(
    document_id: int,
    target_count: Optional[int] = Query(None, ge=1, le=100, description="Target number of knowledge points to extract"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Extract knowledge points from a specific document"""
    try:
        result = await knowledge_point_service.extract_knowledge_points_from_document(
            db=db,
            document_id=document_id,
            target_count=target_count
        )
        
        # Handle both old and new return formats
        if isinstance(result, dict) and "knowledge_points" in result:
            return result
        else:
            # Legacy format - convert to new format
            return {
                "success": True,
                "document_id": document_id,
                "knowledge_points": result,
                "count": len(result),
                "message": f"成功提取了 {len(result)} 个知识点"
            }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract knowledge points: {str(e)}")


@router.post("/extract/knowledge-base/{knowledge_base_id}")
async def extract_knowledge_points_from_knowledge_base(
    knowledge_base_id: int,
    target_count_per_document: Optional[int] = Query(None, ge=1, le=100, description="Target number of knowledge points per document"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Extract knowledge points from all documents in a knowledge base"""
    try:
        result = await knowledge_point_service.extract_knowledge_points_from_knowledge_base(
            db=db,
            knowledge_base_id=knowledge_base_id,
            target_count_per_document=target_count_per_document
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract knowledge points: {str(e)}")


@router.get("/")
async def get_knowledge_points(
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    knowledge_base_id: Optional[int] = Query(None, description="Filter by knowledge base ID"),
    importance_level: Optional[int] = Query(None, ge=1, le=5, description="Minimum importance level"),
    search_query: Optional[str] = Query(None, description="Search in title and content"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get knowledge points with filtering options"""
    try:
        knowledge_points = knowledge_point_service.get_knowledge_points(
            db=db,
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            importance_level=importance_level,
            search_query=search_query,
            skip=skip,
            limit=limit
        )
        
        return {
            "success": True,
            "knowledge_points": knowledge_points,
            "count": len(knowledge_points),
            "filters": {
                "document_id": document_id,
                "knowledge_base_id": knowledge_base_id,
                "importance_level": importance_level,
                "search_query": search_query
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge points: {str(e)}")


@router.get("/{kp_id}")
async def get_knowledge_point(
    kp_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get a specific knowledge point by ID"""
    try:
        knowledge_point = knowledge_point_service.get_knowledge_point_by_id(db=db, kp_id=kp_id)
        
        if not knowledge_point:
            raise HTTPException(status_code=404, detail="Knowledge point not found")
        
        return {
            "success": True,
            "knowledge_point": knowledge_point
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge point: {str(e)}")


@router.put("/{kp_id}")
async def update_knowledge_point(
    kp_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    importance_level: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update a knowledge point"""
    try:
        # Validate importance level
        if importance_level is not None and (importance_level < 1 or importance_level > 5):
            raise HTTPException(status_code=400, detail="Importance level must be between 1 and 5")
        
        knowledge_point = knowledge_point_service.update_knowledge_point(
            db=db,
            kp_id=kp_id,
            title=title,
            content=content,
            importance_level=importance_level
        )
        
        if not knowledge_point:
            raise HTTPException(status_code=404, detail="Knowledge point not found")
        
        return {
            "success": True,
            "knowledge_point": knowledge_point,
            "message": "Knowledge point updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update knowledge point: {str(e)}")


@router.delete("/{kp_id}")
async def delete_knowledge_point(
    kp_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete a knowledge point"""
    try:
        success = knowledge_point_service.delete_knowledge_point(db=db, kp_id=kp_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge point not found")
        
        return {
            "success": True,
            "message": "Knowledge point deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete knowledge point: {str(e)}")





@router.post("/search")
async def search_knowledge_points(
    search_request: KnowledgePointSearchRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Search knowledge points from existing knowledge points"""
    try:
        # 在已存在的知识点中搜索
        knowledge_points = knowledge_point_service.get_knowledge_points(
            db=db,
            knowledge_base_id=search_request.knowledge_base_id,
            document_id=search_request.document_id,
            search_query=search_request.query,
            skip=0,
            limit=search_request.n_results
        )
        
        # 转换为搜索结果格式
        results = []
        for kp_dict in knowledge_points:
            results.append({
                "content": kp_dict["content"],
                "metadata": {
                    "knowledge_point_id": kp_dict["id"],
                    "document_id": kp_dict["document_id"],
                    "title": kp_dict["title"],
                    "importance_level": kp_dict["importance_level"]
                },
                "id": str(kp_dict["id"])
            })
        
        return {
            "success": True,
            "query": search_request.query,
            "results": results,
            "count": len(results),
            "filters": {
                "knowledge_base_id": search_request.knowledge_base_id,
                "document_id": search_request.document_id,
                "n_results": search_request.n_results
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search knowledge points: {str(e)}")


@router.get("/statistics/overview")
async def get_knowledge_point_statistics(
    knowledge_base_id: Optional[int] = Query(None, description="Filter by knowledge base ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get statistics about knowledge points"""
    try:
        stats = knowledge_point_service.get_knowledge_point_statistics(
            db=db,
            knowledge_base_id=knowledge_base_id
        )
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/batch/extract")
async def batch_extract_knowledge_points(
    document_ids: List[int],
    force_regenerate: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Extract knowledge points from multiple documents"""
    try:
        if not document_ids:
            raise HTTPException(status_code=400, detail="Document IDs list cannot be empty")
        
        if len(document_ids) > 50:
            raise HTTPException(status_code=400, detail="Cannot process more than 50 documents at once")
        
        results = []
        total_kps = 0
        errors = []
        
        for document_id in document_ids:
            try:
                result = await knowledge_point_service.extract_knowledge_points_from_document(
                    db=db,
                    document_id=document_id
                )
                # Handle both old and new return formats
                if isinstance(result, dict) and "knowledge_points" in result:
                    kp_count = result["count"]
                else:
                    kp_count = len(result)
                
                results.append({
                    "document_id": document_id,
                    "knowledge_points_count": kp_count,
                    "success": True
                })
                total_kps += kp_count
            except Exception as e:
                errors.append({
                    "document_id": document_id,
                    "error": str(e)
                })
                results.append({
                    "document_id": document_id,
                    "knowledge_points_count": 0,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "processed_documents": len(document_ids),
            "successful_extractions": len([r for r in results if r["success"]]),
            "total_knowledge_points": total_kps,
            "results": results,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch extract knowledge points: {str(e)}")


@router.delete("/batch")
async def batch_delete_knowledge_points(
    kp_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete multiple knowledge points"""
    try:
        if not kp_ids:
            raise HTTPException(status_code=400, detail="Knowledge point IDs list cannot be empty")
        
        if len(kp_ids) > 100:
            raise HTTPException(status_code=400, detail="Cannot delete more than 100 knowledge points at once")
        
        deleted_count = 0
        errors = []
        
        for kp_id in kp_ids:
            try:
                success = knowledge_point_service.delete_knowledge_point(db=db, kp_id=kp_id)
                if success:
                    deleted_count += 1
                else:
                    errors.append(f"Knowledge point {kp_id} not found")
            except Exception as e:
                errors.append(f"Failed to delete knowledge point {kp_id}: {str(e)}")
        
        return {
            "success": True,
            "requested_deletions": len(kp_ids),
            "successful_deletions": deleted_count,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch delete knowledge points: {str(e)}")