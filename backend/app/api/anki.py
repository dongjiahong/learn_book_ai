"""
Anki export API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import os
import tempfile
from datetime import datetime

from ..core.middleware import get_current_user
from ..models.database import get_db
from ..models.models import User, KnowledgeBase
from ..services.anki_service import anki_service


router = APIRouter(prefix="/api/anki", tags=["anki"])


class AnkiExportRequest(BaseModel):
    """Request model for Anki export"""
    deck_name: str
    knowledge_base_ids: Optional[List[int]] = None
    include_qa: bool = True
    include_kp: bool = True


class CustomAnkiExportRequest(BaseModel):
    """Request model for custom Anki export"""
    deck_name: str
    answer_record_ids: Optional[List[int]] = None
    knowledge_point_ids: Optional[List[int]] = None


class AnkiExportResponse(BaseModel):
    """Response model for Anki export"""
    export_id: str
    deck_name: str
    file_path: str
    created_at: datetime
    card_count: int


# In-memory storage for export files (in production, use Redis or database)
export_files = {}


@router.post("/export", response_model=AnkiExportResponse)
async def export_anki_deck(
    request: AnkiExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export Anki deck from user's learning data"""
    try:
        # Validate knowledge base access
        if request.knowledge_base_ids:
            kb_count = db.query(KnowledgeBase).filter(
                KnowledgeBase.id.in_(request.knowledge_base_ids),
                KnowledgeBase.user_id == current_user.id
            ).count()
            
            if kb_count != len(request.knowledge_base_ids):
                raise HTTPException(
                    status_code=403,
                    detail="Access denied to one or more knowledge bases"
                )
        
        # Generate deck
        file_path = anki_service.generate_deck_from_records(
            user_id=current_user.id,
            deck_name=request.deck_name,
            knowledge_base_ids=request.knowledge_base_ids,
            include_qa=request.include_qa,
            include_kp=request.include_kp,
            db=db
        )
        
        # Generate export ID
        export_id = f"export_{current_user.id}_{int(datetime.now().timestamp())}"
        
        # Store export info
        export_info = {
            "export_id": export_id,
            "deck_name": request.deck_name,
            "file_path": file_path,
            "created_at": datetime.now(),
            "user_id": current_user.id,
            "card_count": 0  # TODO: Calculate actual card count
        }
        
        export_files[export_id] = export_info
        
        return AnkiExportResponse(**export_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/export/knowledge-base/{knowledge_base_id}", response_model=AnkiExportResponse)
async def export_knowledge_base_deck(
    knowledge_base_id: int,
    include_qa: bool = True,
    include_kp: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export Anki deck from a specific knowledge base"""
    try:
        # Validate knowledge base access
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.user_id == current_user.id
        ).first()
        
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Generate deck
        file_path = anki_service.generate_deck_from_knowledge_base(
            user_id=current_user.id,
            knowledge_base_id=knowledge_base_id,
            include_qa=include_qa,
            include_kp=include_kp,
            db=db
        )
        
        # Generate export ID
        export_id = f"kb_export_{current_user.id}_{knowledge_base_id}_{int(datetime.now().timestamp())}"
        
        # Store export info
        export_info = {
            "export_id": export_id,
            "deck_name": f"RAG Learning - {kb.name}",
            "file_path": file_path,
            "created_at": datetime.now(),
            "user_id": current_user.id,
            "card_count": 0  # TODO: Calculate actual card count
        }
        
        export_files[export_id] = export_info
        
        return AnkiExportResponse(**export_info)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/export/custom", response_model=AnkiExportResponse)
async def export_custom_deck(
    request: CustomAnkiExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export custom Anki deck from specific records and knowledge points"""
    try:
        # Generate deck
        file_path = anki_service.generate_custom_deck(
            user_id=current_user.id,
            deck_name=request.deck_name,
            answer_record_ids=request.answer_record_ids,
            knowledge_point_ids=request.knowledge_point_ids,
            db=db
        )
        
        # Generate export ID
        export_id = f"custom_export_{current_user.id}_{int(datetime.now().timestamp())}"
        
        # Store export info
        export_info = {
            "export_id": export_id,
            "deck_name": request.deck_name,
            "file_path": file_path,
            "created_at": datetime.now(),
            "user_id": current_user.id,
            "card_count": 0  # TODO: Calculate actual card count
        }
        
        export_files[export_id] = export_info
        
        return AnkiExportResponse(**export_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/download/{export_id}")
async def download_anki_deck(
    export_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Download generated Anki deck file"""
    if export_id not in export_files:
        raise HTTPException(status_code=404, detail="Export not found")
    
    export_info = export_files[export_id]
    
    # Verify user access
    if export_info["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path = export_info["file_path"]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found")
    
    # Schedule file cleanup after download
    def cleanup_file():
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            # Also remove from temp directory if empty
            temp_dir = os.path.dirname(file_path)
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)
            # Remove from memory
            if export_id in export_files:
                del export_files[export_id]
        except Exception:
            pass  # Ignore cleanup errors
    
    background_tasks.add_task(cleanup_file)
    
    return FileResponse(
        path=file_path,
        filename=f"{export_info['deck_name'].replace(' ', '_')}.apkg",
        media_type="application/octet-stream"
    )


@router.get("/exports")
async def list_user_exports(
    current_user: User = Depends(get_current_user)
):
    """List user's recent exports"""
    user_exports = [
        {
            "export_id": export_id,
            "deck_name": info["deck_name"],
            "created_at": info["created_at"],
            "card_count": info["card_count"]
        }
        for export_id, info in export_files.items()
        if info["user_id"] == current_user.id
    ]
    
    # Sort by creation time, newest first
    user_exports.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"exports": user_exports}


@router.delete("/exports/{export_id}")
async def delete_export(
    export_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an export and its associated file"""
    if export_id not in export_files:
        raise HTTPException(status_code=404, detail="Export not found")
    
    export_info = export_files[export_id]
    
    # Verify user access
    if export_info["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Clean up file
    file_path = export_info["file_path"]
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        # Also remove from temp directory if empty
        temp_dir = os.path.dirname(file_path)
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)
    except Exception:
        pass  # Ignore cleanup errors
    
    # Remove from memory
    del export_files[export_id]
    
    return {"message": "Export deleted successfully"}