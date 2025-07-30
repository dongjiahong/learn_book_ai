#!/usr/bin/env python3
"""
Test script for knowledge point extraction functionality
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import get_db
from app.models.models import Document, KnowledgeBase, User
from app.services.model_service import model_service


async def test_knowledge_point_extraction():
    """Test knowledge point extraction functionality"""
    print("Testing Knowledge Point Extraction...")
    
    try:
        # Test the model service extraction directly
        test_content = """
        机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。
        
        主要的机器学习类型包括：
        1. 监督学习：使用标记数据训练模型
        2. 无监督学习：从未标记数据中发现模式
        3. 强化学习：通过与环境交互学习最优策略
        
        深度学习是机器学习的一个子集，使用神经网络来模拟人脑的学习过程。
        """
        
        print("Extracting knowledge points from test content...")
        knowledge_points = await model_service.extract_knowledge_points(test_content)
        
        print(f"Extracted {len(knowledge_points)} knowledge points:")
        for i, kp in enumerate(knowledge_points, 1):
            print(f"\n{i}. {kp['title']}")
            print(f"   Content: {kp['content'][:100]}...")
            print(f"   Importance: {kp['importance_level']}")
        
        print("\n✅ Knowledge point extraction test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_database_operations():
    """Test database operations for knowledge points"""
    print("\nTesting Database Operations...")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Check if we have any documents
        documents = db.query(Document).limit(5).all()
        print(f"Found {len(documents)} documents in database")
        
        for doc in documents:
            print(f"- Document {doc.id}: {doc.filename}")
            
            # Check existing knowledge points
            from app.models.models import KnowledgePoint
            existing_kps = db.query(KnowledgePoint).filter(KnowledgePoint.document_id == doc.id).all()
            print(f"  Existing knowledge points: {len(existing_kps)}")
        
        print("\n✅ Database operations test completed!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function"""
    print("🚀 Starting Knowledge Point Service Tests\n")
    
    # Test model service
    await test_knowledge_point_extraction()
    
    # Test database operations
    await test_database_operations()
    
    # Test API import
    try:
        print("\nTesting API import...")
        from app.api.knowledge_points import router
        print(f"✅ Knowledge points API router imported successfully: {len(router.routes)} routes")
    except Exception as e:
        print(f"❌ API import failed: {e}")
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())