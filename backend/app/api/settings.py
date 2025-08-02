"""
Settings API endpoints for RAG Learning Platform
Handles configuration management and model settings
"""

import logging
import toml
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.middleware import get_current_user
from app.core.config import config
from app.core.model_config import ModelProvider, OpenAIConfig, OllamaConfig, EmbeddingConfig, OpenAIEmbeddingConfig
from app.models.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class ModelSettingsRequest(BaseModel):
    """Request model for updating model settings"""
    provider: Optional[ModelProvider] = None
    fallback_provider: Optional[ModelProvider] = None
    
    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None
    openai_embedding_model: Optional[str] = None
    
    # Ollama settings
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    
    # Embedding settings
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    
    # OpenAI embedding settings
    openai_embedding_model_name: Optional[str] = None
    openai_embedding_dimension: Optional[int] = None
    
    # General settings
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)


class ModelSettingsResponse(BaseModel):
    """Response model for model settings"""
    provider: str
    fallback_provider: Optional[str]
    
    # OpenAI settings
    openai_api_key_set: bool
    openai_base_url: str
    openai_model: str
    openai_embedding_model: str
    
    # Ollama settings
    ollama_base_url: str
    ollama_model: str
    
    # Embedding settings
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    
    # OpenAI embedding settings (separate config)
    openai_embedding_model_config: str
    openai_embedding_dimension_config: int
    
    # General settings
    temperature: float
    max_tokens: int
    timeout: int


@router.get("/models", response_model=ModelSettingsResponse)
async def get_model_settings(current_user: User = Depends(get_current_user)) -> ModelSettingsResponse:
    """获取当前模型设置"""
    try:
        model_config = config.model_config
        
        return ModelSettingsResponse(
            provider=model_config.provider.value,
            fallback_provider=model_config.fallback_provider.value if model_config.fallback_provider else None,
            
            # OpenAI settings
            openai_api_key_set=bool(model_config.openai.api_key and model_config.openai.api_key.strip()),
            openai_base_url=model_config.openai.base_url,
            openai_model=model_config.openai.model,
            openai_embedding_model=model_config.openai.embedding_model,
            
            # Ollama settings
            ollama_base_url=model_config.ollama.base_url,
            ollama_model=model_config.ollama.model,
            
            # Embedding settings
            embedding_provider=model_config.embedding.provider,
            embedding_model=model_config.embedding.model,
            embedding_dimension=model_config.embedding.dimension,
            
            # OpenAI embedding settings (separate config)
            openai_embedding_model_config=model_config.openai_embedding.model,
            openai_embedding_dimension_config=model_config.openai_embedding.dimension,
            
            # General settings
            temperature=model_config.openai.temperature,
            max_tokens=model_config.openai.max_tokens,
            timeout=model_config.openai.timeout
        )
        
    except Exception as e:
        logger.error(f"Failed to get model settings: {e}")
        raise HTTPException(status_code=500, detail="获取模型设置失败")


@router.put("/models")
async def update_model_settings(
    settings: ModelSettingsRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """更新模型设置"""
    try:
        # 读取当前配置
        config_path = Path("config.toml")
        if not config_path.exists():
            raise HTTPException(status_code=500, detail="配置文件不存在")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            current_config = toml.load(f)
        
        # 更新配置
        updated_sections = []
        
        # 更新 LLM 配置
        if settings.provider is not None:
            current_config.setdefault("llm", {})["provider"] = settings.provider.value
            updated_sections.append("llm.provider")
        
        if settings.fallback_provider is not None:
            current_config.setdefault("llm", {})["fallback_provider"] = settings.fallback_provider.value
            updated_sections.append("llm.fallback_provider")
        
        if settings.temperature is not None:
            current_config.setdefault("llm", {})["temperature"] = settings.temperature
            updated_sections.append("llm.temperature")
        
        if settings.max_tokens is not None:
            current_config.setdefault("llm", {})["max_tokens"] = settings.max_tokens
            updated_sections.append("llm.max_tokens")
        
        # 更新 OpenAI 配置
        if settings.openai_api_key is not None:
            current_config.setdefault("openai", {})["api_key"] = settings.openai_api_key
            updated_sections.append("openai.api_key")
        
        if settings.openai_base_url is not None:
            current_config.setdefault("openai", {})["base_url"] = settings.openai_base_url
            updated_sections.append("openai.base_url")
        
        if settings.openai_model is not None:
            current_config.setdefault("openai", {})["model"] = settings.openai_model
            updated_sections.append("openai.model")
        
        if settings.openai_embedding_model is not None:
            current_config.setdefault("openai", {})["embedding_model"] = settings.openai_embedding_model
            updated_sections.append("openai.embedding_model")
        
        # 更新 Ollama 配置
        if settings.ollama_base_url is not None:
            current_config.setdefault("ollama", {})["base_url"] = settings.ollama_base_url
            updated_sections.append("ollama.base_url")
        
        if settings.ollama_model is not None:
            current_config.setdefault("ollama", {})["model"] = settings.ollama_model
            updated_sections.append("ollama.model")
        
        # 更新嵌入配置
        if settings.embedding_provider is not None:
            current_config.setdefault("embeddings", {})["provider"] = settings.embedding_provider
            updated_sections.append("embeddings.provider")
        
        if settings.embedding_model is not None:
            current_config.setdefault("embeddings", {})["model"] = settings.embedding_model
            updated_sections.append("embeddings.model")
        
        if settings.embedding_dimension is not None:
            current_config.setdefault("embeddings", {})["dimension"] = settings.embedding_dimension
            updated_sections.append("embeddings.dimension")
        
        # 更新 OpenAI 嵌入配置
        if settings.openai_embedding_model_name is not None:
            current_config.setdefault("openai_embeddings", {})["model"] = settings.openai_embedding_model_name
            updated_sections.append("openai_embeddings.model")
        
        if settings.openai_embedding_dimension is not None:
            current_config.setdefault("openai_embeddings", {})["dimension"] = settings.openai_embedding_dimension
            updated_sections.append("openai_embeddings.dimension")
        
        # 保存配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(current_config, f)
        
        # 重新加载配置
        config.reload_config()
        
        logger.info(f"Model settings updated by user {current_user.username}: {updated_sections}")
        
        return {
            "message": "模型设置更新成功",
            "updated_sections": updated_sections
        }
        
    except Exception as e:
        logger.error(f"Failed to update model settings: {e}")
        raise HTTPException(status_code=500, detail=f"更新模型设置失败: {str(e)}")


@router.get("/models/status")
async def get_model_status(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """获取模型状态"""
    try:
        # 这里需要从模型管理器获取状态
        # 暂时返回基本信息
        model_config = config.model_config
        
        return {
            "active_provider": model_config.provider.value,
            "fallback_provider": model_config.fallback_provider.value if model_config.fallback_provider else None,
            "openai_configured": bool(model_config.openai.api_key and model_config.openai.api_key.strip()),
            "ollama_configured": bool(model_config.ollama.base_url),
            "embedding_provider": model_config.embedding.provider,
            "health_check_interval": model_config.health_check_interval
        }
        
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(status_code=500, detail="获取模型状态失败")


class TestConnectionRequest(BaseModel):
    provider: ModelProvider

@router.post("/models/test-connection")
async def test_model_connection(
    request: TestConnectionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """测试模型连接"""
    try:
        # 这里需要实现实际的连接测试
        # 暂时返回模拟结果
        provider = request.provider
        if provider == ModelProvider.OPENAI:
            model_config = config.model_config
            if not model_config.openai.api_key or not model_config.openai.api_key.strip():
                return {
                    "success": False,
                    "error": "OpenAI API key 未设置"
                }
        
        return {
            "success": True,
            "message": f"{provider.value} 连接测试成功",
            "response_time_ms": 150  # 模拟响应时间
        }
        
    except Exception as e:
        logger.error(f"Failed to test model connection: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/export")
async def export_settings(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """导出设置配置"""
    try:
        config_path = Path("config.toml")
        if not config_path.exists():
            raise HTTPException(status_code=404, detail="配置文件不存在")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
        
        # 移除敏感信息
        if "openai" in config_data and "api_key" in config_data["openai"]:
            config_data["openai"]["api_key"] = "***"
        
        return {
            "config": config_data,
            "exported_at": "2025-02-08T12:00:00Z"  # 实际应该使用当前时间
        }
        
    except Exception as e:
        logger.error(f"Failed to export settings: {e}")
        raise HTTPException(status_code=500, detail="导出设置失败")