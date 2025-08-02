"""
Model configuration management for RAG Learning Platform
Supports OpenAI API and Ollama local models with health checking and validation
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List
import httpx
import openai
import ollama
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported model providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"


class ModelStatus(str, Enum):
    """Model health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of model health check"""
    status: ModelStatus
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    model_info: Optional[Dict[str, Any]] = None


class OpenAIConfig(BaseModel):
    """OpenAI API configuration"""
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI API base URL")
    model: str = Field(default="gpt-3.5-turbo", description="OpenAI model name")
    embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(default=2048, gt=0, description="Maximum tokens to generate")
    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("OpenAI API key cannot be empty")
        return v.strip() if v else v


class OllamaConfig(BaseModel):
    """Ollama local model configuration"""
    base_url: str = Field(default="http://localhost:11434", description="Ollama server URL")
    model: str = Field(default="qwen3:4b", description="Ollama model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(default=2048, gt=0, description="Maximum tokens to generate")
    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError("Ollama base URL must be a valid HTTP/HTTPS URL")
        return v.rstrip('/')


class EmbeddingConfig(BaseModel):
    """Embedding model configuration"""
    provider: str = Field(default="ollama", description="Embedding provider (ollama/openai)")
    model: str = Field(default="shaw/dmeta-embedding-zh-small-q4", description="Embedding model name")
    dimension: int = Field(default=384, gt=0, description="Embedding dimension")
    batch_size: int = Field(default=32, gt=0, description="Batch size for embedding")


class OpenAIEmbeddingConfig(BaseModel):
    """OpenAI embedding specific configuration"""
    model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model name")
    dimension: int = Field(default=1536, gt=0, description="Embedding dimension")
    batch_size: int = Field(default=100, gt=0, description="Batch size for embedding")


class ModelConfig(BaseModel):
    """Complete model configuration"""
    provider: ModelProvider = Field(default=ModelProvider.OLLAMA, description="Active model provider")
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    openai_embedding: OpenAIEmbeddingConfig = Field(default_factory=OpenAIEmbeddingConfig)
    fallback_provider: Optional[ModelProvider] = Field(default=None, description="Fallback provider if primary fails")
    health_check_interval: int = Field(default=300, gt=0, description="Health check interval in seconds")


class BaseModelClient(ABC):
    """Abstract base class for model clients"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._last_health_check: Optional[HealthCheckResult] = None
    
    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """Perform health check on the model"""
        pass
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the model"""
        pass
    
    @property
    def is_healthy(self) -> bool:
        """Check if the model is healthy based on last health check"""
        return (self._last_health_check is not None and 
                self._last_health_check.status == ModelStatus.HEALTHY)


class OpenAIClient(BaseModelClient):
    """OpenAI API client with health checking"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(
            api_key=config.openai.api_key,
            timeout=config.openai.timeout
        )
    
    async def health_check(self) -> HealthCheckResult:
        """Check OpenAI API health"""
        import time
        start_time = time.time()
        
        try:
            # Simple test request to check API availability
            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                temperature=0
            )
            
            response_time = (time.time() - start_time) * 1000
            
            self._last_health_check = HealthCheckResult(
                status=ModelStatus.HEALTHY,
                response_time_ms=response_time,
                model_info={
                    "model": self.config.openai.model,
                    "provider": "openai"
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            self._last_health_check = HealthCheckResult(
                status=ModelStatus.UNHEALTHY,
                error_message=str(e)
            )
        
        return self._last_health_check
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', self.config.openai.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.openai.max_tokens)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI text generation failed: {e}")
            raise


class OllamaClient(BaseModelClient):
    """Ollama local model client with health checking"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = ollama.AsyncClient(host=config.ollama.base_url)
    
    async def health_check(self) -> HealthCheckResult:
        """Check Ollama server health"""
        import time
        start_time = time.time()
        
        try:
            # Check if Ollama server is running
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(
                    f"{self.config.ollama.base_url}/api/tags",
                    timeout=self.config.ollama.timeout
                )
                response.raise_for_status()
                
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                # Check if our configured model is available
                model_available = any(
                    self.config.ollama.model in name for name in model_names
                )
                
                if not model_available:
                    raise ValueError(f"Model {self.config.ollama.model} not found in Ollama")
                
                response_time = (time.time() - start_time) * 1000
                
                self._last_health_check = HealthCheckResult(
                    status=ModelStatus.HEALTHY,
                    response_time_ms=response_time,
                    model_info={
                        "model": self.config.ollama.model,
                        "provider": "ollama",
                        "available_models": model_names
                    }
                )
                
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            self._last_health_check = HealthCheckResult(
                status=ModelStatus.UNHEALTHY,
                error_message=str(e)
            )
        
        return self._last_health_check
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama"""
        try:
            response = await self.client.generate(
                model=self.config.ollama.model,
                prompt=prompt,
                options={
                    'temperature': kwargs.get('temperature', self.config.ollama.temperature),
                    'num_predict': kwargs.get('max_tokens', self.config.ollama.max_tokens),
                    'repeat_penalty': 1.1,
                    'top_k': 40,
                    'top_p': 0.9
                }
            )
            return response['response']
        except Exception as e:
            logger.error(f"Ollama text generation failed: {e}")
            raise


class ModelManager:
    """Manages model clients and provides switching capabilities"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.clients: Dict[ModelProvider, BaseModelClient] = {}
        self._initialize_clients()
        self._health_check_task: Optional[asyncio.Task] = None
    
    def _initialize_clients(self):
        """Initialize model clients based on configuration"""
        # Initialize OpenAI client if API key is provided
        if self.config.openai.api_key and self.config.openai.api_key.strip():
            self.clients[ModelProvider.OPENAI] = OpenAIClient(self.config)
        
        # Initialize Ollama client
        self.clients[ModelProvider.OLLAMA] = OllamaClient(self.config)
    
    async def start_health_monitoring(self):
        """Start periodic health checking"""
        if self._health_check_task is None or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def stop_health_monitoring(self):
        """Stop periodic health checking"""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
    
    async def _health_check_loop(self):
        """Periodic health check loop"""
        while True:
            try:
                await self.check_all_models_health()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def check_all_models_health(self) -> Dict[ModelProvider, HealthCheckResult]:
        """Check health of all configured models"""
        results = {}
        
        for provider, client in self.clients.items():
            try:
                result = await client.health_check()
                results[provider] = result
                logger.info(f"{provider} health check: {result.status}")
            except Exception as e:
                logger.error(f"Health check failed for {provider}: {e}")
                results[provider] = HealthCheckResult(
                    status=ModelStatus.UNHEALTHY,
                    error_message=str(e)
                )
        
        return results
    
    def get_active_client(self) -> BaseModelClient:
        """Get the currently active model client"""
        primary_client = self.clients.get(self.config.provider)
        
        if primary_client and primary_client.is_healthy:
            return primary_client
        
        # Try fallback provider if primary is unhealthy
        if self.config.fallback_provider:
            fallback_client = self.clients.get(self.config.fallback_provider)
            if fallback_client and fallback_client.is_healthy:
                logger.warning(f"Using fallback provider {self.config.fallback_provider}")
                return fallback_client
        
        # Return primary client even if unhealthy (will raise error on use)
        if primary_client:
            return primary_client
        
        raise RuntimeError(f"No client available for provider {self.config.provider}")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the active model"""
        client = self.get_active_client()
        return await client.generate_text(prompt, **kwargs)
    
    async def switch_provider(self, provider: ModelProvider) -> bool:
        """Switch to a different model provider"""
        if provider not in self.clients:
            logger.error(f"Provider {provider} not configured")
            return False
        
        # Check if the target provider is healthy
        client = self.clients[provider]
        health_result = await client.health_check()
        
        if health_result.status == ModelStatus.HEALTHY:
            self.config.provider = provider
            logger.info(f"Switched to provider {provider}")
            return True
        else:
            logger.error(f"Cannot switch to unhealthy provider {provider}: {health_result.error_message}")
            return False
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all configured models"""
        status = {
            "active_provider": self.config.provider,
            "fallback_provider": self.config.fallback_provider,
            "models": {}
        }
        
        for provider, client in self.clients.items():
            if client._last_health_check:
                status["models"][provider] = {
                    "status": client._last_health_check.status,
                    "response_time_ms": client._last_health_check.response_time_ms,
                    "error_message": client._last_health_check.error_message,
                    "model_info": client._last_health_check.model_info
                }
            else:
                status["models"][provider] = {
                    "status": ModelStatus.UNKNOWN,
                    "message": "No health check performed yet"
                }
        
        return status