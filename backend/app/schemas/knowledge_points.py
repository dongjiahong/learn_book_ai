"""
Pydantic schemas for knowledge point management
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class KnowledgePointSearchRequest(BaseModel):
    """Schema for knowledge point search request"""
    query: Optional[str] = Field(None, min_length=1, description="Search query string")
    knowledge_base_id: Optional[int] = Field(None, gt=0, description="Filter by knowledge base ID")
    document_id: Optional[int] = Field(None, gt=0, description="Filter by document ID")
    n_results: int = Field(10, ge=1, le=50, description="Number of results to return")


class KnowledgePointResponse(BaseModel):
    """Schema for knowledge point response"""
    id: int
    title: str
    content: str
    importance_level: int
    document_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgePointListResponse(BaseModel):
    """Schema for knowledge point list response"""
    knowledge_points: List[KnowledgePointResponse]
    total: int
    page: int
    page_size: int


class KnowledgePointCreate(BaseModel):
    """Schema for creating a knowledge point"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    importance_level: int = Field(..., ge=1, le=5)
    document_id: int = Field(..., gt=0)


class KnowledgePointUpdate(BaseModel):
    """Schema for updating a knowledge point"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    importance_level: Optional[int] = Field(None, ge=1, le=5)


class KnowledgePointSearchResult(BaseModel):
    """Schema for knowledge point search result"""
    content: str
    metadata: dict
    id: str


class BatchDeleteRequest(BaseModel):
    """Schema for batch delete request"""
    kp_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of knowledge point IDs to delete")