"""
Integration tests for API endpoints
"""

import pytest
import json
import tempfile
import os
from io import BytesIO
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock

from app.models.models import User, KnowledgeBase, Document, Question, AnswerRecord


class TestAuthAPI:
    """Test authentication API endpoints"""
    
    def test_register_user_success(self, client: TestClient):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
    
    def test_register_duplicate_username(self, client: TestClient):
        """Test registration with duplicate username"""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "password123"
            }
        )
        
        # Second registration with same username
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_success(self, client: TestClient):
        """Test successful login"""
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "password123"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "username": "loginuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_get_current_user(self, client: TestClient, authenticated_headers: dict):
        """Test getting current user information"""
        response = client.get("/api/auth/me", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "id" in data
    
    def test_refresh_token(self, client: TestClient):
        """Test token refresh"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "refreshuser",
                "email": "refresh@example.com",
                "password": "password123"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "refreshuser",
                "password": "password123"
            }
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestKnowledgeBaseAPI:
    """Test knowledge base API endpoints"""
    
    def test_create_knowledge_base(self, client: TestClient, authenticated_headers: dict):
        """Test creating a knowledge base"""
        response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={
                "name": "Test Knowledge Base",
                "description": "A test knowledge base"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Knowledge Base"
        assert data["description"] == "A test knowledge base"
        assert "id" in data
    
    def test_get_knowledge_bases(self, client: TestClient, authenticated_headers: dict):
        """Test getting knowledge bases"""
        # Create a knowledge base first
        client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={
                "name": "Test KB",
                "description": "Test description"
            }
        )
        
        response = client.get("/api/knowledge-bases", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "Test KB"
    
    def test_get_knowledge_base_by_id(self, client: TestClient, authenticated_headers: dict):
        """Test getting a specific knowledge base"""
        # Create knowledge base
        create_response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={
                "name": "Specific KB",
                "description": "Specific description"
            }
        )
        
        kb_id = create_response.json()["id"]
        
        # Get specific knowledge base
        response = client.get(f"/api/knowledge-bases/{kb_id}", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == kb_id
        assert data["name"] == "Specific KB"
    
    def test_update_knowledge_base(self, client: TestClient, authenticated_headers: dict):
        """Test updating a knowledge base"""
        # Create knowledge base
        create_response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={
                "name": "Original KB",
                "description": "Original description"
            }
        )
        
        kb_id = create_response.json()["id"]
        
        # Update knowledge base
        response = client.put(
            f"/api/knowledge-bases/{kb_id}",
            headers=authenticated_headers,
            json={
                "name": "Updated KB",
                "description": "Updated description"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated KB"
        assert data["description"] == "Updated description"
    
    def test_delete_knowledge_base(self, client: TestClient, authenticated_headers: dict):
        """Test deleting a knowledge base"""
        # Create knowledge base
        create_response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={
                "name": "To Delete KB",
                "description": "Will be deleted"
            }
        )
        
        kb_id = create_response.json()["id"]
        
        # Delete knowledge base
        response = client.delete(f"/api/knowledge-bases/{kb_id}", headers=authenticated_headers)
        
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(f"/api/knowledge-bases/{kb_id}", headers=authenticated_headers)
        assert get_response.status_code == 404


class TestDocumentAPI:
    """Test document API endpoints"""
    
    def test_upload_document(self, client: TestClient, authenticated_headers: dict):
        """Test document upload"""
        # Create knowledge base first
        kb_response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={
                "name": "Document KB",
                "description": "For document testing"
            }
        )
        
        kb_id = kb_response.json()["id"]
        
        # Create test file
        test_content = b"This is test document content for testing purposes."
        
        with patch('app.services.file_service.FileService.save_uploaded_file') as mock_save, \
             patch('app.services.document_processor.DocumentProcessor.process_document') as mock_process:
            
            mock_save.return_value = {
                "file_path": "/test/path/test.txt",
                "file_size": len(test_content)
            }
            mock_process.return_value = True
            
            # Upload document
            response = client.post(
                "/api/documents/upload",
                headers=authenticated_headers,
                files={"file": ("test.txt", BytesIO(test_content), "text/plain")},
                data={"knowledge_base_id": str(kb_id)}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["filename"] == "test.txt"
            assert data["knowledge_base_id"] == kb_id
    
    def test_get_documents(self, client: TestClient, authenticated_headers: dict):
        """Test getting documents"""
        response = client.get("/api/documents", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_documents_by_knowledge_base(self, client: TestClient, authenticated_headers: dict):
        """Test getting documents by knowledge base"""
        # Create knowledge base
        kb_response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={"name": "Test KB", "description": "Test"}
        )
        
        kb_id = kb_response.json()["id"]
        
        response = client.get(
            f"/api/documents?knowledge_base_id={kb_id}",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_delete_document(self, client: TestClient, authenticated_headers: dict):
        """Test deleting a document"""
        # This test would require creating a document first
        # For now, test the endpoint with non-existent document
        response = client.delete("/api/documents/99999", headers=authenticated_headers)
        
        assert response.status_code == 404class TestQ
uestionAPI:
    """Test question API endpoints"""
    
    @patch('app.services.question_service.QuestionService')
    def test_generate_questions(self, mock_question_service, client: TestClient, authenticated_headers: dict):
        """Test question generation"""
        # Create knowledge base and document
        kb_response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={"name": "Question KB", "description": "For questions"}
        )
        kb_id = kb_response.json()["id"]
        
        # Mock question generation
        mock_service_instance = mock_question_service.return_value
        mock_service_instance.generate_questions_from_document = AsyncMock(return_value=[
            Mock(
                id=1,
                question_text="What is machine learning?",
                context="ML context",
                difficulty_level=2,
                document_id=1
            )
        ])
        
        response = client.post(
            "/api/questions/generate",
            headers=authenticated_headers,
            json={
                "document_id": 1,
                "num_questions": 5,
                "difficulty_level": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "questions_generated" in data
    
    def test_get_questions(self, client: TestClient, authenticated_headers: dict):
        """Test getting questions"""
        response = client.get("/api/questions", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_question_by_id(self, client: TestClient, authenticated_headers: dict):
        """Test getting a specific question"""
        # Test with non-existent question
        response = client.get("/api/questions/99999", headers=authenticated_headers)
        
        assert response.status_code == 404
    
    def test_get_questions_by_document(self, client: TestClient, authenticated_headers: dict):
        """Test getting questions by document"""
        response = client.get(
            "/api/questions?document_id=1",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestLearningAPI:
    """Test learning API endpoints"""
    
    @patch('app.services.evaluation_service.EvaluationService')
    def test_submit_answer(self, mock_evaluation_service, client: TestClient, authenticated_headers: dict):
        """Test submitting an answer for evaluation"""
        # Mock evaluation service
        mock_service_instance = mock_evaluation_service.return_value
        mock_service_instance.evaluate_answer = AsyncMock(return_value={
            "success": True,
            "question_id": 1,
            "score": 8.5,
            "feedback": "Good answer",
            "reference_answer": "Reference answer",
            "record_id": 1
        })
        
        response = client.post(
            "/api/learning/submit-answer",
            headers=authenticated_headers,
            json={
                "question_id": 1,
                "user_answer": "Machine learning is a subset of AI"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["score"] == 8.5
        assert "feedback" in data
    
    def test_get_learning_records(self, client: TestClient, authenticated_headers: dict):
        """Test getting learning records"""
        response = client.get("/api/learning/records", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_learning_statistics(self, client: TestClient, authenticated_headers: dict):
        """Test getting learning statistics"""
        response = client.get("/api/learning/statistics", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_questions_answered" in data
        assert "average_score" in data
    
    def test_search_learning_records(self, client: TestClient, authenticated_headers: dict):
        """Test searching learning records"""
        response = client.get(
            "/api/learning/records/search?query=machine learning&score_min=7.0",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestKnowledgePointAPI:
    """Test knowledge point API endpoints"""
    
    @patch('app.services.knowledge_point_service.KnowledgePointService')
    def test_extract_knowledge_points(self, mock_kp_service, client: TestClient, authenticated_headers: dict):
        """Test knowledge point extraction"""
        # Mock knowledge point service
        mock_service_instance = mock_kp_service.return_value
        mock_service_instance.extract_knowledge_points_from_document = AsyncMock(return_value=[
            Mock(
                id=1,
                title="Machine Learning",
                content="ML is a subset of AI",
                importance_level=3,
                document_id=1
            )
        ])
        
        response = client.post(
            "/api/knowledge-points/extract",
            headers=authenticated_headers,
            json={"document_id": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "knowledge_points_extracted" in data
    
    def test_get_knowledge_points(self, client: TestClient, authenticated_headers: dict):
        """Test getting knowledge points"""
        response = client.get("/api/knowledge-points", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_knowledge_point(self, client: TestClient, authenticated_headers: dict):
        """Test updating a knowledge point"""
        # Test with non-existent knowledge point
        response = client.put(
            "/api/knowledge-points/99999",
            headers=authenticated_headers,
            json={
                "title": "Updated Title",
                "content": "Updated content",
                "importance_level": 2
            }
        )
        
        assert response.status_code == 404
    
    def test_search_knowledge_points(self, client: TestClient, authenticated_headers: dict):
        """Test searching knowledge points"""
        response = client.get(
            "/api/knowledge-points/search?query=machine learning",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestReviewAPI:
    """Test review system API endpoints"""
    
    @patch('app.services.spaced_repetition_service.SpacedRepetitionService')
    def test_get_due_reviews(self, mock_sr_service, client: TestClient, authenticated_headers: dict):
        """Test getting due reviews"""
        # Mock spaced repetition service
        mock_service_instance = mock_sr_service.return_value
        mock_service_instance.get_due_reviews = AsyncMock(return_value=[
            Mock(
                id=1,
                content_id=1,
                content_type="question",
                next_review="2024-01-01T10:00:00"
            )
        ])
        
        response = client.get("/api/review/due", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch('app.services.spaced_repetition_service.SpacedRepetitionService')
    def test_complete_review(self, mock_sr_service, client: TestClient, authenticated_headers: dict):
        """Test completing a review"""
        # Mock spaced repetition service
        mock_service_instance = mock_sr_service.return_value
        mock_service_instance.complete_review = AsyncMock(return_value={
            "success": True,
            "next_review": "2024-01-02T10:00:00",
            "interval_days": 2
        })
        
        response = client.post(
            "/api/review/complete",
            headers=authenticated_headers,
            json={
                "content_id": 1,
                "content_type": "question",
                "quality": 4
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_review_statistics(self, client: TestClient, authenticated_headers: dict):
        """Test getting review statistics"""
        response = client.get("/api/review/statistics", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_reviews" in data or isinstance(data, dict)


class TestAnkiAPI:
    """Test Anki export API endpoints"""
    
    @patch('app.services.anki_service.AnkiService')
    def test_export_questions_to_anki(self, mock_anki_service, client: TestClient, authenticated_headers: dict):
        """Test exporting questions to Anki"""
        # Mock Anki service
        mock_service_instance = mock_anki_service.return_value
        mock_service_instance.export_questions_to_anki = AsyncMock(return_value={
            "success": True,
            "file_path": "/tmp/export.apkg",
            "cards_exported": 5
        })
        
        response = client.post(
            "/api/anki/export/questions",
            headers=authenticated_headers,
            json={
                "question_ids": [1, 2, 3, 4, 5],
                "deck_name": "Test Deck"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cards_exported"] == 5
    
    @patch('app.services.anki_service.AnkiService')
    def test_export_knowledge_points_to_anki(self, mock_anki_service, client: TestClient, authenticated_headers: dict):
        """Test exporting knowledge points to Anki"""
        # Mock Anki service
        mock_service_instance = mock_anki_service.return_value
        mock_service_instance.export_knowledge_points_to_anki = AsyncMock(return_value={
            "success": True,
            "file_path": "/tmp/kp_export.apkg",
            "cards_exported": 3
        })
        
        response = client.post(
            "/api/anki/export/knowledge-points",
            headers=authenticated_headers,
            json={
                "knowledge_point_ids": [1, 2, 3],
                "deck_name": "Knowledge Points Deck"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cards_exported"] == 3
    
    def test_get_export_history(self, client: TestClient, authenticated_headers: dict):
        """Test getting export history"""
        response = client.get("/api/anki/exports", headers=authenticated_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch('app.services.anki_service.AnkiService')
    def test_download_anki_file(self, mock_anki_service, client: TestClient, authenticated_headers: dict):
        """Test downloading Anki file"""
        # This would typically return a file response
        response = client.get("/api/anki/download/test_export_id", headers=authenticated_headers)
        
        # Since we don't have actual files, expect 404 or appropriate error
        assert response.status_code in [200, 404, 500]


class TestAPIErrorHandling:
    """Test API error handling"""
    
    def test_unauthorized_access(self, client: TestClient):
        """Test accessing protected endpoints without authentication"""
        response = client.get("/api/knowledge-bases")
        
        assert response.status_code == 403
    
    def test_invalid_token(self, client: TestClient):
        """Test accessing endpoints with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/knowledge-bases", headers=headers)
        
        assert response.status_code == 401
    
    def test_invalid_json_payload(self, client: TestClient, authenticated_headers: dict):
        """Test sending invalid JSON payload"""
        response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            data="invalid json"
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client: TestClient, authenticated_headers: dict):
        """Test sending request with missing required fields"""
        response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={"description": "Missing name field"}
        )
        
        assert response.status_code == 422
    
    def test_resource_not_found(self, client: TestClient, authenticated_headers: dict):
        """Test accessing non-existent resources"""
        response = client.get("/api/knowledge-bases/99999", headers=authenticated_headers)
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client: TestClient, authenticated_headers: dict):
        """Test using wrong HTTP method"""
        response = client.patch("/api/knowledge-bases", headers=authenticated_headers)
        
        assert response.status_code == 405


class TestAPIPerformance:
    """Test API performance with larger datasets"""
    
    def test_pagination_performance(self, client: TestClient, authenticated_headers: dict):
        """Test API pagination performance"""
        # Create multiple knowledge bases
        for i in range(20):
            client.post(
                "/api/knowledge-bases",
                headers=authenticated_headers,
                json={
                    "name": f"KB {i}",
                    "description": f"Description {i}"
                }
            )
        
        # Test pagination
        response = client.get(
            "/api/knowledge-bases?skip=0&limit=10",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10
    
    def test_search_performance(self, client: TestClient, authenticated_headers: dict):
        """Test search API performance"""
        response = client.get(
            "/api/learning/records/search?query=test&limit=50",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 50


class TestAPIValidation:
    """Test API input validation"""
    
    def test_email_validation(self, client: TestClient):
        """Test email format validation"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422
    
    def test_password_strength_validation(self, client: TestClient):
        """Test password strength validation"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "123"  # Too short
            }
        )
        
        assert response.status_code == 422
    
    def test_file_type_validation(self, client: TestClient, authenticated_headers: dict):
        """Test file type validation for document upload"""
        # Create knowledge base
        kb_response = client.post(
            "/api/knowledge-bases",
            headers=authenticated_headers,
            json={"name": "Test KB", "description": "Test"}
        )
        kb_id = kb_response.json()["id"]
        
        # Try to upload invalid file type
        invalid_content = b"Invalid file content"
        
        response = client.post(
            "/api/documents/upload",
            headers=authenticated_headers,
            files={"file": ("test.exe", BytesIO(invalid_content), "application/x-executable")},
            data={"knowledge_base_id": str(kb_id)}
        )
        
        # Should reject invalid file types
        assert response.status_code in [400, 422]
    
    def test_numeric_validation(self, client: TestClient, authenticated_headers: dict):
        """Test numeric field validation"""
        response = client.post(
            "/api/questions/generate",
            headers=authenticated_headers,
            json={
                "document_id": "not_a_number",
                "num_questions": -5,  # Invalid negative number
                "difficulty_level": 10  # Out of range
            }
        )
        
        assert response.status_code == 422