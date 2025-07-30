"""
Review API endpoints for spaced repetition learning
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from ..models.database import get_db
from ..core.middleware import get_current_user
from ..models.models import User
from ..services.spaced_repetition_service import SpacedRepetitionService
from ..services.notification_service import NotificationService


router = APIRouter(prefix="/api/review", tags=["review"])


class ReviewSubmission(BaseModel):
    """Model for review submission"""
    content_id: int
    content_type: str  # 'question' or 'knowledge_point'
    quality: int  # 0-5 rating of recall quality


class ReviewResponse(BaseModel):
    """Model for review response"""
    success: bool
    message: str
    next_review: str
    interval_days: int
    ease_factor: float


@router.get("/due")
async def get_due_reviews(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get items due for review"""
    try:
        service = SpacedRepetitionService(db)
        due_items = service.get_due_reviews(current_user.id, limit)
        return due_items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get due reviews: {str(e)}"
        )


@router.post("/complete")
async def complete_review(
    review_data: ReviewSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ReviewResponse:
    """Complete a review and update spaced repetition schedule"""
    try:
        # Validate quality rating
        if not 0 <= review_data.quality <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quality rating must be between 0 and 5"
            )
        
        # Validate content type
        if review_data.content_type not in ['question', 'knowledge_point']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content type must be 'question' or 'knowledge_point'"
            )
        
        service = SpacedRepetitionService(db)
        updated_record = service.update_review_record(
            current_user.id,
            review_data.content_id,
            review_data.content_type,
            review_data.quality
        )
        
        return ReviewResponse(
            success=True,
            message="Review completed successfully",
            next_review=updated_record.next_review.isoformat(),
            interval_days=updated_record.interval_days,
            ease_factor=updated_record.ease_factor
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete review: {str(e)}"
        )


@router.get("/statistics")
async def get_review_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get review statistics for the current user"""
    try:
        service = SpacedRepetitionService(db)
        stats = service.get_review_statistics(current_user.id)
        
        # Add learning streak
        streak = service.get_learning_streak(current_user.id)
        stats['learning_streak'] = streak
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review statistics: {str(e)}"
        )


@router.get("/upcoming")
async def get_upcoming_reviews(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """Get upcoming reviews for the next N days"""
    try:
        if days < 1 or days > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days must be between 1 and 30"
            )
        
        service = SpacedRepetitionService(db)
        upcoming = service.get_upcoming_reviews(current_user.id, days)
        return upcoming
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upcoming reviews: {str(e)}"
        )


class ScheduleRequest(BaseModel):
    """Model for scheduling request"""
    content_id: int
    content_type: str


@router.post("/schedule")
async def schedule_item_for_review(
    schedule_data: ScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Schedule a new item for spaced repetition"""
    try:
        # Validate content type
        if schedule_data.content_type not in ['question', 'knowledge_point']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content type must be 'question' or 'knowledge_point'"
            )
        
        service = SpacedRepetitionService(db)
        review_record = service.schedule_new_item(current_user.id, schedule_data.content_id, schedule_data.content_type)
        
        return {
            'success': True,
            'message': 'Item scheduled for review',
            'review_record_id': review_record.id,
            'next_review': review_record.next_review.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule item for review: {str(e)}"
        )


@router.get("/reminders")
async def get_review_reminders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get review reminders for the current user"""
    try:
        notification_service = NotificationService(db)
        reminders = notification_service.get_due_reminders(current_user.id)
        return reminders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review reminders: {str(e)}"
        )


@router.get("/daily-summary")
async def get_daily_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get daily learning summary"""
    try:
        notification_service = NotificationService(db)
        summary = notification_service.get_daily_summary(current_user.id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily summary: {str(e)}"
        )


@router.get("/weekly-summary")
async def get_weekly_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get weekly learning summary"""
    try:
        notification_service = NotificationService(db)
        summary = notification_service.get_weekly_summary(current_user.id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get weekly summary: {str(e)}"
        )