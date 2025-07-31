"""
ChromaDB vector store service for document and knowledge point embeddings
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
import os
import requests
import json

from app.core.config import config

logger = logging.getLogger(__name__)


class OllamaEmbeddingFunction:
    """Custom embedding function for Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "shaw/dmeta-embedding-zh-small-q4"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._name = f"ollama-{model}"
    
    def name(self) -> str:
        """Return the name of the embedding function"""
        return self._name
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings for input texts"""
        import numpy as np
        embeddings = []
        
        for text in input:
            try:
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get("embedding", [])
                    if embedding:
                        # Convert to numpy array for ChromaDB compatibility
                        embeddings.append(np.array(embedding))
                    else:
                        logger.error(f"No embedding returned for text: {text[:50]}...")
                        # Use zero vector as fallback
                        embeddings.append(np.array([0.0] * 768))
                else:
                    logger.error(f"Ollama embedding request failed: {response.status_code} - {response.text}")
                    # Use zero vector as fallback
                    embeddings.append(np.array([0.0] * 768))
                    
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                # Use zero vector as fallback
                embeddings.append(np.array([0.0] * 768))
        
        return embeddings


class ChromaVectorStore:
    """ChromaDB vector store for managing document and knowledge point embeddings"""
    
    def __init__(self):
        self.client = None
        self.document_collection = None
        self.knowledge_point_collection = None
        self.embedding_function = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collections"""
        try:
            # Check if we should use remote ChromaDB or local persistent client
            if hasattr(config, 'vector_store_host') and config.vector_store_host != "localhost" or \
               hasattr(config, 'vector_store_port') and config.vector_store_port != 8000:
                # Use HTTP client for remote ChromaDB
                self.client = chromadb.HttpClient(
                    host=config.vector_store_host,
                    port=config.vector_store_port,
                    settings=Settings(
                        anonymized_telemetry=False
                    )
                )
                logger.info(f"Connected to remote ChromaDB at {config.vector_store_host}:{config.vector_store_port}")
            else:
                # Use HTTP client for local ChromaDB service on port 8000
                self.client = chromadb.HttpClient(
                    host="localhost",
                    port=8000,
                    settings=Settings(
                        anonymized_telemetry=False
                    )
                )
                logger.info("Connected to local ChromaDB service on port 8000")
            
            # Initialize embedding function based on provider
            if config.embeddings_provider == "ollama":
                # Use custom Ollama embedding function
                self.embedding_function = OllamaEmbeddingFunction(
                    base_url=config.ollama_base_url,
                    model=config.embeddings_model
                )
                logger.info(f"Using Ollama embedding function with model: {config.embeddings_model}")
            else:
                # Try to use sentence-transformers, fallback to default if not available
                try:
                    self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=config.embeddings_model
                    )
                    logger.info(f"Using SentenceTransformer embedding function with model: {config.embeddings_model}")
                except (ImportError, ValueError) as e:
                    logger.warning(f"Failed to load sentence-transformers: {e}")
                    logger.info("Using default embedding function")
                    self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            
            # Create or get document collection
            self.document_collection = self.client.get_or_create_collection(
                name="documents",
                embedding_function=self.embedding_function,
                metadata={"description": "Document chunks for RAG retrieval"}
            )
            
            # Create or get knowledge point collection
            self.knowledge_point_collection = self.client.get_or_create_collection(
                name="knowledge_points",
                embedding_function=self.embedding_function,
                metadata={"description": "Knowledge points for learning"}
            )
            
            logger.info("ChromaDB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def add_document_chunks(
        self,
        document_id: int,
        knowledge_base_id: int,
        chunks: List[str],
        file_type: str = "unknown"
    ) -> bool:
        """
        Add document chunks to the vector store
        
        Args:
            document_id: Database document ID
            knowledge_base_id: Database knowledge base ID
            chunks: List of text chunks
            file_type: Type of the source file
            
        Returns:
            bool: Success status
        """
        try:
            if not chunks:
                logger.warning(f"No chunks provided for document {document_id}")
                return True
            
            # Generate unique IDs for each chunk
            chunk_ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]
            
            # Create metadata for each chunk
            metadatas = [
                {
                    "document_id": document_id,
                    "knowledge_base_id": knowledge_base_id,
                    "chunk_index": i,
                    "file_type": file_type,
                    "content_type": "document_chunk"
                }
                for i in range(len(chunks))
            ]
            
            # Add to collection
            self.document_collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            logger.info(f"Added {len(chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document chunks: {e}")
            return False
    
    def add_knowledge_points(
        self,
        knowledge_points: List[Dict[str, Any]]
    ) -> bool:
        """
        Add knowledge points to the vector store
        
        Args:
            knowledge_points: List of knowledge point dictionaries with keys:
                - id: Knowledge point ID
                - document_id: Source document ID
                - title: Knowledge point title
                - content: Knowledge point content
                - importance_level: Importance level (1-5)
                
        Returns:
            bool: Success status
        """
        try:
            if not knowledge_points:
                logger.warning("No knowledge points provided")
                return True
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for kp in knowledge_points:
                # Combine title and content for better search
                content = f"{kp['title']}\n\n{kp['content']}"
                documents.append(content)
                
                metadatas.append({
                    "knowledge_point_id": kp["id"],
                    "document_id": kp["document_id"],
                    "title": kp["title"],
                    "importance_level": kp.get("importance_level", 1),
                    "content_type": "knowledge_point"
                })
                
                ids.append(f"kp_{kp['id']}")
            
            # Add to collection
            self.knowledge_point_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(knowledge_points)} knowledge points")
            return True
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to add knowledge points: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def search_documents(
        self,
        query: str,
        knowledge_base_id: Optional[int] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks
        
        Args:
            query: Search query
            knowledge_base_id: Optional knowledge base filter
            n_results: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        try:
            # Build where clause for filtering
            where_clause = {}
            if knowledge_base_id is not None:
                where_clause["knowledge_base_id"] = knowledge_base_id
            
            # Perform search
            results = self.document_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None,
                        "id": results["ids"][0][i]
                    })
            
            logger.info(f"Found {len(formatted_results)} document results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
    
    def search_knowledge_points(
        self,
        query: str,
        document_id: Optional[int] = None,
        importance_level: Optional[int] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge points
        
        Args:
            query: Search query
            document_id: Optional document filter
            importance_level: Optional importance level filter
            n_results: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        try:
            # Build where clause for filtering
            where_clause = {}
            if document_id is not None:
                where_clause["document_id"] = document_id
            if importance_level is not None:
                where_clause["importance_level"] = {"$gte": importance_level}
            
            # Perform search
            results = self.knowledge_point_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None,
                        "id": results["ids"][0][i]
                    })
            
            logger.info(f"Found {len(formatted_results)} knowledge point results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search knowledge points: {e}")
            return []
    
    def delete_document_chunks(self, document_id: int) -> bool:
        """
        Delete all chunks for a specific document
        
        Args:
            document_id: Database document ID
            
        Returns:
            bool: Success status
        """
        try:
            # Get all chunk IDs for this document
            results = self.document_collection.get(
                where={"document_id": document_id}
            )
            
            if results["ids"]:
                self.document_collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document chunks: {e}")
            return False
    
    def delete_knowledge_points(self, document_id: int) -> bool:
        """
        Delete all knowledge points for a specific document
        
        Args:
            document_id: Database document ID
            
        Returns:
            bool: Success status
        """
        try:
            # Get all knowledge point IDs for this document
            results = self.knowledge_point_collection.get(
                where={"document_id": document_id}
            )
            
            if results["ids"]:
                self.knowledge_point_collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} knowledge points for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge points: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector collections
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            doc_count = self.document_collection.count()
            kp_count = self.knowledge_point_collection.count()
            
            return {
                "document_chunks": doc_count,
                "knowledge_points": kp_count,
                "total_vectors": doc_count + kp_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def reset_collections(self) -> bool:
        """
        Reset all collections (delete all data)
        WARNING: This will delete all vector data!
        
        Returns:
            bool: Success status
        """
        try:
            self.client.delete_collection("documents")
            self.client.delete_collection("knowledge_points")
            
            # Recreate collections
            self.document_collection = self.client.create_collection(
                name="documents",
                embedding_function=self.embedding_function,
                metadata={"description": "Document chunks for RAG retrieval"}
            )
            
            self.knowledge_point_collection = self.client.create_collection(
                name="knowledge_points",
                embedding_function=self.embedding_function,
                metadata={"description": "Knowledge points for learning"}
            )
            
            logger.info("Vector collections reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collections: {e}")
            return False


# Global vector store instance (lazy initialization)
_vector_store_instance = None

def get_vector_store() -> ChromaVectorStore:
    """Get the global vector store instance"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = ChromaVectorStore()
    return _vector_store_instance