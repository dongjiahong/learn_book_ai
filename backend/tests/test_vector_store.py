"""
Unit tests for vector store functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from typing import List, Dict, Any

from app.services.vector_store import VectorStore, ChromaVectorStore
from app.services.rag_service import RAGService


class TestVectorStore:
    """Test base vector store functionality"""
    
    @pytest.fixture
    def mock_chroma_client(self):
        """Create a mock ChromaDB client"""
        mock_client = Mock()
        mock_collection = Mock()
        
        # Mock collection methods
        mock_collection.add = Mock()
        mock_collection.query = Mock()
        mock_collection.delete = Mock()
        mock_collection.get = Mock()
        mock_collection.count = Mock(return_value=0)
        
        # Mock client methods
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        mock_client.delete_collection = Mock()
        mock_client.list_collections = Mock(return_value=[])
        
        return mock_client, mock_collection
    
    @pytest.fixture
    def vector_store(self, mock_chroma_client):
        """Create a vector store instance with mocked ChromaDB"""
        mock_client, mock_collection = mock_chroma_client
        
        with patch('chromadb.Client', return_value=mock_client):
            store = ChromaVectorStore(
                persist_directory="./test_chroma_db",
                collection_name="test_collection"
            )
            store.collection = mock_collection
            return store, mock_collection
    
    def test_add_documents(self, vector_store):
        """Test adding documents to vector store"""
        store, mock_collection = vector_store
        
        documents = [
            {
                "id": "doc1",
                "content": "This is the first document about machine learning.",
                "metadata": {"source": "doc1.pdf", "page": 1}
            },
            {
                "id": "doc2", 
                "content": "This is the second document about deep learning.",
                "metadata": {"source": "doc2.pdf", "page": 1}
            }
        ]
        
        # Mock embedding generation
        with patch.object(store, '_generate_embeddings') as mock_embed:
            mock_embed.return_value = [
                [0.1, 0.2, 0.3, 0.4],  # Embedding for doc1
                [0.5, 0.6, 0.7, 0.8]   # Embedding for doc2
            ]
            
            store.add_documents(documents)
            
            # Verify collection.add was called with correct parameters
            mock_collection.add.assert_called_once()
            call_args = mock_collection.add.call_args[1]
            
            assert call_args["ids"] == ["doc1", "doc2"]
            assert call_args["documents"] == [doc["content"] for doc in documents]
            assert call_args["metadatas"] == [doc["metadata"] for doc in documents]
            assert len(call_args["embeddings"]) == 2
    
    def test_query_documents(self, vector_store):
        """Test querying documents from vector store"""
        store, mock_collection = vector_store
        
        # Mock query response
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "distances": [[0.1, 0.3]],
            "documents": [["First document content", "Second document content"]],
            "metadatas": [[{"source": "doc1.pdf"}, {"source": "doc2.pdf"}]]
        }
        
        # Mock embedding generation for query
        with patch.object(store, '_generate_embeddings') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3, 0.4]]
            
            results = store.query("machine learning", n_results=2)
            
            assert len(results["documents"][0]) == 2
            assert results["documents"][0][0] == "First document content"
            assert results["distances"][0][0] == 0.1
            mock_collection.query.assert_called_once()
    
    def test_delete_documents(self, vector_store):
        """Test deleting documents from vector store"""
        store, mock_collection = vector_store
        
        document_ids = ["doc1", "doc2"]
        store.delete_documents(document_ids)
        
        mock_collection.delete.assert_called_once_with(ids=document_ids)
    
    def test_get_document_count(self, vector_store):
        """Test getting document count"""
        store, mock_collection = vector_store
        
        mock_collection.count.return_value = 42
        
        count = store.get_document_count()
        
        assert count == 42
        mock_collection.count.assert_called_once()
    
    def test_similarity_search(self, vector_store):
        """Test similarity search functionality"""
        store, mock_collection = vector_store
        
        # Mock query response with similarity scores
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2", "doc3"]],
            "distances": [[0.1, 0.3, 0.8]],  # Lower distance = higher similarity
            "documents": [["Relevant doc", "Somewhat relevant", "Less relevant"]],
            "metadatas": [[{"source": "doc1.pdf"}, {"source": "doc2.pdf"}, {"source": "doc3.pdf"}]]
        }
        
        with patch.object(store, '_generate_embeddings') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3, 0.4]]
            
            results = store.similarity_search("test query", threshold=0.5, n_results=3)
            
            # Should return only documents with distance <= threshold
            assert len(results["documents"][0]) == 2  # doc1 and doc2 pass threshold
            assert results["distances"][0][0] == 0.1  # Most similar first
            assert results["distances"][0][1] == 0.3  # Second most similar
    
    def test_batch_add_documents(self, vector_store):
        """Test adding documents in batches"""
        store, mock_collection = vector_store
        
        # Create many documents
        documents = []
        for i in range(150):  # More than typical batch size
            documents.append({
                "id": f"doc{i}",
                "content": f"Document {i} content",
                "metadata": {"source": f"doc{i}.pdf"}
            })
        
        with patch.object(store, '_generate_embeddings') as mock_embed:
            # Mock embeddings for all documents
            mock_embed.return_value = [[0.1, 0.2, 0.3, 0.4]] * len(documents)
            
            store.add_documents(documents, batch_size=50)
            
            # Should be called multiple times for batching
            assert mock_collection.add.call_count >= 3  # 150 docs / 50 batch size
    
    def test_update_document(self, vector_store):
        """Test updating a document in vector store"""
        store, mock_collection = vector_store
        
        # Mock existing document check
        mock_collection.get.return_value = {
            "ids": ["doc1"],
            "documents": ["Old content"],
            "metadatas": [{"source": "doc1.pdf"}]
        }
        
        updated_doc = {
            "id": "doc1",
            "content": "Updated document content",
            "metadata": {"source": "doc1.pdf", "updated": True}
        }
        
        with patch.object(store, '_generate_embeddings') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3, 0.4]]
            
            store.update_document(updated_doc)
            
            # Should delete old and add new
            mock_collection.delete.assert_called_once_with(ids=["doc1"])
            mock_collection.add.assert_called_once()
    
    def test_get_documents_by_metadata(self, vector_store):
        """Test getting documents by metadata filter"""
        store, mock_collection = vector_store
        
        # Mock filtered query response
        mock_collection.get.return_value = {
            "ids": ["doc1", "doc2"],
            "documents": ["Doc 1 content", "Doc 2 content"],
            "metadatas": [{"source": "doc1.pdf", "type": "research"}, {"source": "doc2.pdf", "type": "research"}]
        }
        
        results = store.get_documents_by_metadata({"type": "research"})
        
        assert len(results["ids"]) == 2
        assert all("research" in meta["type"] for meta in results["metadatas"])
        mock_collection.get.assert_called_once()


class TestRAGServiceIntegration:
    """Test RAG service integration with vector store"""
    
    @pytest.fixture
    def mock_rag_service(self):
        """Create a mock RAG service"""
        with patch('app.services.rag_service.ChromaVectorStore') as mock_store_class, \
             patch('app.services.rag_service.Settings') as mock_settings:
            
            # Mock vector store instance
            mock_store = Mock()
            mock_store_class.return_value = mock_store
            
            # Create RAG service
            rag_service = RAGService()
            rag_service.vector_store = mock_store
            
            return rag_service, mock_store
    
    @pytest.mark.asyncio
    async def test_add_document_to_rag(self, mock_rag_service):
        """Test adding document to RAG system"""
        rag_service, mock_store = mock_rag_service
        
        document_content = "This is a test document about machine learning algorithms."
        document_metadata = {
            "document_id": 1,
            "filename": "ml_doc.pdf",
            "knowledge_base_id": 1
        }
        
        # Mock document processing
        with patch.object(rag_service, '_process_document_content') as mock_process:
            mock_process.return_value = [
                {
                    "id": "chunk_1",
                    "content": "This is a test document",
                    "metadata": {**document_metadata, "chunk_index": 0}
                },
                {
                    "id": "chunk_2", 
                    "content": "about machine learning algorithms",
                    "metadata": {**document_metadata, "chunk_index": 1}
                }
            ]
            
            result = await rag_service.add_document(document_content, document_metadata)
            
            assert result is True
            mock_store.add_documents.assert_called_once()
            
            # Verify chunks were created correctly
            call_args = mock_store.add_documents.call_args[0][0]
            assert len(call_args) == 2
            assert call_args[0]["id"] == "chunk_1"
            assert call_args[1]["id"] == "chunk_2"
    
    @pytest.mark.asyncio
    async def test_query_rag_system(self, mock_rag_service):
        """Test querying the RAG system"""
        rag_service, mock_store = mock_rag_service
        
        # Mock vector store query response
        mock_store.query.return_value = {
            "documents": [["Relevant document content", "Another relevant content"]],
            "metadatas": [[{"document_id": 1, "chunk_index": 0}, {"document_id": 2, "chunk_index": 0}]],
            "distances": [[0.1, 0.3]]
        }
        
        # Mock LLM response
        with patch.object(rag_service, '_generate_response_with_context') as mock_generate:
            mock_generate.return_value = "Generated response based on context"
            
            result = await rag_service.query("What is machine learning?")
            
            assert result["response"] == "Generated response based on context"
            assert len(result["source_nodes"]) == 2
            mock_store.query.assert_called_once()
    
    def test_document_chunking(self, mock_rag_service):
        """Test document content chunking"""
        rag_service, _ = mock_rag_service
        
        # Long document content
        long_content = "This is a very long document. " * 100  # Repeat to make it long
        
        chunks = rag_service._chunk_document(long_content, chunk_size=200, overlap=50)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 250 for chunk in chunks)  # chunk_size + some tolerance
        
        # Check overlap
        if len(chunks) > 1:
            # Should have some overlap between consecutive chunks
            assert chunks[0][-20:] in chunks[1] or chunks[1][:20] in chunks[0]
    
    def test_metadata_enrichment(self, mock_rag_service):
        """Test metadata enrichment for document chunks"""
        rag_service, _ = mock_rag_service
        
        base_metadata = {
            "document_id": 1,
            "filename": "test.pdf",
            "knowledge_base_id": 1
        }
        
        chunks = ["First chunk content", "Second chunk content"]
        
        enriched_chunks = rag_service._enrich_chunks_with_metadata(chunks, base_metadata)
        
        assert len(enriched_chunks) == 2
        assert enriched_chunks[0]["metadata"]["chunk_index"] == 0
        assert enriched_chunks[1]["metadata"]["chunk_index"] == 1
        assert all(chunk["metadata"]["document_id"] == 1 for chunk in enriched_chunks)
    
    @pytest.mark.asyncio
    async def test_remove_document_from_rag(self, mock_rag_service):
        """Test removing document from RAG system"""
        rag_service, mock_store = mock_rag_service
        
        document_id = 1
        
        # Mock getting document chunks
        mock_store.get_documents_by_metadata.return_value = {
            "ids": ["chunk_1", "chunk_2", "chunk_3"],
            "documents": ["Content 1", "Content 2", "Content 3"],
            "metadatas": [
                {"document_id": 1, "chunk_index": 0},
                {"document_id": 1, "chunk_index": 1},
                {"document_id": 1, "chunk_index": 2}
            ]
        }
        
        result = await rag_service.remove_document(document_id)
        
        assert result is True
        mock_store.get_documents_by_metadata.assert_called_once_with({"document_id": document_id})
        mock_store.delete_documents.assert_called_once_with(["chunk_1", "chunk_2", "chunk_3"])


class TestVectorStorePerformance:
    """Test vector store performance with larger datasets"""
    
    @pytest.fixture
    def large_dataset(self):
        """Create a large dataset for performance testing"""
        documents = []
        for i in range(1000):
            documents.append({
                "id": f"doc_{i}",
                "content": f"This is document {i} with some content about topic {i % 10}.",
                "metadata": {
                    "source": f"doc_{i}.pdf",
                    "topic": f"topic_{i % 10}",
                    "page": i % 50
                }
            })
        return documents
    
    def test_bulk_insert_performance(self, vector_store, large_dataset):
        """Test performance of bulk document insertion"""
        store, mock_collection = vector_store
        
        with patch.object(store, '_generate_embeddings') as mock_embed:
            # Mock embeddings for all documents
            mock_embed.return_value = [[0.1, 0.2, 0.3, 0.4]] * len(large_dataset)
            
            # Should handle large dataset efficiently
            store.add_documents(large_dataset, batch_size=100)
            
            # Verify batching occurred
            assert mock_collection.add.call_count == 10  # 1000 docs / 100 batch size
    
    def test_query_performance_with_large_dataset(self, vector_store):
        """Test query performance with large result sets"""
        store, mock_collection = vector_store
        
        # Mock large query response
        large_response = {
            "ids": [["doc_" + str(i) for i in range(100)]],
            "distances": [[0.1 + i * 0.01 for i in range(100)]],
            "documents": [[f"Document {i} content" for i in range(100)]],
            "metadatas": [[{"source": f"doc_{i}.pdf"} for i in range(100)]]
        }
        
        mock_collection.query.return_value = large_response
        
        with patch.object(store, '_generate_embeddings') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3, 0.4]]
            
            results = store.query("test query", n_results=100)
            
            assert len(results["documents"][0]) == 100
            # Results should be sorted by similarity (distance)
            distances = results["distances"][0]
            assert all(distances[i] <= distances[i+1] for i in range(len(distances)-1))


class TestVectorStoreErrorHandling:
    """Test error handling in vector store operations"""
    
    def test_connection_error_handling(self):
        """Test handling of connection errors"""
        with patch('chromadb.Client') as mock_client_class:
            mock_client_class.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                ChromaVectorStore(persist_directory="./test_db")
    
    def test_invalid_embedding_dimensions(self, vector_store):
        """Test handling of invalid embedding dimensions"""
        store, mock_collection = vector_store
        
        documents = [{"id": "doc1", "content": "Test content", "metadata": {}}]
        
        with patch.object(store, '_generate_embeddings') as mock_embed:
            # Return embeddings with wrong dimensions
            mock_embed.return_value = [[0.1, 0.2]]  # Too few dimensions
            
            # Should handle dimension mismatch gracefully
            with pytest.raises((ValueError, Exception)):
                store.add_documents(documents)
    
    def test_empty_query_handling(self, vector_store):
        """Test handling of empty queries"""
        store, mock_collection = vector_store
        
        with patch.object(store, '_generate_embeddings') as mock_embed:
            mock_embed.return_value = [[]]
            
            # Should handle empty query gracefully
            results = store.query("", n_results=5)
            
            # Should return empty results or handle appropriately
            assert results is not None
    
    def test_duplicate_document_id_handling(self, vector_store):
        """Test handling of duplicate document IDs"""
        store, mock_collection = vector_store
        
        # Mock existing document
        mock_collection.get.return_value = {
            "ids": ["doc1"],
            "documents": ["Existing content"],
            "metadatas": [{"source": "existing.pdf"}]
        }
        
        duplicate_doc = {
            "id": "doc1",
            "content": "Duplicate content",
            "metadata": {"source": "duplicate.pdf"}
        }
        
        with patch.object(store, '_generate_embeddings') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3, 0.4]]
            
            # Should handle duplicate by updating
            store.add_documents([duplicate_doc])
            
            # Should have called delete and add for update
            mock_collection.delete.assert_called()
            mock_collection.add.assert_called()