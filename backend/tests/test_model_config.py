"""
Unit tests for model configuration management
"""

import pytest
import asyncio
import tempfile
import os
import importlib.util
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from app.core.model_config import (
    ModelConfig, ModelProvider, OpenAIConfig, OllamaConfig, EmbeddingConfig,
    ModelManager, OpenAIClient, OllamaClient, ModelStatus, HealthCheckResult
)


class TestModelConfig:
    """Test model configuration classes"""
    
    def test_openai_config_validation(self):
        """Test OpenAI configuration validation"""
        # Valid config
        config = OpenAIConfig(api_key="sk-test123")
        assert config.api_key == "sk-test123"
        assert config.model == "gpt-3.5-turbo"
        
        # Invalid API key
        with pytest.raises(ValueError, match="OpenAI API key cannot be empty"):
            OpenAIConfig(api_key="")
        
        with pytest.raises(ValueError, match="OpenAI API key cannot be empty"):
            OpenAIConfig(api_key="   ")
    
    def test_ollama_config_validation(self):
        """Test Ollama configuration validation"""
        # Valid config
        config = OllamaConfig(base_url="http://localhost:11434")
        assert config.base_url == "http://localhost:11434"
        assert config.model == "qwen3:4b"
        
        # Invalid URL
        with pytest.raises(ValueError, match="Ollama base URL must be a valid HTTP/HTTPS URL"):
            OllamaConfig(base_url="invalid-url")
        
        with pytest.raises(ValueError, match="Ollama base URL must be a valid HTTP/HTTPS URL"):
            OllamaConfig(base_url="")
    
    def test_embedding_config_defaults(self):
        """Test embedding configuration defaults"""
        config = EmbeddingConfig()
        assert config.provider == "huggingface"
        assert config.model == "shaw/dmeta-embedding-zh-small-q4"
        assert config.dimension == 384
        assert config.batch_size == 32
    
    def test_model_config_creation(self):
        """Test complete model configuration creation"""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            openai=OpenAIConfig(api_key="sk-test123"),
            ollama=OllamaConfig(),
            embedding=EmbeddingConfig(),
            fallback_provider=ModelProvider.OLLAMA
        )
        
        assert config.provider == ModelProvider.OPENAI
        assert config.fallback_provider == ModelProvider.OLLAMA
        assert config.openai.api_key == "sk-test123"
        assert config.health_check_interval == 300


class TestOpenAIClient:
    """Test OpenAI client functionality"""
    
    @pytest.fixture
    def model_config(self):
        """Create test model configuration"""
        return ModelConfig(
            provider=ModelProvider.OPENAI,
            openai=OpenAIConfig(api_key="sk-test123")
        )
    
    @pytest.fixture
    def openai_client(self, model_config):
        """Create OpenAI client for testing"""
        return OpenAIClient(model_config)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, openai_client):
        """Test successful health check"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello"
        
        with patch.object(openai_client.client.chat.completions, 'create', 
                         new_callable=AsyncMock, return_value=mock_response) as mock_create:
            result = await openai_client.health_check()
            
            assert result.status == ModelStatus.HEALTHY
            assert result.response_time_ms is not None
            assert result.response_time_ms > 0
            assert result.model_info["provider"] == "openai"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, openai_client):
        """Test failed health check"""
        with patch.object(openai_client.client.chat.completions, 'create', 
                         new_callable=AsyncMock, side_effect=Exception("API Error")) as mock_create:
            result = await openai_client.health_check()
            
            assert result.status == ModelStatus.UNHEALTHY
            assert result.error_message == "API Error"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, openai_client):
        """Test successful text generation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated text"
        
        with patch.object(openai_client.client.chat.completions, 'create', 
                         new_callable=AsyncMock, return_value=mock_response) as mock_create:
            result = await openai_client.generate_text("Test prompt")
            
            assert result == "Generated text"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_text_failure(self, openai_client):
        """Test failed text generation"""
        with patch.object(openai_client.client.chat.completions, 'create', 
                         new_callable=AsyncMock, side_effect=Exception("Generation failed")):
            with pytest.raises(Exception, match="Generation failed"):
                await openai_client.generate_text("Test prompt")


class TestOllamaClient:
    """Test Ollama client functionality"""
    
    @pytest.fixture
    def model_config(self):
        """Create test model configuration"""
        return ModelConfig(
            provider=ModelProvider.OLLAMA,
            openai=OpenAIConfig(api_key=None),
            ollama=OllamaConfig(base_url="http://localhost:11434", model="qwen3:4b")
        )
    
    @pytest.fixture
    def ollama_client(self, model_config):
        """Create Ollama client for testing"""
        return OllamaClient(model_config)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, ollama_client):
        """Test successful health check"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen3:4b"},
                {"name": "llama2:7b"}
            ]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await ollama_client.health_check()
            
            assert result.status == ModelStatus.HEALTHY
            assert result.response_time_ms is not None
            assert result.model_info["provider"] == "ollama"
            assert "qwen3:4b" in result.model_info["available_models"]
    
    @pytest.mark.asyncio
    async def test_health_check_model_not_found(self, ollama_client):
        """Test health check when model is not available"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2:7b"}
            ]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await ollama_client.health_check()
            
            assert result.status == ModelStatus.UNHEALTHY
            assert "not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, ollama_client):
        """Test successful text generation"""
        mock_response = {"response": "Generated text"}
        
        with patch.object(ollama_client.client, 'generate', new_callable=AsyncMock, return_value=mock_response) as mock_generate:
            result = await ollama_client.generate_text("Test prompt")
            
            assert result == "Generated text"
            mock_generate.assert_called_once()


class TestModelManager:
    """Test model manager functionality"""
    
    @pytest.fixture
    def model_config(self):
        """Create test model configuration"""
        return ModelConfig(
            provider=ModelProvider.OLLAMA,
            openai=OpenAIConfig(api_key="sk-test123"),
            ollama=OllamaConfig(),
            fallback_provider=ModelProvider.OPENAI
        )
    
    @pytest.fixture
    def model_manager(self, model_config):
        """Create model manager for testing"""
        return ModelManager(model_config)
    
    def test_initialization(self, model_manager):
        """Test model manager initialization"""
        assert ModelProvider.OPENAI in model_manager.clients
        assert ModelProvider.OLLAMA in model_manager.clients
        assert isinstance(model_manager.clients[ModelProvider.OPENAI], OpenAIClient)
        assert isinstance(model_manager.clients[ModelProvider.OLLAMA], OllamaClient)
    
    @pytest.mark.asyncio
    async def test_check_all_models_health(self, model_manager):
        """Test health check for all models"""
        # Mock health check results
        healthy_result = HealthCheckResult(status=ModelStatus.HEALTHY, response_time_ms=100)
        unhealthy_result = HealthCheckResult(status=ModelStatus.UNHEALTHY, error_message="Error")
        
        with patch.object(model_manager.clients[ModelProvider.OPENAI], 'health_check', 
                         return_value=healthy_result), \
             patch.object(model_manager.clients[ModelProvider.OLLAMA], 'health_check', 
                         return_value=unhealthy_result):
            
            results = await model_manager.check_all_models_health()
            
            assert results[ModelProvider.OPENAI].status == ModelStatus.HEALTHY
            assert results[ModelProvider.OLLAMA].status == ModelStatus.UNHEALTHY
    
    def test_get_active_client_primary_healthy(self, model_manager):
        """Test getting active client when primary is healthy"""
        # Mock primary client as healthy
        model_manager.clients[ModelProvider.OLLAMA]._last_health_check = HealthCheckResult(
            status=ModelStatus.HEALTHY
        )
        
        client = model_manager.get_active_client()
        assert client == model_manager.clients[ModelProvider.OLLAMA]
    
    def test_get_active_client_fallback(self, model_manager):
        """Test getting active client with fallback when primary is unhealthy"""
        # Mock primary as unhealthy, fallback as healthy
        model_manager.clients[ModelProvider.OLLAMA]._last_health_check = HealthCheckResult(
            status=ModelStatus.UNHEALTHY
        )
        model_manager.clients[ModelProvider.OPENAI]._last_health_check = HealthCheckResult(
            status=ModelStatus.HEALTHY
        )
        
        client = model_manager.get_active_client()
        assert client == model_manager.clients[ModelProvider.OPENAI]
    
    @pytest.mark.asyncio
    async def test_switch_provider_success(self, model_manager):
        """Test successful provider switching"""
        # Mock target provider as healthy
        healthy_result = HealthCheckResult(status=ModelStatus.HEALTHY)
        
        with patch.object(model_manager.clients[ModelProvider.OPENAI], 'health_check', 
                         return_value=healthy_result):
            result = await model_manager.switch_provider(ModelProvider.OPENAI)
            
            assert result is True
            assert model_manager.config.provider == ModelProvider.OPENAI
    
    @pytest.mark.asyncio
    async def test_switch_provider_unhealthy(self, model_manager):
        """Test provider switching to unhealthy provider"""
        # Mock target provider as unhealthy
        unhealthy_result = HealthCheckResult(status=ModelStatus.UNHEALTHY, error_message="Error")
        
        with patch.object(model_manager.clients[ModelProvider.OPENAI], 'health_check', 
                         return_value=unhealthy_result):
            result = await model_manager.switch_provider(ModelProvider.OPENAI)
            
            assert result is False
            assert model_manager.config.provider == ModelProvider.OLLAMA  # Should remain unchanged
    
    def test_get_model_status(self, model_manager):
        """Test getting model status"""
        # Mock health check results
        model_manager.clients[ModelProvider.OPENAI]._last_health_check = HealthCheckResult(
            status=ModelStatus.HEALTHY, response_time_ms=100
        )
        model_manager.clients[ModelProvider.OLLAMA]._last_health_check = HealthCheckResult(
            status=ModelStatus.UNHEALTHY, error_message="Connection failed"
        )
        
        status = model_manager.get_model_status()
        
        assert status["active_provider"] == ModelProvider.OLLAMA
        assert status["fallback_provider"] == ModelProvider.OPENAI
        assert status["models"][ModelProvider.OPENAI]["status"] == ModelStatus.HEALTHY
        assert status["models"][ModelProvider.OLLAMA]["status"] == ModelStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_health_monitoring_lifecycle(self, model_manager):
        """Test health monitoring start and stop"""
        # Start monitoring
        await model_manager.start_health_monitoring()
        assert model_manager._health_check_task is not None
        assert not model_manager._health_check_task.done()
        
        # Stop monitoring
        await model_manager.stop_health_monitoring()
        assert model_manager._health_check_task.cancelled()


class TestConfigIntegration:
    """Test integration with configuration system"""
    
    def test_config_toml_parsing(self):
        """Test parsing TOML configuration"""
        # Test the model config creation directly
        import toml
        
        toml_content = """
[llm]
provider = "openai"
fallback_provider = "ollama"
temperature = 0.8
max_tokens = 1024
health_check_interval = 600

[openai]
api_key = "sk-test123"
model = "gpt-4"
timeout = 60

[ollama]
base_url = "http://localhost:11434"
model = "qwen3:4b"
timeout = 45

[embeddings]
provider = "huggingface"
model = "shaw/dmeta-embedding-zh-small-q4"
dimension = 768
batch_size = 16
"""
        
        # Parse TOML content
        config_data = toml.loads(toml_content)
        
        # Extract sections
        llm_section = config_data.get("llm", {})
        openai_section = config_data.get("openai", {})
        ollama_section = config_data.get("ollama", {})
        embeddings_section = config_data.get("embeddings", {})
        
        # Create configurations
        openai_config = OpenAIConfig(
            api_key=openai_section.get("api_key"),
            model=openai_section.get("model", "gpt-3.5-turbo"),
            temperature=llm_section.get("temperature", 0.7),
            max_tokens=llm_section.get("max_tokens", 2048),
            timeout=openai_section.get("timeout", 30)
        )
        
        ollama_config = OllamaConfig(
            base_url=ollama_section.get("base_url", "http://localhost:11434"),
            model=ollama_section.get("model", "qwen3:4b"),
            temperature=llm_section.get("temperature", 0.7),
            max_tokens=llm_section.get("max_tokens", 2048),
            timeout=ollama_section.get("timeout", 30)
        )
        
        embedding_config = EmbeddingConfig(
            provider=embeddings_section.get("provider", "huggingface"),
            model=embeddings_section.get("model", "shaw/dmeta-embedding-zh-small-q4"),
            dimension=embeddings_section.get("dimension", 384),
            batch_size=embeddings_section.get("batch_size", 32)
        )
        
        # Create complete model config
        model_config = ModelConfig(
            provider=ModelProvider(llm_section.get("provider", "ollama")),
            openai=openai_config,
            ollama=ollama_config,
            embedding=embedding_config,
            fallback_provider=ModelProvider(llm_section.get("fallback_provider")) if llm_section.get("fallback_provider") else None,
            health_check_interval=llm_section.get("health_check_interval", 300)
        )
        
        # Verify configuration
        assert model_config.provider == ModelProvider.OPENAI
        assert model_config.fallback_provider == ModelProvider.OLLAMA
        assert model_config.openai.api_key == "sk-test123"
        assert model_config.openai.model == "gpt-4"
        assert model_config.openai.timeout == 60
        assert model_config.ollama.base_url == "http://localhost:11434"
        assert model_config.ollama.timeout == 45
        assert model_config.embedding.model == "shaw/dmeta-embedding-zh-small-q4"
        assert model_config.embedding.dimension == 768
        assert model_config.embedding.batch_size == 16
        assert model_config.health_check_interval == 600


if __name__ == "__main__":
    pytest.main([__file__])