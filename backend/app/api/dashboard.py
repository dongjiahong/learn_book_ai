"""
Dashboard API endpoints for getting overview statistics
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..core.middleware import get_current_user
from ..models.database import get_db
from ..models.models import User
from ..models.crud import knowledge_base_crud, document_crud, answer_record_crud
from ..services.spaced_repetition_service import SpacedRepetitionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive dashboard statistics for the current user"""
    try:
        # Get knowledge base count
        knowledge_base_count = knowledge_base_crud.count_by_user(db=db, user_id=current_user.id)
        
        # Get document count across all user's knowledge bases
        user_kbs = knowledge_base_crud.get_by_user(db=db, user_id=current_user.id)
        document_count = sum(
            document_crud.count_by_knowledge_base(db=db, knowledge_base_id=kb.id) 
            for kb in user_kbs
        )
        
        # Get learning statistics
        learning_stats = answer_record_crud.get_statistics(db, current_user.id)
        
        # Get review statistics
        review_service = SpacedRepetitionService(db)
        review_stats = review_service.get_review_statistics(current_user.id)
        
        # Calculate learning points (simple scoring system)
        learning_points = (
            learning_stats.get('total_questions_answered', 0) * 10 +
            int(learning_stats.get('average_score', 0) * 100) +
            review_stats.get('completed_today', 0) * 5
        )
        
        return {
            "knowledge_bases": knowledge_base_count,
            "documents": document_count,
            "learning_records": learning_stats.get('total_questions_answered', 0),
            "learning_points": learning_points,
            "recent_activity": learning_stats.get('recent_activity', [])[:5],  # Last 5 activities
            "review_stats": {
                "due_today": review_stats.get('due_today', 0),
                "completed_today": review_stats.get('completed_today', 0),
                "learning_streak": review_stats.get('learning_streak', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard statistics")