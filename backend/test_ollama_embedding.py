"""
Test Ollama embedding functionality
"""

import asyncio
from llama_index.embeddings.ollama import OllamaEmbedding


async def test_ollama_embedding():
    """Test Ollama embedding model"""
    print("Testing Ollama embedding...")
    
    try:
        # Initialize Ollama embedding
        embed_model = OllamaEmbedding(
            model_name="shaw/dmeta-embedding-zh-small-q4",
            base_url="http://localhost:11434",
            ollama_additional_kwargs={"mirostat": 0},
        )
        
        print("✓ Ollama embedding model initialized")
        
        # Test embedding generation
        test_text = "这是一个测试文本"
        print(f"Testing embedding for: {test_text}")
        
        embedding = embed_model.get_text_embedding(test_text)
        print(f"✓ Generated embedding with dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        
        # Test batch embedding
        test_texts = ["第一个测试", "第二个测试", "第三个测试"]
        print(f"Testing batch embedding for {len(test_texts)} texts")
        
        embeddings = embed_model.get_text_embedding_batch(test_texts)
        print(f"✓ Generated {len(embeddings)} embeddings")
        
        print("✓ Ollama embedding test completed successfully!")
        
    except Exception as e:
        print(f"✗ Ollama embedding test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ollama_embedding())