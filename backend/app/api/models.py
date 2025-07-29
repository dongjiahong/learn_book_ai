"""
API endpoints for model management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ..core.auth import get_current_user
from ..services.model_service import model_service
from ..schemas.auth import User

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/status")
async def get_model_status(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current model status and health information"""
    try:
        return await model_service.get_model_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.post("/health-check")
async def check_model_health(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Perform health check on all configured models"""
    try:
        return await model_service.check_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/switch-provider")
async def switch_model_provider(
    provider: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Switch to a different model provider"""
    try:
        success = await model_service.switch_provider(provider)
        if success:
            return {
                "success": True,
                "message": f"Successfully switched to provider: {provider}",
                "active_provider": provider
            }
        else:
            return {
                "success": False,
                "message": f"Failed to switch to provider: {provider}",
                "error": "Provider is not available or unhealthy"
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to switch provider: {str(e)}")


@router.post("/generate")
async def generate_text(
    prompt: str,
    temperature: float = None,
    max_tokens: int = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate text using the active model"""
    try:
        kwargs = {}
        if temperature is not None:
            kwargs['temperature'] = temperature
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        
        result = await model_service.generate_text(prompt, **kwargs)
        return {
            "success": True,
            "result": result,
            "prompt": prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")


@router.post("/generate-questions")
async def generate_questions(
    content: str,
    num_questions: int = 5,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate questions based on content"""
    try:
        questions = await model_service.generate_questions(content, num_questions)
        return {
            "success": True,
            "questions": questions,
            "count": len(questions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@router.post("/evaluate-answer")
async def evaluate_answer(
    question: str,
    user_answer: str,
    reference_content: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Evaluate user answer against reference content"""
    try:
        evaluation = await model_service.evaluate_answer(question, user_answer, reference_content)
        return {
            "success": True,
            "evaluation": evaluation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer evaluation failed: {str(e)}")


@router.post("/extract-knowledge-points")
async def extract_knowledge_points(
    content: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Extract knowledge points from content"""
    try:
        knowledge_points = await model_service.extract_knowledge_points(content)
        return {
            "success": True,
            "knowledge_points": knowledge_points,
            "count": len(knowledge_points)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge point extraction failed: {str(e)}")