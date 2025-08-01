"""
SQLAlchemy models for the RAG Learning Platform
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from .database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    knowledge_bases = relationship("KnowledgeBase", back_populates="user", cascade="all, delete-orphan")
    answer_records = relationship("AnswerRecord", back_populates="user", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="user", cascade="all, delete-orphan")
    learning_sets = relationship("LearningSet", back_populates="user", cascade="all, delete-orphan")
    learning_records = relationship("LearningRecord", back_populates="user", cascade="all, delete-orphan")


class KnowledgeBase(Base):
    """Knowledge base model"""
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    learning_sets = relationship("LearningSet", back_populates="knowledge_base", cascade="all, delete-orphan")


class Document(Base):
    """Document model"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    questions = relationship("Question", back_populates="document", cascade="all, delete-orphan")
    knowledge_points = relationship("KnowledgePoint", back_populates="document", cascade="all, delete-orphan")


class Question(Base):
    """Question model"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    context = Column(Text)
    difficulty_level = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="questions")
    answer_records = relationship("AnswerRecord", back_populates="question", cascade="all, delete-orphan")


class AnswerRecord(Base):
    """Answer record model"""
    __tablename__ = "answer_records"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    reference_answer = Column(Text)
    score = Column(Float)
    feedback = Column(Text)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="answer_records")
    question = relationship("Question", back_populates="answer_records")


class KnowledgePoint(Base):
    """Knowledge point model"""
    __tablename__ = "knowledge_points"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    title = Column(String(200), nullable=False)
    question = Column(Text)  # 新增：基于知识点内容生成的问题
    content = Column(Text, nullable=False)
    importance_level = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="knowledge_points")
    learning_set_items = relationship("LearningSetItem", back_populates="knowledge_point", cascade="all, delete-orphan")
    learning_records = relationship("LearningRecord", back_populates="knowledge_point", cascade="all, delete-orphan")


class ReviewRecord(Base):
    """Review record model for spaced repetition"""
    __tablename__ = "review_records"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, nullable=False)  # ID of question or knowledge_point
    content_type = Column(String(20), nullable=False)  # 'question' or 'knowledge_point'
    review_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime(timezone=True))
    next_review = Column(DateTime(timezone=True))
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User", back_populates="review_records")


class LearningSet(Base):
    """Learning set model for organizing knowledge points into study sets"""
    __tablename__ = "learning_sets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="learning_sets")
    knowledge_base = relationship("KnowledgeBase", back_populates="learning_sets")
    learning_items = relationship("LearningSetItem", back_populates="learning_set", cascade="all, delete-orphan")
    learning_records = relationship("LearningRecord", back_populates="learning_set", cascade="all, delete-orphan")


class LearningSetItem(Base):
    """Learning set item model for individual knowledge points in a learning set"""
    __tablename__ = "learning_set_items"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    learning_set_id = Column(Integer, ForeignKey("learning_sets.id"), nullable=False)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    learning_set = relationship("LearningSet", back_populates="learning_items")
    knowledge_point = relationship("KnowledgePoint", back_populates="learning_set_items")


class LearningRecord(Base):
    """Learning record model for tracking user progress with knowledge points"""
    __tablename__ = "learning_records"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False)
    learning_set_id = Column(Integer, ForeignKey("learning_sets.id"), nullable=False)
    
    # 记忆曲线相关字段
    mastery_level = Column(Integer, default=0)  # 0: 不会, 1: 学习中, 2: 已学会
    review_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime(timezone=True))
    next_review = Column(DateTime(timezone=True))
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="learning_records")
    knowledge_point = relationship("KnowledgePoint", back_populates="learning_records")
    learning_set = relationship("LearningSet", back_populates="learning_records")