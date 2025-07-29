"""
Integration test for model service
"""

import asyncio
from app.services.model_service import model_service


async def test_model_service():
    """Test model service functionality"""
    print("Testing model service...")
    
    try:
        # Start the service
        await model_service.start()
        print("✓ Model service started successfully")
        
        # Get model status
        status = await model_service.get_model_status()
        print(f"✓ Model status retrieved: {status['active_provider']}")
        
        # Check health
        health = await model_service.check_health()
        print(f"✓ Health check completed: {len(health)} providers checked")
        
        # Test text generation (this might fail if no models are available)
        try:
            result = await model_service.generate_text("Hello, this is a test.", max_tokens=10)
            print(f"✓ Text generation successful: {result[:50]}...")
        except Exception as e:
            print(f"⚠ Text generation failed (expected if no models available): {e}")
        
        # Stop the service
        await model_service.stop()
        print("✓ Model service stopped successfully")
        
    except Exception as e:
        print(f"✗ Model service test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_model_service())