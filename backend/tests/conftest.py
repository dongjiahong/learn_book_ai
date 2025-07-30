"""
Pytest configuration and shared fixtures for the RAG Learning Platform tests
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch

from app.models.database import Base, get_db
from app.models.models import User, KnowledgeBase, Document, Question, AnswerRecord, KnowledgePoint, ReviewRecord
from app.core.config import Config
from app.core.model_config import ModelConfig, ModelProvider, OpenAIConfig, OllamaConfig, EmbeddingConfig
from main import app

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_config() -> Config:
    """Create a test configuration."""
    # Create temporary config file
    config_content = """
[database]
url = "sqlite:///./test.db"
echo = false

[auth]
secret_key = "test-secret-key"
algorithm = "HS256"
access_token_expire_minutes = 30

[llm]
provider = "ollama"
fallback_provider = "openai"
temperature = 0.7
max_tokens = 1024
health_check_interval = 300

[openai]
api_key = "sk-test123"
model = "gpt-3.5-turbo"
timeout = 30

[ollama]
base_url = "http://localhost:11434"
model = "qwen3:4b"
timeout = 30

[embeddings]
provider = "huggingface"
model = "shaw/dmeta-embedding-zh-small-q4"
dimension = 384
batch_size = 32

[vector_store]
provider = "chroma"
persist_directory = "./test_chroma_db"
collection_name = "test_collection"

[anki]
deck_name = "Test Deck"
model_name = "Basic"

[server]
host = "0.0.0.0"
port = 8000
debug = true
reload = false

[cors]
allow_origins = ["http://localhost:3000"]
allow_credentials = true
allow_methods = ["*"]
allow_headers = ["*"]
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(config_content)
        config_path = f.name
    
    try:
        config = Config(config_path)
        yield config
    finally:
        os.unlink(config_path)


@pytest.fixture
def test_model_config() -> ModelConfig:
    """Create a test model configuration."""
    return ModelConfig(
        provider=ModelProvider.OLLAMA,
        openai=OpenAIConfig(api_key="sk-test123"),
        ollama=OllamaConfig(base_url="http://localhost:11434", model="qwen3:4b"),
        embedding=EmbeddingConfig(),
        fallback_provider=ModelProvider.OPENAI,
        health_check_interval=300
    )


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "secret"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_knowledge_base(db_session: Session, test_user: User) -> KnowledgeBase:
    """Create a test knowledge base."""
    kb = KnowledgeBase(
        user_id=test_user.id,
        name="Test Knowledge Base",
        description="A test knowledge base for testing purposes"
    )
    db_session.add(kb)
    db_session.commit()
    db_session.refresh(kb)
    return kb


@pytest.fixture
def test_document(db_session: Session, test_knowledge_base: KnowledgeBase) -> Document:
    """Create a test document."""
    doc = Document(
        knowledge_base_id=test_knowledge_base.id,
        filename="test_document.pdf",
        file_path="/test/path/test_document.pdf",
        file_type="pdf",
        file_size=1024,
        processed=True
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture
def test_question(db_session: Session, test_document: Document) -> Question:
    """Create a test question."""
    question = Question(
        document_id=test_document.id,
        question_text="What is the main topic of this document?",
        context="This document discusses various aspects of machine learning.",
        difficulty_level=2
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


@pytest.fixture
def test_answer_record(db_session: Session, test_user: User, test_question: Question) -> AnswerRecord:
    """Create a test answer record."""
    record = AnswerRecord(
        user_id=test_user.id,
        question_id=test_question.id,
        user_answer="The main topic is machine learning algorithms.",
        reference_answer="The document covers machine learning concepts and applications.",
        score=8.5,
        feedback="Good understanding of the main concepts."
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


@pytest.fixture
def test_knowledge_point(db_session: Session, test_document: Document) -> KnowledgePoint:
    """Create a test knowledge point."""
    kp = KnowledgePoint(
        document_id=test_document.id,
        title="Machine Learning Basics",
        content="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
        importance_level=3
    )
    db_session.add(kp)
    db_session.commit()
    db_session.refresh(kp)
    return kp


@pytest.fixture
def test_review_record(db_session: Session, test_user: User, test_question: Question) -> ReviewRecord:
    """Create a test review record."""
    from datetime import datetime, timedelta
    
    record = ReviewRecord(
        user_id=test_user.id,
        content_id=test_question.id,
        content_type="question",
        review_count=1,
        last_reviewed=datetime.now(),
        next_review=datetime.now() + timedelta(days=1),
        ease_factor=2.5,
        interval_days=1
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


@pytest.fixture
def mock_model_service():
    """Create a mock model service."""
    mock_service = Mock()
    mock_service.generate_text = AsyncMock(return_value="Generated text response")
    mock_service.generate_questions = AsyncMock(return_value=[
        {
            "question": "What is machine learning?",
            "context": "Machine learning context",
            "difficulty": 2
        }
    ])
    mock_service.evaluate_answer = AsyncMock(return_value={
        "score": 8.5,
        "feedback": "Good answer",
        "reference_answer": "Reference answer"
    })
    mock_service.extract_knowledge_points = AsyncMock(return_value=[
        {
            "title": "Knowledge Point",
            "content": "Knowledge point content",
            "importance": 3
        }
    ])
    return mock_service


@pytest.fixture
def mock_rag_service():
    """Create a mock RAG service."""
    mock_service = Mock()
    mock_service.add_document = AsyncMock(return_value=True)
    mock_service.query = AsyncMock(return_value={
        "response": "RAG response",
        "source_nodes": []
    })
    mock_service.get_relevant_context = AsyncMock(return_value="Relevant context")
    return mock_service


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    mock_store = Mock()
    mock_store.add = Mock()
    mock_store.query = Mock(return_value={
        "ids": [["doc1", "doc2"]],
        "distances": [[0.1, 0.2]],
        "documents": [["Document 1", "Document 2"]],
        "metadatas": [[{"source": "doc1"}, {"source": "doc2"}]]
    })
    mock_store.delete = Mock()
    return mock_store


@pytest.fixture
def authenticated_headers(client: TestClient) -> dict:
    """Get authentication headers for API requests."""
    # Register and login a user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def temp_file():
    """Create a temporary file for testing file uploads."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document content for testing purposes.")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_file_upload():
    """Create a mock file upload for testing."""
    from io import BytesIO
    
    file_content = b"This is test file content for document processing."
    file_obj = BytesIO(file_content)
    file_obj.name = "test_document.txt"
    
    return {
        "file": ("test_document.txt", file_obj, "text/plain")
    }


# Async fixtures for async tests
@pytest.fixture
async def async_db_session() -> AsyncGenerator[Session, None]:
    """Create an async database session for async tests."""
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# Mock external services
@pytest.fixture(autouse=True)
def mock_external_services():
    """Automatically mock external services for all tests."""
    with patch('app.services.model_service.ModelService') as mock_model, \
         patch('app.services.rag_service.RAGService') as mock_rag, \
         patch('chromadb.Client') as mock_chroma:
        
        # Configure mocks with default behaviors
        mock_model.return_value.generate_text = AsyncMock(return_value="Mock response")
        mock_rag.return_value.add_document = AsyncMock(return_value=True)
        mock_chroma.return_value.get_or_create_collection = Mock()
        
        yield {
            'model_service': mock_model,
            'rag_service': mock_rag,
            'chroma_client': mock_chroma
        }


# Performance testing fixtures
@pytest.fixture
def performance_test_data(db_session: Session, test_user: User):
    """Create test data for performance testing."""
    # Create multiple knowledge bases
    knowledge_bases = []
    for i in range(5):
        kb = KnowledgeBase(
            user_id=test_user.id,
            name=f"Knowledge Base {i+1}",
            description=f"Test knowledge base {i+1}"
        )
        db_session.add(kb)
        knowledge_bases.append(kb)
    
    db_session.commit()
    
    # Create multiple documents
    documents = []
    for kb in knowledge_bases:
        for j in range(10):
            doc = Document(
                knowledge_base_id=kb.id,
                filename=f"document_{j+1}.pdf",
                file_path=f"/test/path/document_{j+1}.pdf",
                file_type="pdf",
                file_size=1024 * (j + 1),
                processed=True
            )
            db_session.add(doc)
            documents.append(doc)
    
    db_session.commit()
    
    # Create multiple questions
    questions = []
    for doc in documents:
        for k in range(5):
            question = Question(
                document_id=doc.id,
                question_text=f"Test question {k+1} for {doc.filename}?",
                context=f"Context for question {k+1}",
                difficulty_level=(k % 3) + 1
            )
            db_session.add(question)
            questions.append(question)
    
    db_session.commit()
    
    return {
        'knowledge_bases': knowledge_bases,
        'documents': documents,
        'questions': questions
    }