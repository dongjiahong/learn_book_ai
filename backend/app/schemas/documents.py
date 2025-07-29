"""
Pydantic schemas for document management
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """Supported file types"""
    PDF = "pdf"
    EPUB = "epub"
    TXT = "txt"
    MD = "md"


class DocumentBase(BaseModel):
    """Base document schema"""
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: FileType
    file_size: int = Field(..., gt=0)


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    knowledge_base_id: int = Field(..., gt=0)


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    filename: Optional[str] = Field(None, min_length=1, max_length=255)


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: int
    knowledge_base_id: int
    file_path: str
    processed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response"""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    success: bool
    message: str
    document: Optional[DocumentResponse] = None


class DocumentProcessingStatus(BaseModel):
    """Schema for document processing status"""
    document_id: int
    processed: bool
    processing_progress: Optional[float] = None
    error_message: Optional[str] = None


class KnowledgeBaseBase(BaseModel):
    """Base knowledge base schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """Schema for creating a knowledge base"""
    pass


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating a knowledge base"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    """Schema for knowledge base response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class KnowledgeBaseDetailResponse(KnowledgeBaseResponse):
    """Schema for detailed knowledge base response"""
    documents: List[DocumentResponse] = []


class KnowledgeBaseListResponse(BaseModel):
    """Schema for knowledge base list response"""
    knowledge_bases: List[KnowledgeBaseResponse]
    total: int
    page: int
    page_size: int