"""
Authentication middleware for protecting API endpoints
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from .auth import auth_manager
from ..models.database import get_db
from ..models.models import User

# HTTP Bearer token scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify token and get user ID
        user_id = auth_manager.get_user_id_from_token(token)
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
            
        return user
        
    except Exception:
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get current active user (can be extended for user status checks)
    """
    # For now, all users are considered active
    # This can be extended to check user.is_active field if needed
    return current_user

# Optional authentication dependency (for endpoints that work with or without auth)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional dependency to get current user (returns None if not authenticated)
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        user_id = auth_manager.get_user_id_from_token(token)
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None