"""
Integration test for RAG service
"""

import asyncio
import tempfile
import os
from pathlib import Path
from app.services.rag_service import rag_service


async def test_rag_service():
    """Test RAG service functionality"""
    print("Testing RAG service...")
    
    try:
        # Test 1: Get initial stats
        print("1. Getting initial index stats...")
        stats = await rag_service.get_index_stats()
        print(f"   Initial stats: {stats}")
        
        # Test 2: Create a test document
        print("2. Creating test document...")
        test_content = """
        人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，
        并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        
        机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习。
        机器学习算法通过训练数据来构建数学模型，以便对新数据做出预测或决策。
        
        深度学习是机器学习的一个子集，它基于人工神经网络，特别是深层神经网络。
        深度学习在图像识别、自然语言处理、语音识别等领域取得了显著成果。
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            # Test 3: Load document
            print("3. Loading test document...")
            result = await rag_service.load_documents([temp_file_path])
            print(f"   Load result: {result}")
            
            if result.get("success"):
                # Test 4: Query the system
                print("4. Testing query...")
                query_result = await rag_service.query("什么是机器学习？")
                print(f"   Query result: {query_result.get('response', 'No response')[:200]}...")
                
                # Test 5: Get similar documents
                print("5. Testing similar document retrieval...")
                similar_docs = await rag_service.get_similar_documents("深度学习", top_k=2)
                print(f"   Found {len(similar_docs)} similar documents")
                
                # Test 6: Get updated stats
                print("6. Getting updated stats...")
                updated_stats = await rag_service.get_index_stats()
                print(f"   Updated stats: {updated_stats}")
                
                print("✓ RAG service test completed successfully!")
            else:
                print(f"✗ Failed to load document: {result}")
                
        finally:
            # Clean up
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"Warning: Failed to delete temp file: {e}")
        
    except Exception as e:
        print(f"✗ RAG service test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_rag_service())