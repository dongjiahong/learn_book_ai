"""
Models package for the RAG Learning Platform
"""
from .database import Base, get_db, create_tables, drop_tables, SessionLocal, engine
from .models import (
    User,
    KnowledgeBase,
    Document,
    Question,
    AnswerRecord,
    KnowledgePoint,
    ReviewRecord
)
from .crud import CRUDBase
from .init_db import init_database, create_sample_data, verify_database

__all__ = [
    "Base",
    "get_db",
    "create_tables",
    "drop_tables",
    "SessionLocal",
    "engine",
    "User",
    "KnowledgeBase",
    "Document",
    "Question",
    "AnswerRecord",
    "KnowledgePoint",
    "ReviewRecord",
    "CRUDBase",
    "init_database",
    "create_sample_data",
    "verify_database"
]