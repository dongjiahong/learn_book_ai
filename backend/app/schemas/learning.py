"""
Pydantic schemas for learning records and learning sets
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    """Content type for review records"""
    QUESTION = "question"
    KNOWLEDGE_POINT = "knowledge_point"


class MasteryLevel(int, Enum):
    """Mastery level for learning records"""
    NOT_LEARNED = 0  # 不会
    LEARNING = 1     # 学习中
    MASTERED = 2     # 已学会


class AnswerRecordBase(BaseModel):
    """Base schema for answer records"""
    user_answer: str = Field(..., description="User's answer to the question")
    reference_answer: Optional[str] = Field(None, description="Reference answer")
    score: Optional[float] = Field(None, ge=0, le=10, description="Score out of 10")
    feedback: Optional[str] = Field(None, description="Feedback on the answer")


class AnswerRecordCreate(AnswerRecordBase):
    """Schema for creating answer records"""
    question_id: int = Field(..., description="ID of the question being answered")


class AnswerRecordUpdate(BaseModel):
    """Schema for updating answer records"""
    user_answer: Optional[str] = Field(None, description="Updated user answer")
    reference_answer: Optional[str] = Field(None, description="Updated reference answer")
    score: Optional[float] = Field(None, ge=0, le=10, description="Updated score")
    feedback: Optional[str] = Field(None, description="Updated feedback")


class AnswerRecordResponse(AnswerRecordBase):
    """Schema for answer record responses"""
    id: int
    user_id: int
    question_id: int
    answered_at: datetime
    
    # Related data
    question_text: Optional[str] = None
    document_filename: Optional[str] = None
    knowledge_base_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReviewRecordBase(BaseModel):
    """Base schema for review records"""
    content_id: int = Field(..., description="ID of the content being reviewed")
    content_type: ContentType = Field(..., description="Type of content")
    review_count: int = Field(default=0, description="Number of times reviewed")
    ease_factor: float = Field(default=2.5, ge=1.3, le=3.0, description="Ease factor for spaced repetition")
    interval_days: int = Field(default=1, ge=1, description="Interval in days for next review")


class ReviewRecordCreate(ReviewRecordBase):
    """Schema for creating review records"""
    pass


class ReviewRecordUpdate(BaseModel):
    """Schema for updating review records"""
    review_count: Optional[int] = Field(None, description="Updated review count")
    ease_factor: Optional[float] = Field(None, ge=1.3, le=3.0, description="Updated ease factor")
    interval_days: Optional[int] = Field(None, ge=1, description="Updated interval in days")
    last_reviewed: Optional[datetime] = Field(None, description="Last review timestamp")
    next_review: Optional[datetime] = Field(None, description="Next review timestamp")


class ReviewRecordResponse(ReviewRecordBase):
    """Schema for review record responses"""
    id: int
    user_id: int
    last_reviewed: Optional[datetime]
    next_review: Optional[datetime]
    
    # Related data
    content_title: Optional[str] = None
    document_filename: Optional[str] = None
    knowledge_base_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class LearningRecordFilter(BaseModel):
    """Schema for filtering learning records"""
    knowledge_base_id: Optional[int] = Field(None, description="Filter by knowledge base")
    document_id: Optional[int] = Field(None, description="Filter by document")
    score_min: Optional[float] = Field(None, ge=0, le=10, description="Minimum score filter")
    score_max: Optional[float] = Field(None, ge=0, le=10, description="Maximum score filter")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    content_type: Optional[ContentType] = Field(None, description="Filter by content type")


class LearningStatistics(BaseModel):
    """Schema for learning statistics"""
    total_questions_answered: int = Field(default=0, description="Total questions answered")
    average_score: float = Field(default=0.0, description="Average score")
    total_study_time: int = Field(default=0, description="Total study time in minutes")
    questions_by_difficulty: Dict[int, int] = Field(default_factory=dict, description="Questions count by difficulty")
    scores_by_date: List[Dict[str, Any]] = Field(default_factory=list, description="Scores grouped by date")
    knowledge_base_progress: List[Dict[str, Any]] = Field(default_factory=list, description="Progress by knowledge base")
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Recent learning activity")


class LearningProgressResponse(BaseModel):
    """Schema for learning progress response"""
    user_id: int
    statistics: LearningStatistics
    due_reviews: List[ReviewRecordResponse] = Field(default_factory=list, description="Reviews due today")
    recent_records: List[AnswerRecordResponse] = Field(default_factory=list, description="Recent answer records")


class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete operations"""
    record_ids: List[int] = Field(..., description="List of record IDs to delete")


class LearningRecordSearchRequest(BaseModel):
    """Schema for searching learning records"""
    query: Optional[str] = Field(None, description="Search query")
    filters: Optional[LearningRecordFilter] = Field(None, description="Additional filters")
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of records to return")
    sort_by: Optional[str] = Field(default="answered_at", description="Field to sort by")
    sort_order: Optional[str] = Field(default="desc", description="Sort order")


# Learning Set Schemas
class LearningSetBase(BaseModel):
    """Base schema for learning sets"""
    name: str = Field(..., min_length=1, max_length=200, description="Name of the learning set")
    description: Optional[str] = Field(None, description="Description of the learning set")


class LearningSetCreate(LearningSetBase):
    """Schema for creating learning sets"""
    knowledge_base_id: int = Field(..., description="ID of the knowledge base")
    document_ids: List[int] = Field(..., description="List of document IDs to include in the learning set")


class LearningSetUpdate(BaseModel):
    """Schema for updating learning sets"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated name")
    description: Optional[str] = Field(None, description="Updated description")


class LearningSetItemResponse(BaseModel):
    """Schema for learning set item responses"""
    id: int
    knowledge_point_id: int
    added_at: datetime
    
    # Knowledge point details
    knowledge_point_title: str
    knowledge_point_content: str
    knowledge_point_question: Optional[str] = None
    knowledge_point_importance: int
    
    # Learning progress
    mastery_level: Optional[int] = None
    review_count: Optional[int] = None
    next_review: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LearningSetResponse(LearningSetBase):
    """Schema for learning set responses"""
    id: int
    user_id: int
    knowledge_base_id: int
    created_at: datetime
    updated_at: datetime
    
    # Statistics
    total_items: int = Field(default=0, description="Total number of knowledge points")
    mastered_items: int = Field(default=0, description="Number of mastered knowledge points")
    learning_items: int = Field(default=0, description="Number of knowledge points being learned")
    new_items: int = Field(default=0, description="Number of new knowledge points")
    
    # Related data
    knowledge_base_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class LearningSetDetailResponse(LearningSetResponse):
    """Schema for detailed learning set responses with items"""
    items: List[LearningSetItemResponse] = Field(default_factory=list, description="Learning set items")


# Learning Record Schemas (for the new learning system)
class NewLearningRecordBase(BaseModel):
    """Base schema for new learning records"""
    mastery_level: MasteryLevel = Field(default=MasteryLevel.NOT_LEARNED, description="Mastery level")
    review_count: int = Field(default=0, description="Number of reviews")
    ease_factor: float = Field(default=2.5, ge=1.3, le=3.0, description="Ease factor for spaced repetition")
    interval_days: int = Field(default=1, ge=1, description="Interval in days for next review")


class NewLearningRecordCreate(NewLearningRecordBase):
    """Schema for creating new learning records"""
    knowledge_point_id: int = Field(..., description="ID of the knowledge point")
    learning_set_id: int = Field(..., description="ID of the learning set")


class NewLearningRecordUpdate(BaseModel):
    """Schema for updating learning records"""
    mastery_level: Optional[MasteryLevel] = Field(None, description="Updated mastery level")
    review_count: Optional[int] = Field(None, description="Updated review count")
    ease_factor: Optional[float] = Field(None, ge=1.3, le=3.0, description="Updated ease factor")
    interval_days: Optional[int] = Field(None, ge=1, description="Updated interval in days")
    last_reviewed: Optional[datetime] = Field(None, description="Last review timestamp")
    next_review: Optional[datetime] = Field(None, description="Next review timestamp")


class NewLearningRecordResponse(NewLearningRecordBase):
    """Schema for learning record responses"""
    id: int
    user_id: int
    knowledge_point_id: int
    learning_set_id: int
    last_reviewed: Optional[datetime]
    next_review: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Related data
    knowledge_point_title: Optional[str] = None
    knowledge_point_question: Optional[str] = None
    knowledge_point_content: Optional[str] = None
    learning_set_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Learning Session Schemas
class LearningSessionStart(BaseModel):
    """Schema for starting a learning session"""
    learning_set_id: int = Field(..., description="ID of the learning set")
    review_type: Optional[str] = Field(default="all", description="Type of review: 'all', 'due', 'new'")


class LearningSessionAnswer(BaseModel):
    """Schema for answering in a learning session"""
    knowledge_point_id: int = Field(..., description="ID of the knowledge point")
    learning_set_id: int = Field(..., description="ID of the learning set")
    mastery_level: MasteryLevel = Field(..., description="User's mastery level for this knowledge point")


class LearningSessionResponse(BaseModel):
    """Schema for learning session responses"""
    learning_set_id: int
    learning_set_name: str
    current_item: Optional[LearningSetItemResponse] = None
    remaining_items: int = Field(default=0, description="Number of remaining items")
    session_progress: Dict[str, int] = Field(default_factory=dict, description="Session progress statistics")


# Statistics Schemas
class LearningSetStatistics(BaseModel):
    """Schema for learning set statistics"""
    learning_set_id: int
    total_items: int = Field(default=0, description="Total knowledge points")
    mastered_items: int = Field(default=0, description="Mastered knowledge points")
    learning_items: int = Field(default=0, description="Knowledge points being learned")
    new_items: int = Field(default=0, description="New knowledge points")
    due_items: int = Field(default=0, description="Knowledge points due for review")
    
    # Progress over time
    daily_progress: List[Dict[str, Any]] = Field(default_factory=list, description="Daily progress data")
    mastery_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution by mastery level")


class KnowledgeBaseStatistics(BaseModel):
    """Schema for knowledge base statistics"""
    knowledge_base_id: int
    total_documents: int = Field(default=0, description="Total number of documents")
    total_knowledge_points: int = Field(default=0, description="Total number of knowledge points")
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="Document statistics")
    learning_sets_count: int = Field(default=0, description="Number of learning sets created from this knowledge base")