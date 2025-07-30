"""
API endpoints for answer evaluation and feedback
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..core.middleware import get_current_user
from ..models.database import get_db
from ..models.models import User, Question, KnowledgeBase, Document
from ..services.evaluation_service import evaluation_service

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class AnswerSubmission(BaseModel):
    """Model for answer submission"""
    question_id: int
    user_answer: str
    save_record: bool = True


class BatchAnswerSubmission(BaseModel):
    """Model for batch answer submission"""
    answers: List[Dict[str, Any]]


@router.post("/submit-answer")
async def submit_answer(
    submission: AnswerSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Submit and evaluate a single answer"""
    try:
        # Verify question exists and user has access
        question = (
            db.query(Question)
            .join(Document)
            .join(KnowledgeBase)
            .filter(
                Question.id == submission.question_id,
                KnowledgeBase.user_id == current_user.id
            )
            .first()
        )
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found or access denied")
        
        # Evaluate answer
        result = await evaluation_service.evaluate_answer(
            db=db,
            user_id=current_user.id,
            question_id=submission.question_id,
            user_answer=submission.user_answer,
            save_record=submission.save_record
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Evaluation failed'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.post("/batch-submit")
async def batch_submit_answers(
    submission: BatchAnswerSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Submit and evaluate multiple answers in batch"""
    try:
        # Validate all questions belong to user
        question_ids = [answer.get('question_id') for answer in submission.answers if answer.get('question_id')]
        
        if not question_ids:
            raise HTTPException(status_code=400, detail="No valid question IDs provided")
        
        accessible_questions = (
            db.query(Question.id)
            .join(Document)
            .join(KnowledgeBase)
            .filter(
                Question.id.in_(question_ids),
                KnowledgeBase.user_id == current_user.id
            )
            .all()
        )
        
        accessible_ids = {q.id for q in accessible_questions}
        
        # Filter answers to only include accessible questions
        valid_answers = [
            answer for answer in submission.answers
            if answer.get('question_id') in accessible_ids
        ]
        
        if not valid_answers:
            raise HTTPException(status_code=403, detail="No accessible questions found")
        
        # Batch evaluate
        result = await evaluation_service.batch_evaluate_answers(
            db=db,
            user_id=current_user.id,
            answers=valid_answers
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch submit answers: {str(e)}")


@router.get("/records")
async def get_answer_records(
    question_id: Optional[int] = Query(default=None),
    knowledge_base_id: Optional[int] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get answer records for the current user"""
    try:
        # Verify knowledge base access if specified
        if knowledge_base_id:
            kb = db.query(KnowledgeBase).filter(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBase.user_id == current_user.id
            ).first()
            
            if not kb:
                raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Verify question access if specified
        if question_id:
            question = (
                db.query(Question)
                .join(Document)
                .join(KnowledgeBase)
                .filter(
                    Question.id == question_id,
                    KnowledgeBase.user_id == current_user.id
                )
                .first()
            )
            
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")
        
        # Get records
        records = await evaluation_service.get_answer_records(
            db=db,
            user_id=current_user.id,
            question_id=question_id,
            knowledge_base_id=knowledge_base_id,
            skip=skip,
            limit=limit
        )
        
        return {
            'success': True,
            'records': records,
            'count': len(records),
            'filters': {
                'question_id': question_id,
                'knowledge_base_id': knowledge_base_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get answer records: {str(e)}")


@router.get("/statistics")
async def get_evaluation_statistics(
    knowledge_base_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get evaluation statistics for the current user"""
    try:
        # Verify knowledge base access if specified
        if knowledge_base_id:
            kb = db.query(KnowledgeBase).filter(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBase.user_id == current_user.id
            ).first()
            
            if not kb:
                raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Get statistics
        stats = await evaluation_service.get_evaluation_statistics(
            db=db,
            user_id=current_user.id,
            knowledge_base_id=knowledge_base_id
        )
        
        return {
            'success': True,
            'statistics': stats,
            'knowledge_base_id': knowledge_base_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/records/{record_id}")
async def get_answer_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get a specific answer record by ID"""
    try:
        from ..models.models import AnswerRecord
        
        # Get record with access verification
        record = (
            db.query(AnswerRecord)
            .join(Question)
            .join(Document)
            .join(KnowledgeBase)
            .filter(
                AnswerRecord.id == record_id,
                AnswerRecord.user_id == current_user.id
            )
            .first()
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Answer record not found")
        
        return {
            'success': True,
            'record': {
                'id': record.id,
                'question_id': record.question_id,
                'question_text': record.question.question_text,
                'question_context': record.question.context,
                'question_difficulty': record.question.difficulty_level,
                'user_answer': record.user_answer,
                'reference_answer': record.reference_answer,
                'score': record.score,
                'feedback': record.feedback,
                'answered_at': record.answered_at.isoformat(),
                'document': {
                    'id': record.question.document.id,
                    'name': record.question.document.filename,
                    'knowledge_base_id': record.question.document.knowledge_base_id,
                    'knowledge_base_name': record.question.document.knowledge_base.name
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get answer record: {str(e)}")


@router.delete("/records/{record_id}")
async def delete_answer_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete an answer record"""
    try:
        from ..models.models import AnswerRecord
        
        # Get record with access verification
        record = (
            db.query(AnswerRecord)
            .filter(
                AnswerRecord.id == record_id,
                AnswerRecord.user_id == current_user.id
            )
            .first()
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Answer record not found")
        
        # Delete record
        db.delete(record)
        db.commit()
        
        return {
            'success': True,
            'message': 'Answer record deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete answer record: {str(e)}")


@router.post("/re-evaluate/{record_id}")
async def re_evaluate_answer(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Re-evaluate an existing answer record"""
    try:
        from ..models.models import AnswerRecord
        
        # Get record with access verification
        record = (
            db.query(AnswerRecord)
            .join(Question)
            .join(Document)
            .join(KnowledgeBase)
            .filter(
                AnswerRecord.id == record_id,
                AnswerRecord.user_id == current_user.id
            )
            .first()
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Answer record not found")
        
        # Re-evaluate the answer
        result = await evaluation_service.evaluate_answer(
            db=db,
            user_id=current_user.id,
            question_id=record.question_id,
            user_answer=record.user_answer,
            save_record=False  # Don't create new record
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Re-evaluation failed'))
        
        # Update existing record
        evaluation = result['evaluation']
        record.reference_answer = evaluation.get('reference_answer', record.reference_answer)
        record.score = evaluation.get('score', record.score)
        record.feedback = evaluation.get('feedback', record.feedback)
        
        db.commit()
        db.refresh(record)
        
        return {
            'success': True,
            'message': 'Answer re-evaluated successfully',
            'evaluation': evaluation,
            'record_id': record.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to re-evaluate answer: {str(e)}")


@router.get("/performance-trends")
async def get_performance_trends(
    knowledge_base_id: Optional[int] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get performance trends over time"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        from ..models.models import AnswerRecord
        
        # Verify knowledge base access if specified
        if knowledge_base_id:
            kb = db.query(KnowledgeBase).filter(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBase.user_id == current_user.id
            ).first()
            
            if not kb:
                raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = (
            db.query(
                func.date(AnswerRecord.answered_at).label('date'),
                func.avg(AnswerRecord.score).label('avg_score'),
                func.count(AnswerRecord.id).label('answer_count')
            )
            .join(Question)
            .join(Document)
            .filter(
                AnswerRecord.user_id == current_user.id,
                AnswerRecord.answered_at >= start_date,
                AnswerRecord.answered_at <= end_date
            )
        )
        
        if knowledge_base_id:
            query = query.filter(Document.knowledge_base_id == knowledge_base_id)
        
        # Execute query
        results = query.group_by(func.date(AnswerRecord.answered_at)).all()
        
        # Format results
        trends = []
        for result in results:
            trends.append({
                'date': result.date.isoformat(),
                'average_score': round(float(result.avg_score), 2),
                'answer_count': result.answer_count
            })
        
        # Sort by date
        trends.sort(key=lambda x: x['date'])
        
        return {
            'success': True,
            'trends': trends,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'knowledge_base_id': knowledge_base_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance trends: {str(e)}")