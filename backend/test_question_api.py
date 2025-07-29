"""
Test script for question generation API endpoints
"""

import asyncio
import sys
import os
from pathlib import Path
import httpx
import json

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.database import get_db
from app.models.models import User, KnowledgeBase, Document


async def test_api_endpoints():
    """Test the question generation API endpoints"""
    print("Testing Question Generation API Endpoints")
    print("="*50)
    
    # First, get test data from database
    db = next(get_db())
    
    try:
        # Get test user and data
        test_user = db.query(User).first()
        if not test_user:
            print("❌ No test user found in database")
            return
        
        test_kb = db.query(KnowledgeBase).filter(KnowledgeBase.user_id == test_user.id).first()
        if not test_kb:
            print("❌ No test knowledge base found")
            return
        
        test_doc = db.query(Document).filter(
            Document.knowledge_base_id == test_kb.id,
            Document.processed == True
        ).first()
        if not test_doc:
            # Try to find any document
            any_doc = db.query(Document).filter(Document.knowledge_base_id == test_kb.id).first()
            if any_doc:
                print(f"❌ Found document but not processed: {any_doc.filename} (processed: {any_doc.processed})")
            else:
                print("❌ No documents found in knowledge base")
            return
        
        print(f"Using test data:")
        print(f"- User: {test_user.username}")
        print(f"- Knowledge Base: {test_kb.name} (ID: {test_kb.id})")
        print(f"- Document: {test_doc.filename} (ID: {test_doc.id})")
        
    except Exception as e:
        print(f"❌ Failed to get test data: {e}")
        return
    finally:
        db.close()
    
    # Test API endpoints (Note: This would require the server to be running)
    print(f"\n📝 API endpoint tests would require the FastAPI server to be running.")
    print(f"   To test the API endpoints manually:")
    print(f"   1. Start the server: python main.py")
    print(f"   2. Use the following endpoints:")
    print(f"      - POST /api/questions/generate/document/{test_doc.id}")
    print(f"      - POST /api/questions/generate/knowledge-base/{test_kb.id}")
    print(f"      - GET /api/questions/document/{test_doc.id}")
    print(f"      - GET /api/questions/knowledge-base/{test_kb.id}")
    print(f"      - GET /api/questions/stats/difficulty-distribution")
    
    # Show sample curl commands
    print(f"\n📋 Sample curl commands (replace with actual auth token):")
    print(f"""
    # Generate questions for document
    curl -X POST "http://localhost:8000/api/questions/generate/document/{test_doc.id}?num_questions=5&min_quality_score=6.0" \\
         -H "Authorization: Bearer YOUR_TOKEN"
    
    # Generate questions for knowledge base
    curl -X POST "http://localhost:8000/api/questions/generate/knowledge-base/{test_kb.id}?num_questions_per_document=3" \\
         -H "Authorization: Bearer YOUR_TOKEN"
    
    # Get questions by document
    curl -X GET "http://localhost:8000/api/questions/document/{test_doc.id}" \\
         -H "Authorization: Bearer YOUR_TOKEN"
    
    # Get difficulty distribution
    curl -X GET "http://localhost:8000/api/questions/stats/difficulty-distribution?knowledge_base_id={test_kb.id}" \\
         -H "Authorization: Bearer YOUR_TOKEN"
    """)


async def verify_service_components():
    """Verify all service components are working"""
    print("\n" + "="*50)
    print("Verifying Service Components")
    print("="*50)
    
    try:
        # Test imports
        from app.services.question_service import question_service, QuestionQualityEvaluator, QuestionDifficultyClassifier
        from app.api.questions import router
        print("✅ All imports successful")
        
        # Test quality evaluator
        evaluator = QuestionQualityEvaluator()
        quality_result = evaluator.evaluate_question_quality(
            "什么是机器学习？", 
            "机器学习是人工智能的一个分支"
        )
        print(f"✅ Quality evaluator working - Score: {quality_result['score']}")
        
        # Test difficulty classifier
        classifier = QuestionDifficultyClassifier()
        difficulty = classifier.classify_difficulty(
            "分析机器学习算法的优缺点", 
            "机器学习算法有很多种类型"
        )
        print(f"✅ Difficulty classifier working - Level: {difficulty}")
        
        # Test router registration
        print(f"✅ API router has {len(router.routes)} routes registered")
        
        # List all routes
        print(f"\n📋 Available API routes:")
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = ', '.join(route.methods)
                print(f"   {methods} {route.path}")
        
        print(f"\n✅ All service components verified successfully!")
        
    except Exception as e:
        print(f"❌ Service component verification failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    await verify_service_components()
    await test_api_endpoints()


if __name__ == "__main__":
    asyncio.run(main())