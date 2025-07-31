import toml
from pathlib import Path
from typing import Dict, Any, List, Optional
from .model_config import ModelConfig, ModelProvider, OpenAIConfig, OllamaConfig, EmbeddingConfig

class Config:
    """Configuration loader for the RAG Learning Platform"""
    
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from TOML file"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = toml.load(f)
        else:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        # Initialize model configuration
        self._model_config = self._create_model_config()
    
    def _create_model_config(self) -> ModelConfig:
        """Create model configuration from TOML data"""
        try:
            # Extract model configuration sections
            llm_section = self._config.get("llm", {})
            openai_section = self._config.get("openai", {})
            ollama_section = self._config.get("ollama", {})
            embeddings_section = self._config.get("embeddings", {})
            
            # Create provider-specific configs
            api_key = openai_section.get("api_key", "")
            openai_config = OpenAIConfig(
                api_key=api_key if api_key else None,
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
            
            # Determine provider and fallback
            provider_str = llm_section.get("provider", "ollama")
            provider = ModelProvider(provider_str)
            
            fallback_str = llm_section.get("fallback_provider")
            fallback_provider = ModelProvider(fallback_str) if fallback_str else None
            
            return ModelConfig(
                provider=provider,
                openai=openai_config,
                ollama=ollama_config,
                embedding=embedding_config,
                fallback_provider=fallback_provider,
                health_check_interval=llm_section.get("health_check_interval", 300)
            )
            
        except Exception as e:
            raise ValueError(f"Invalid model configuration: {e}")
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value"""
        if key is None:
            return self._config.get(section, default)
        return self._config.get(section, {}).get(key, default)
    
    @property
    def database_url(self) -> str:
        return self.get("database", "url", "sqlite:///./rag_learning.db")
    
    @property
    def database_echo(self) -> bool:
        return self.get("database", "echo", False)
    
    @property
    def secret_key(self) -> str:
        return self.get("auth", "secret_key", "your-secret-key-here")
    
    @property
    def algorithm(self) -> str:
        return self.get("auth", "algorithm", "HS256")
    
    @property
    def access_token_expire_minutes(self) -> int:
        return self.get("auth", "access_token_expire_minutes", 30)
    
    @property
    def llm_provider(self) -> str:
        return self.get("llm", "provider", "ollama")
    
    @property
    def llm_model(self) -> str:
        return self.get("llm", "model", "llama2")
    
    @property
    def llm_temperature(self) -> float:
        return self.get("llm", "temperature", 0.7)
    
    @property
    def llm_max_tokens(self) -> int:
        return self.get("llm", "max_tokens", 2048)
    
    @property
    def openai_api_key(self) -> str:
        return self.get("openai", "api_key", "")
    
    @property
    def openai_model(self) -> str:
        return self.get("openai", "model", "gpt-3.5-turbo")
    
    @property
    def ollama_base_url(self) -> str:
        return self.get("ollama", "base_url", "http://localhost:11434")
    
    @property
    def ollama_model(self) -> str:
        return self.get("ollama", "model", "llama2")
    
    @property
    def embeddings_provider(self) -> str:
        return self.get("embeddings", "provider", "huggingface")
    
    @property
    def embeddings_model(self) -> str:
        return self.get("embeddings", "model", "sentence-transformers/all-MiniLM-L6-v2")
    
    @property
    def embeddings_dimension(self) -> int:
        return self.get("embeddings", "dimension", 384)
    
    @property
    def vector_store_provider(self) -> str:
        return self.get("vector_store", "provider", "chroma")
    
    @property
    def vector_store_persist_directory(self) -> str:
        return self.get("vector_store", "persist_directory", "./chroma_db")
    
    @property
    def vector_store_host(self) -> str:
        return self.get("vector_store", "host", "localhost")
    
    @property
    def vector_store_port(self) -> int:
        return self.get("vector_store", "port", 8000)
    
    @property
    def vector_store_collection_name(self) -> str:
        return self.get("vector_store", "collection_name", "learning_materials")
    
    @property
    def anki_deck_name(self) -> str:
        return self.get("anki", "deck_name", "RAG Learning Deck")
    
    @property
    def anki_model_name(self) -> str:
        return self.get("anki", "model_name", "Basic")
    
    @property
    def server_host(self) -> str:
        return self.get("server", "host", "0.0.0.0")
    
    @property
    def server_port(self) -> int:
        return self.get("server", "port", 8000)
    
    @property
    def server_debug(self) -> bool:
        return self.get("server", "debug", True)
    
    @property
    def server_reload(self) -> bool:
        return self.get("server", "reload", True)
    
    @property
    def cors_allow_origins(self) -> List[str]:
        return self.get("cors", "allow_origins", ["http://localhost:3000"])
    
    @property
    def cors_allow_credentials(self) -> bool:
        return self.get("cors", "allow_credentials", True)
    
    @property
    def cors_allow_methods(self) -> List[str]:
        return self.get("cors", "allow_methods", ["*"])
    
    @property
    def cors_allow_headers(self) -> List[str]:
        return self.get("cors", "allow_headers", ["*"])
    
    @property
    def model_config(self) -> ModelConfig:
        """Get model configuration"""
        return self._model_config
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self.load_config()
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate database configuration
        if not self.database_url:
            validation_results["errors"].append("Database URL is required")
            validation_results["valid"] = False
        
        # Validate auth configuration
        if self.secret_key == "your-secret-key-here":
            validation_results["warnings"].append("Using default secret key - change for production")
        
        # Validate model configuration
        try:
            model_config = self.model_config
            
            # Check if at least one model provider is properly configured
            has_valid_provider = False
            
            if model_config.provider == ModelProvider.OPENAI:
                if not model_config.openai.api_key or not model_config.openai.api_key.strip():
                    validation_results["errors"].append("OpenAI API key is required when using OpenAI provider")
                    validation_results["valid"] = False
                else:
                    has_valid_provider = True
            
            if model_config.provider == ModelProvider.OLLAMA:
                if not model_config.ollama.base_url:
                    validation_results["errors"].append("Ollama base URL is required when using Ollama provider")
                    validation_results["valid"] = False
                else:
                    has_valid_provider = True
            
            if not has_valid_provider:
                validation_results["errors"].append("No valid model provider configured")
                validation_results["valid"] = False
                
        except Exception as e:
            validation_results["errors"].append(f"Model configuration error: {e}")
            validation_results["valid"] = False
        
        return validation_results

# Global configuration instance
config = Config()