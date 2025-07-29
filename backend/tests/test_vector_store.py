"""
Test cases for ChromaDB vector store
"""
import pytest
import tempfile
import shutil
import os
from unittest.mock import patch, MagicMock

from app.services.vector_store import ChromaVectorStore, get_vector_store


class TestChromaVectorStore:
    """Test cases for ChromaVectorStore"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def vector_store(self, temp_dir):
        """Create a vector store instance for testing"""
        with patch('app.core.config.config') as mock_config:
            mock_config.vector_store_persist_directory = temp_dir
            mock_config.embeddings_model = "sentence-transformers/all-MiniLM-L6-v2"
            
            store = ChromaVectorStore()
            return store
    
    def test_initialization(self, vector_store):
        """Test vector store initialization"""
        assert vector_store.client is not None
        assert vector_store.document_collection is not None
        assert vector_store.knowledge_point_collection is not None
        assert vector_store.embedding_function is not None
    
    def test_add_document_chunks(self, vector_store):
        """Test adding document chunks"""
        chunks = [
            "This is the first chunk of text.",
            "This is the second chunk of text.",
            "This is the third chunk of text."
        ]
        
        success = vector_store.add_document_chunks(
            document_id=1,
            knowledge_base_id=1,
            chunks=chunks,
            file_type="txt"
        )
        
        assert success is True
        
        # Verify chunks were added
        stats = vector_store.get_collection_stats()
        assert stats["document_chunks"] == 3
    
    def test_add_empty_chunks(self, vector_store):
        """Test adding empty chunks list"""
        success = vector_store.add_document_chunks(
            document_id=1,
            knowledge_base_id=1,
            chunks=[],
            file_type="txt"
        )
        
        assert success is True
        
        # Verify no chunks were added
        stats = vector_store.get_collection_stats()
        assert stats["document_chunks"] == 0
    
    def test_add_knowledge_points(self, vector_store):
        """Test adding knowledge points"""
        knowledge_points = [
            {
                "id": 1,
                "document_id": 1,
                "title": "Important Concept",
                "content": "This is an important concept to remember.",
                "importance_level": 3
            },
            {
                "id": 2,
                "document_id": 1,
                "title": "Key Formula",
                "content": "E = mc^2 is Einstein's famous equation.",
                "importance_level": 5
            }
        ]
        
        success = vector_store.add_knowledge_points(knowledge_points)
        
        assert success is True
        
        # Verify knowledge points were added
        stats = vector_store.get_collection_stats()
        assert stats["knowledge_points"] == 2
    
    def test_search_documents(self, vector_store):
        """Test document search functionality"""
        # First add some test chunks
        chunks = [
            "Python is a programming language.",
            "Machine learning is a subset of AI.",
            "Databases store structured data."
        ]
        
        vector_store.add_document_chunks(
            document_id=1,
            knowledge_base_id=1,
            chunks=chunks,
            file_type="txt"
        )
        
        # Search for relevant chunks
        results = vector_store.search_documents(
            query="programming language",
            n_results=2
        )
        
        assert len(results) <= 2
        assert all("content" in result for result in results)
        assert all("metadata" in result for result in results)
    
    def test_search_knowledge_points(self, vector_store):
        """Test knowledge point search functionality"""
        # First add some test knowledge points
        knowledge_points = [
            {
                "id": 1,
                "document_id": 1,
                "title": "Python Programming",
                "content": "Python is a high-level programming language.",
                "importance_level": 3
            },
            {
                "id": 2,
                "document_id": 1,
                "title": "Data Science",
                "content": "Data science involves analyzing data.",
                "importance_level": 4
            }
        ]
        
        vector_store.add_knowledge_points(knowledge_points)
        
        # Search for relevant knowledge points
        results = vector_store.search_knowledge_points(
            query="programming",
            n_results=2
        )
        
        assert len(results) <= 2
        assert all("content" in result for result in results)
        assert all("metadata" in result for result in results)
    
    def test_delete_document_chunks(self, vector_store):
        """Test deleting document chunks"""
        # First add some test chunks
        chunks = ["Test chunk 1", "Test chunk 2"]
        
        vector_store.add_document_chunks(
            document_id=1,
            knowledge_base_id=1,
            chunks=chunks,
            file_type="txt"
        )
        
        # Verify chunks were added
        stats = vector_store.get_collection_stats()
        assert stats["document_chunks"] == 2
        
        # Delete chunks
        success = vector_store.delete_document_chunks(document_id=1)
        assert success is True
        
        # Verify chunks were deleted
        stats = vector_store.get_collection_stats()
        assert stats["document_chunks"] == 0
    
    def test_delete_knowledge_points(self, vector_store):
        """Test deleting knowledge points"""
        # First add some test knowledge points
        knowledge_points = [
            {
                "id": 1,
                "document_id": 1,
                "title": "Test Point",
                "content": "Test content",
                "importance_level": 1
            }
        ]
        
        vector_store.add_knowledge_points(knowledge_points)
        
        # Verify knowledge points were added
        stats = vector_store.get_collection_stats()
        assert stats["knowledge_points"] == 1
        
        # Delete knowledge points
        success = vector_store.delete_knowledge_points(document_id=1)
        assert success is True
        
        # Verify knowledge points were deleted
        stats = vector_store.get_collection_stats()
        assert stats["knowledge_points"] == 0
    
    def test_get_collection_stats(self, vector_store):
        """Test getting collection statistics"""
        stats = vector_store.get_collection_stats()
        
        assert "document_chunks" in stats
        assert "knowledge_points" in stats
        assert "total_vectors" in stats
        assert isinstance(stats["document_chunks"], int)
        assert isinstance(stats["knowledge_points"], int)
        assert isinstance(stats["total_vectors"], int)
    
    def test_reset_collections(self, vector_store):
        """Test resetting collections"""
        # First add some test data
        chunks = ["Test chunk"]
        vector_store.add_document_chunks(1, 1, chunks, "txt")
        
        knowledge_points = [{
            "id": 1,
            "document_id": 1,
            "title": "Test",
            "content": "Test content",
            "importance_level": 1
        }]
        vector_store.add_knowledge_points(knowledge_points)
        
        # Verify data was added
        stats = vector_store.get_collection_stats()
        assert stats["document_chunks"] > 0 or stats["knowledge_points"] > 0
        
        # Reset collections
        success = vector_store.reset_collections()
        assert success is True
        
        # Verify collections were reset
        stats = vector_store.get_collection_stats()
        assert stats["document_chunks"] == 0
        assert stats["knowledge_points"] == 0
    
    def test_search_with_filters(self, vector_store):
        """Test search with metadata filters"""
        # Add chunks from different knowledge bases
        vector_store.add_document_chunks(1, 1, ["KB1 content"], "txt")
        vector_store.add_document_chunks(2, 2, ["KB2 content"], "txt")
        
        # Search with knowledge base filter
        results = vector_store.search_documents(
            query="content",
            knowledge_base_id=1,
            n_results=5
        )
        
        # Should only return results from KB1
        for result in results:
            assert result["metadata"]["knowledge_base_id"] == 1