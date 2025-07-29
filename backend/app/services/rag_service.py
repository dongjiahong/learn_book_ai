"""
RAG (Retrieval-Augmented Generation) service using LlamaIndex with Ollama focus
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.readers.file import PDFReader, EpubReader
import chromadb

from ..core.config import config
from ..core.model_config import ModelProvider

logger = logging.getLogger(__name__)


class SimpleEmbedding:
    """Simple embedding model for testing without external dependencies"""
    
    def __init__(self, embed_dim: int = 384):
        self.embed_dim = embed_dim
    
    def get_text_embedding(self, text: str) -> List[float]:
        """Generate a simple hash-based embedding"""
        import hashlib
        import struct
        
        # Create a simple hash-based embedding
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float vector
        embedding = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i:i+4]
            if len(chunk) == 4:
                val = struct.unpack('f', chunk)[0]
                embedding.append(val)
        
        # Pad or truncate to desired dimension
        while len(embedding) < self.embed_dim:
            embedding.extend(embedding[:min(len(embedding), self.embed_dim - len(embedding))])
        
        return embedding[:self.embed_dim]
    
    def get_text_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        return [self.get_text_embedding(text) for text in texts]


class RAGService:
    """RAG service for document processing and retrieval"""
    
    def __init__(self):
        self.index: Optional[VectorStoreIndex] = None
        self.chroma_client = None
        self.collection = None
        self.embed_model = None
        self._initialize_settings()
        self._initialize_vector_store()
    
    def _initialize_settings(self):
        """Initialize LlamaIndex global settings"""
        try:
            # Initialize LLM - focus on Ollama
            try:
                llm = Ollama(
                    model=config.model_config.ollama.model,
                    base_url=config.model_config.ollama.base_url,
                    temperature=config.model_config.ollama.temperature,
                    request_timeout=config.model_config.ollama.timeout
                )
                Settings.llm = llm
                logger.info(f"Ollama LLM initialized with model: {config.model_config.ollama.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama: {e}")
                # Continue without LLM for basic functionality
            
            # Initialize embedding based on configuration
            embed_model = None
            
            if config.model_config.embedding.provider == "ollama":
                try:
                    from llama_index.embeddings.ollama import OllamaEmbedding
                    
                    embed_model = OllamaEmbedding(
                        model_name=config.model_config.embedding.model,
                        base_url=config.model_config.ollama.base_url,
                        ollama_additional_kwargs={"mirostat": 0},
                    )
                    logger.info(f"Using Ollama embedding model: {config.model_config.embedding.model}")
                    
                except Exception as e:
                    logger.warning(f"Failed to initialize Ollama embedding model: {e}")
            
            elif config.model_config.embedding.provider == "openai":
                try:
                    from llama_index.embeddings.openai import OpenAIEmbedding
                    if config.model_config.openai.api_key:
                        embed_model = OpenAIEmbedding(
                            api_key=config.model_config.openai.api_key,
                            model="text-embedding-ada-002"
                        )
                        logger.info("Using OpenAI embedding model")
                    else:
                        logger.warning("OpenAI API key not configured")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI embedding model: {e}")
            
            # Fallback to simple local embedding if others fail
            if not embed_model:
                try:
                    from llama_index.core.embeddings import BaseEmbedding
                    
                    class LocalEmbedding(BaseEmbedding):
                        def __init__(self):
                            super().__init__()
                            self._embed_dim = config.model_config.embedding.dimension
                            self.simple_embed = SimpleEmbedding(self._embed_dim)
                        
                        def _get_text_embedding(self, text: str) -> List[float]:
                            return self.simple_embed.get_text_embedding(text)
                        
                        def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
                            return self.simple_embed.get_text_embedding_batch(texts)
                    
                    embed_model = LocalEmbedding()
                    logger.info("Using fallback local simple embedding model")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize any embedding model: {e}")
            
            # Set the embedding model
            if embed_model:
                Settings.embed_model = embed_model
                self.embed_model = embed_model
            else:
                logger.error("No embedding model could be initialized")
            
            # Initialize node parser
            Settings.node_parser = SentenceSplitter(
                chunk_size=1024,
                chunk_overlap=200
            )
            
            logger.info("LlamaIndex settings initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LlamaIndex settings: {e}")
            raise
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            # Initialize ChromaDB client
            persist_directory = config.vector_store_persist_directory
            os.makedirs(persist_directory, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(path=persist_directory)
            
            # Get or create collection
            collection_name = config.vector_store_collection_name
            try:
                self.collection = self.chroma_client.get_collection(collection_name)
                logger.info(f"Using existing ChromaDB collection: {collection_name}")
            except Exception:
                self.collection = self.chroma_client.create_collection(collection_name)
                logger.info(f"Created new ChromaDB collection: {collection_name}")
            
            # Create ChromaVectorStore
            vector_store = ChromaVectorStore(chroma_collection=self.collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Use our initialized embedding model
            embed_model = self.embed_model
            
            # Try to load existing index or create empty one
            try:
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context,
                    embed_model=embed_model
                )
                logger.info("Loaded existing vector index")
            except Exception:
                self.index = VectorStoreIndex(
                    nodes=[],
                    storage_context=storage_context,
                    embed_model=embed_model
                )
                logger.info("Created new empty vector index")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def load_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """Load and process documents into the vector store"""
        try:
            documents = []
            processed_files = []
            failed_files = []
            
            for file_path in file_paths:
                try:
                    file_path = Path(file_path)
                    if not file_path.exists():
                        failed_files.append({"file": str(file_path), "error": "File not found"})
                        continue
                    
                    # Determine file type and use appropriate reader
                    if file_path.suffix.lower() == '.pdf':
                        reader = PDFReader()
                        docs = reader.load_data(file_path)
                    elif file_path.suffix.lower() == '.epub':
                        reader = EpubReader()
                        docs = reader.load_data(file_path)
                    elif file_path.suffix.lower() in ['.txt', '.md']:
                        # Use SimpleDirectoryReader for text files
                        reader = SimpleDirectoryReader(
                            input_files=[str(file_path)]
                        )
                        docs = reader.load_data()
                    else:
                        failed_files.append({
                            "file": str(file_path), 
                            "error": f"Unsupported file type: {file_path.suffix}"
                        })
                        continue
                    
                    # Add metadata to documents
                    for doc in docs:
                        doc.metadata.update({
                            "file_path": str(file_path),
                            "file_name": file_path.name,
                            "file_type": file_path.suffix.lower()
                        })
                    
                    documents.extend(docs)
                    processed_files.append(str(file_path))
                    logger.info(f"Successfully loaded {len(docs)} documents from {file_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {e}")
                    failed_files.append({"file": str(file_path), "error": str(e)})
            
            if documents:
                # Add documents to index
                for doc in documents:
                    self.index.insert(doc)
                
                logger.info(f"Added {len(documents)} documents to vector index")
            
            return {
                "success": True,
                "processed_files": processed_files,
                "failed_files": failed_files,
                "total_documents": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_files": [],
                "failed_files": file_paths
            }
    
    async def query(self, query_text: str, top_k: int = 5) -> Dict[str, Any]:
        """Query the RAG system"""
        try:
            if not self.index:
                raise ValueError("Vector index not initialized")
            
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="compact"
            )
            
            # Execute query
            response = query_engine.query(query_text)
            
            # Extract source information
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    sources.append({
                        "content": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                        "metadata": node.metadata,
                        "score": getattr(node, 'score', None)
                    })
            
            return {
                "success": True,
                "response": str(response),
                "sources": sources,
                "query": query_text
            }
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query_text
            }
    
    async def get_similar_documents(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Get similar documents without generating response"""
        try:
            if not self.index:
                raise ValueError("Vector index not initialized")
            
            # Create retriever
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            
            # Retrieve similar nodes
            nodes = retriever.retrieve(query_text)
            
            similar_docs = []
            for node in nodes:
                similar_docs.append({
                    "content": node.text,
                    "metadata": node.metadata,
                    "score": getattr(node, 'score', None)
                })
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Failed to get similar documents: {e}")
            return []
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index"""
        try:
            if not self.index or not self.collection:
                return {"error": "Index not initialized"}
            
            # Get collection info
            collection_count = self.collection.count()
            
            return {
                "collection_name": config.vector_store_collection_name,
                "document_count": collection_count,
                "embedding_model": "local_simple",
                "embedding_dimension": 384,
                "chunk_size": 1024,
                "chunk_overlap": 200,
                "llm_model": config.model_config.ollama.model,
                "llm_provider": "ollama"
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"error": str(e)}
    
    async def clear_index(self) -> bool:
        """Clear all documents from the index"""
        try:
            if self.collection:
                # Delete the collection
                self.chroma_client.delete_collection(config.vector_store_collection_name)
                
                # Recreate the collection and index
                self.collection = self.chroma_client.create_collection(config.vector_store_collection_name)
                vector_store = ChromaVectorStore(chroma_collection=self.collection)
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                self.index = VectorStoreIndex(nodes=[], storage_context=storage_context)
                
                logger.info("Vector index cleared successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            return False


# Global RAG service instance
rag_service = RAGService()