"""
API endpoints for question generation and management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..core.middleware import get_current_user
from ..models.database import get_db
from ..models.models import Document, KnowledgeBase
from ..services.question_service import question_service
from ..models.models import User

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.post("/generate/document/{document_id}")
async def generate_questions_for_document(
    document_id: int,
    num_questions: int = Query(default=5, ge=1, le=20),
    min_quality_score: float = Query(default=6.0, ge=0.0, le=10.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate questions for a specific document"""
    try:
        # Verify document exists and belongs to user
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user owns the document through knowledge base
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == document.knowledge_base_id,
            KnowledgeBase.user_id == current_user.id
        ).first()
        
        if not kb:
            raise HTTPException(status_code=403, detail="Access denied to this document")
        
        # Check if document is processed
        if not document.processed:
            raise HTTPException(
                status_code=400, 
                detail="Document must be processed before generating questions"
            )
        
        # Generate questions
        result = await question_service.generate_questions_for_document(
            db=db,
            document_id=document_id,
            num_questions=num_questions,
            min_quality_score=min_quality_score
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Question generation failed'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.post("/generate/knowledge-base/{knowledge_base_id}")
async def generate_questions_for_knowledge_base(
    knowledge_base_id: int,
    num_questions_per_document: int = Query(default=3, ge=1, le=10),
    min_quality_score: float = Query(default=6.0, ge=0.0, le=10.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate questions for all documents in a knowledge base"""
    try:
        # Verify knowledge base exists and belongs to user
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.user_id == current_user.id
        ).first()
        
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Generate questions
        result = await question_service.generate_questions_for_knowledge_base(
            db=db,
            knowledge_base_id=knowledge_base_id,
            num_questions_per_document=num_questions_per_document,
            min_quality_score=min_quality_score
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Question generation failed'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.get("/document/{document_id}")
async def get_questions_by_document(
    document_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get questions for a specific document"""
    try:
        # Verify document exists and belongs to user
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user owns the document through knowledge base
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == document.knowledge_base_id,
            KnowledgeBase.user_id == current_user.id
        ).first()
        
        if not kb:
            raise HTTPException(status_code=403, detail="Access denied to this document")
        
        # Get questions
        questions = await question_service.get_questions_by_document(
            db=db,
            document_id=document_id,
            skip=skip,
            limit=limit
        )
        
        return {
            'success': True,
            'document_id': document_id,
            'document_name': document.filename,
            'questions': questions,
            'count': len(questions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get questions: {str(e)}")


@router.get("/knowledge-base/{knowledge_base_id}")
async def get_questions_by_knowledge_base(
    knowledge_base_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get questions for a specific knowledge base"""
    try:
        # Verify knowledge base exists and belongs to user
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.user_id == current_user.id
        ).first()
        
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Get questions
        questions = await question_service.get_questions_by_knowledge_base(
            db=db,
            knowledge_base_id=knowledge_base_id,
            skip=skip,
            limit=limit
        )
        
        return {
            'success': True,
            'knowledge_base_id': knowledge_base_id,
            'knowledge_base_name': kb.name,
            'questions': questions,
            'count': len(questions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get questions: {str(e)}")


@router.get("/{question_id}")
async def get_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get a specific question by ID"""
    try:
        from ..models.models import Question
        
        # Get question with document and knowledge base info
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
        
        return {
            'success': True,
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'context': question.context,
                'difficulty_level': question.difficulty_level,
                'document_id': question.document_id,
                'document_name': question.document.filename,
                'knowledge_base_id': question.document.knowledge_base_id,
                'knowledge_base_name': question.document.knowledge_base.name,
                'created_at': question.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get question: {str(e)}")


@router.put("/{question_id}")
async def update_question(
    question_id: int,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update a question"""
    try:
        from ..models.models import Question
        
        # Verify question exists and belongs to user
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
        
        # Validate updates
        allowed_fields = {'question_text', 'context', 'difficulty_level'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid fields: {', '.join(invalid_fields)}"
            )
        
        # Validate difficulty level if provided
        if 'difficulty_level' in updates:
            difficulty = updates['difficulty_level']
            if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
                raise HTTPException(
                    status_code=400,
                    detail="Difficulty level must be an integer between 1 and 5"
                )
        
        # Update question
        updated_question = await question_service.update_question(
            db=db,
            question_id=question_id,
            updates=updates
        )
        
        if not updated_question:
            raise HTTPException(status_code=500, detail="Failed to update question")
        
        return {
            'success': True,
            'question': updated_question
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update question: {str(e)}")


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete a question"""
    try:
        from ..models.models import Question
        
        # Verify question exists and belongs to user
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
        
        # Delete question
        success = await question_service.delete_question(db=db, question_id=question_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete question")
        
        return {
            'success': True,
            'message': 'Question deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete question: {str(e)}")


@router.get("/stats/difficulty-distribution")
async def get_difficulty_distribution(
    knowledge_base_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get difficulty distribution of questions"""
    try:
        from ..models.models import Question
        from sqlalchemy import func
        
        # Base query
        query = (
            db.query(
                Question.difficulty_level,
                func.count(Question.id).label('count')
            )
            .join(Document)
            .join(KnowledgeBase)
            .filter(KnowledgeBase.user_id == current_user.id)
        )
        
        # Filter by knowledge base if specified
        if knowledge_base_id:
            # Verify knowledge base belongs to user
            kb = db.query(KnowledgeBase).filter(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBase.user_id == current_user.id
            ).first()
            
            if not kb:
                raise HTTPException(status_code=404, detail="Knowledge base not found")
            
            query = query.filter(Document.knowledge_base_id == knowledge_base_id)
        
        # Execute query
        results = query.group_by(Question.difficulty_level).all()
        
        # Format results
        distribution = {str(i): 0 for i in range(1, 6)}  # Initialize all levels to 0
        total_questions = 0
        
        for difficulty, count in results:
            distribution[str(difficulty)] = count
            total_questions += count
        
        return {
            'success': True,
            'knowledge_base_id': knowledge_base_id,
            'total_questions': total_questions,
            'distribution': distribution,
            'difficulty_labels': {
                '1': '基础记忆',
                '2': '简单理解',
                '3': '应用分析',
                '4': '综合评价',
                '5': '复杂推理'
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get difficulty distribution: {str(e)}")