"""
API endpoints for learning record management
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.middleware import get_current_user
from ..models.database import get_db
from ..models.crud import answer_record_crud, review_record_crud, question_crud
from ..models.models import AnswerRecord, ReviewRecord
from ..models.models import User
from ..schemas.learning import (
    AnswerRecordCreate,
    AnswerRecordUpdate,
    AnswerRecordResponse,
    ReviewRecordCreate,
    ReviewRecordUpdate,
    ReviewRecordResponse,
    LearningRecordFilter,
    LearningStatistics,
    LearningProgressResponse,
    BulkDeleteRequest,
    LearningRecordSearchRequest,
    ContentType
)

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.post("/answer-records", response_model=AnswerRecordResponse)
async def create_answer_record(
    record_data: AnswerRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new answer record"""
    try:
        # Verify question exists
        question = question_crud.get(db, record_data.question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Create answer record
        record_dict = record_data.dict()
        record_dict["user_id"] = current_user.id
        record_dict["answered_at"] = datetime.now()
        
        answer_record = answer_record_crud.create_with_dict(db, obj_in=record_dict)
        
        # Get record with details for response
        record_with_details = answer_record_crud.get_with_details(
            db, current_user.id, skip=0, limit=1
        )
        
        if record_with_details:
            record, question_text, filename, kb_name = record_with_details[0]
            response = AnswerRecordResponse.from_orm(record)
            response.question_text = question_text
            response.document_filename = filename
            response.knowledge_base_name = kb_name
            return response
        
        return AnswerRecordResponse.from_orm(answer_record)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create answer record: {str(e)}")


@router.get("/answer-records", response_model=List[AnswerRecordResponse])
async def get_answer_records(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    knowledge_base_id: Optional[int] = Query(None, description="Filter by knowledge base"),
    document_id: Optional[int] = Query(None, description="Filter by document"),
    score_min: Optional[float] = Query(None, ge=0, le=10, description="Minimum score filter"),
    score_max: Optional[float] = Query(None, ge=0, le=10, description="Maximum score filter"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get answer records with optional filters"""
    try:
        if knowledge_base_id:
            records_with_details = answer_record_crud.get_by_knowledge_base(
                db, current_user.id, knowledge_base_id, skip, limit
            )
            # Convert to tuples format for consistency
            records_with_details = [
                (record, record.question.question_text, 
                 record.question.document.filename, 
                 record.question.document.knowledge_base.name)
                for record in records_with_details
            ]
        else:
            # Use search with filters
            records_with_details = answer_record_crud.search_records(
                db=db,
                user_id=current_user.id,
                document_id=document_id,
                score_min=score_min,
                score_max=score_max,
                date_from=date_from,
                date_to=date_to,
                skip=skip,
                limit=limit
            )
        
        # Convert to response format
        response_records = []
        for record, question_text, filename, kb_name in records_with_details:
            response = AnswerRecordResponse.from_orm(record)
            response.question_text = question_text
            response.document_filename = filename
            response.knowledge_base_name = kb_name
            response_records.append(response)
        
        return response_records
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get answer records: {str(e)}")


@router.get("/answer-records/{record_id}", response_model=AnswerRecordResponse)
async def get_answer_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific answer record"""
    try:
        record = answer_record_crud.get(db, record_id)
        if not record or record.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Answer record not found")
        
        # Get with details
        records_with_details = answer_record_crud.get_with_details(
            db, current_user.id, skip=0, limit=1000  # Get all to find the specific one
        )
        
        for record_detail, question_text, filename, kb_name in records_with_details:
            if record_detail.id == record_id:
                response = AnswerRecordResponse.from_orm(record_detail)
                response.question_text = question_text
                response.document_filename = filename
                response.knowledge_base_name = kb_name
                return response
        
        return AnswerRecordResponse.from_orm(record)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get answer record: {str(e)}")


@router.put("/answer-records/{record_id}", response_model=AnswerRecordResponse)
async def update_answer_record(
    record_id: int,
    record_update: AnswerRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an answer record"""
    try:
        record = answer_record_crud.get(db, record_id)
        if not record or record.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Answer record not found")
        
        updated_record = answer_record_crud.update(
            db, db_obj=record, obj_in=record_update.dict(exclude_unset=True)
        )
        
        return AnswerRecordResponse.from_orm(updated_record)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update answer record: {str(e)}")


@router.delete("/answer-records/{record_id}")
async def delete_answer_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an answer record"""
    try:
        record = answer_record_crud.get(db, record_id)
        if not record or record.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Answer record not found")
        
        answer_record_crud.delete(db, id=record_id)
        return {"message": "Answer record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete answer record: {str(e)}")


@router.post("/answer-records/bulk-delete")
async def bulk_delete_answer_records(
    delete_request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk delete answer records"""
    try:
        deleted_count = answer_record_crud.bulk_delete(
            db, current_user.id, delete_request.record_ids
        )
        return {
            "message": f"Successfully deleted {deleted_count} answer records",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete records: {str(e)}")


@router.post("/answer-records/search", response_model=List[AnswerRecordResponse])
async def search_answer_records(
    search_request: LearningRecordSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search answer records with advanced filters"""
    try:
        filters = search_request.filters or LearningRecordFilter()
        
        records_with_details = answer_record_crud.search_records(
            db=db,
            user_id=current_user.id,
            query=search_request.query,
            knowledge_base_id=filters.knowledge_base_id,
            document_id=filters.document_id,
            score_min=filters.score_min,
            score_max=filters.score_max,
            date_from=filters.date_from,
            date_to=filters.date_to,
            skip=search_request.skip,
            limit=search_request.limit,
            sort_by=search_request.sort_by,
            sort_order=search_request.sort_order
        )
        
        # Convert to response format
        response_records = []
        for record, question_text, filename, kb_name in records_with_details:
            response = AnswerRecordResponse.from_orm(record)
            response.question_text = question_text
            response.document_filename = filename
            response.knowledge_base_name = kb_name
            response_records.append(response)
        
        return response_records
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search answer records: {str(e)}")


@router.get("/statistics", response_model=LearningStatistics)
async def get_learning_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get learning statistics for the current user"""
    try:
        stats = answer_record_crud.get_statistics(db, current_user.id)
        return LearningStatistics(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning statistics: {str(e)}")


@router.get("/progress", response_model=LearningProgressResponse)
async def get_learning_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive learning progress for the current user"""
    try:
        # Get statistics
        stats = answer_record_crud.get_statistics(db, current_user.id)
        
        # Get due reviews
        due_reviews = review_record_crud.get_due_reviews(db, current_user.id, limit=10)
        due_review_responses = [ReviewRecordResponse.from_orm(review) for review in due_reviews]
        
        # Get recent records
        recent_records_with_details = answer_record_crud.get_with_details(
            db, current_user.id, skip=0, limit=5
        )
        
        recent_record_responses = []
        for record, question_text, filename, kb_name in recent_records_with_details:
            response = AnswerRecordResponse.from_orm(record)
            response.question_text = question_text
            response.document_filename = filename
            response.knowledge_base_name = kb_name
            recent_record_responses.append(response)
        
        return LearningProgressResponse(
            user_id=current_user.id,
            statistics=LearningStatistics(**stats),
            due_reviews=due_review_responses,
            recent_records=recent_record_responses
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning progress: {str(e)}")


# Review Record endpoints
@router.post("/review-records", response_model=ReviewRecordResponse)
async def create_review_record(
    record_data: ReviewRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new review record"""
    try:
        # Check if review record already exists
        existing_record = review_record_crud.get_by_content(
            db, current_user.id, record_data.content_id, record_data.content_type
        )
        
        if existing_record:
            raise HTTPException(status_code=400, detail="Review record already exists for this content")
        
        # Create review record
        record_dict = record_data.dict()
        record_dict["user_id"] = current_user.id
        record_dict["last_reviewed"] = datetime.now()
        
        from datetime import timedelta
        record_dict["next_review"] = datetime.now() + timedelta(days=record_dict["interval_days"])
        
        review_record = review_record_crud.create_with_dict(db, obj_in=record_dict)
        
        return ReviewRecordResponse.from_orm(review_record)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create review record: {str(e)}")


@router.get("/review-records", response_model=List[ReviewRecordResponse])
async def get_review_records(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get review records"""
    try:
        records = review_record_crud.get_by_user(db, current_user.id, skip, limit)
        
        if content_type:
            records = [r for r in records if r.content_type == content_type]
        
        return [ReviewRecordResponse.from_orm(record) for record in records]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get review records: {str(e)}")


@router.get("/review-records/due", response_model=List[ReviewRecordResponse])
async def get_due_reviews(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reviews that are due"""
    try:
        due_reviews = review_record_crud.get_due_reviews(db, current_user.id, limit)
        return [ReviewRecordResponse.from_orm(record) for record in due_reviews]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get due reviews: {str(e)}")


@router.put("/review-records/{record_id}/complete", response_model=ReviewRecordResponse)
async def complete_review(
    record_id: int,
    quality: int = Query(..., ge=0, le=5, description="Quality rating (0-5)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete a review and update the schedule"""
    try:
        record = review_record_crud.get(db, record_id)
        if not record or record.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Review record not found")
        
        updated_record = review_record_crud.update_review_schedule(db, record, quality)
        
        return ReviewRecordResponse.from_orm(updated_record)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete review: {str(e)}")


@router.put("/review-records/{record_id}", response_model=ReviewRecordResponse)
async def update_review_record(
    record_id: int,
    record_update: ReviewRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a review record"""
    try:
        record = review_record_crud.get(db, record_id)
        if not record or record.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Review record not found")
        
        updated_record = review_record_crud.update(
            db, db_obj=record, obj_in=record_update.dict(exclude_unset=True)
        )
        
        return ReviewRecordResponse.from_orm(updated_record)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update review record: {str(e)}")


@router.delete("/review-records/{record_id}")
async def delete_review_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a review record"""
    try:
        record = review_record_crud.get(db, record_id)
        if not record or record.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Review record not found")
        
        review_record_crud.delete(db, id=record_id)
        return {"message": "Review record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete review record: {str(e)}")