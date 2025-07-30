"""
Spaced Repetition Service implementing Anki's SM-2 algorithm
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.models import ReviewRecord, Question, KnowledgePoint, User
from ..models.database import get_db


class SpacedRepetitionService:
    """Service for managing spaced repetition learning using Anki's SM-2 algorithm"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_next_review(self, ease_factor: float, interval_days: int, quality: int) -> tuple[float, int]:
        """
        Calculate next review interval using SM-2 algorithm
        
        Args:
            ease_factor: Current ease factor (default 2.5)
            interval_days: Current interval in days
            quality: Quality of recall (0-5, where 3+ is passing)
            
        Returns:
            tuple: (new_ease_factor, new_interval_days)
        """
        # SM-2 Algorithm implementation
        if quality < 3:
            # Failed recall - reset interval to 1 day
            new_interval = 1
            new_ease_factor = ease_factor
        else:
            # Successful recall
            if interval_days == 1:
                new_interval = 6
            elif interval_days == 6:
                new_interval = 16
            else:
                new_interval = int(interval_days * ease_factor)
            
            # Update ease factor based on quality
            new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            
            # Ensure ease factor doesn't go below 1.3
            new_ease_factor = max(1.3, new_ease_factor)
        
        return new_ease_factor, new_interval
    
    def get_or_create_review_record(self, user_id: int, content_id: int, content_type: str) -> ReviewRecord:
        """Get existing review record or create a new one"""
        review_record = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.content_id == content_id,
                ReviewRecord.content_type == content_type
            )
        ).first()
        
        if not review_record:
            # Create new review record
            review_record = ReviewRecord(
                user_id=user_id,
                content_id=content_id,
                content_type=content_type,
                review_count=0,
                ease_factor=2.5,
                interval_days=1,
                next_review=datetime.utcnow()
            )
            self.db.add(review_record)
            self.db.commit()
            self.db.refresh(review_record)
        
        return review_record
    
    def update_review_record(self, user_id: int, content_id: int, content_type: str, quality: int) -> ReviewRecord:
        """Update review record after a review session"""
        review_record = self.get_or_create_review_record(user_id, content_id, content_type)
        
        # Calculate new parameters
        new_ease_factor, new_interval = self.calculate_next_review(
            review_record.ease_factor,
            review_record.interval_days,
            quality
        )
        
        # Update record
        review_record.review_count += 1
        review_record.last_reviewed = datetime.utcnow()
        review_record.next_review = datetime.utcnow() + timedelta(days=new_interval)
        review_record.ease_factor = new_ease_factor
        review_record.interval_days = new_interval
        
        self.db.commit()
        self.db.refresh(review_record)
        
        return review_record
    
    def get_due_reviews(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get items due for review"""
        now = datetime.utcnow()
        
        # Get due review records
        due_records = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.next_review <= now
            )
        ).order_by(ReviewRecord.next_review).limit(limit).all()
        
        result = []
        for record in due_records:
            item_data = {
                'review_record_id': record.id,
                'content_id': record.content_id,
                'content_type': record.content_type,
                'review_count': record.review_count,
                'last_reviewed': record.last_reviewed,
                'next_review': record.next_review,
                'ease_factor': record.ease_factor,
                'interval_days': record.interval_days
            }
            
            # Get the actual content
            if record.content_type == 'question':
                question = self.db.query(Question).filter(Question.id == record.content_id).first()
                if question:
                    item_data.update({
                        'question_text': question.question_text,
                        'context': question.context,
                        'difficulty_level': question.difficulty_level,
                        'document_id': question.document_id
                    })
            elif record.content_type == 'knowledge_point':
                knowledge_point = self.db.query(KnowledgePoint).filter(
                    KnowledgePoint.id == record.content_id
                ).first()
                if knowledge_point:
                    item_data.update({
                        'title': knowledge_point.title,
                        'content': knowledge_point.content,
                        'importance_level': knowledge_point.importance_level,
                        'document_id': knowledge_point.document_id
                    })
            
            result.append(item_data)
        
        return result
    
    def get_review_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get review statistics for a user"""
        now = datetime.utcnow()
        
        # Total review records
        total_records = self.db.query(ReviewRecord).filter(ReviewRecord.user_id == user_id).count()
        
        # Due today
        due_today = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.next_review <= now
            )
        ).count()
        
        # Due this week
        week_from_now = now + timedelta(days=7)
        due_this_week = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.next_review <= week_from_now,
                ReviewRecord.next_review > now
            )
        ).count()
        
        # Reviews completed today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        completed_today = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.last_reviewed >= today_start
            )
        ).count()
        
        # Average ease factor
        avg_ease_factor = self.db.query(ReviewRecord).filter(
            ReviewRecord.user_id == user_id
        ).with_entities(ReviewRecord.ease_factor).all()
        
        avg_ease = sum(record.ease_factor for record in avg_ease_factor) / len(avg_ease_factor) if avg_ease_factor else 2.5
        
        return {
            'total_items': total_records,
            'due_today': due_today,
            'due_this_week': due_this_week,
            'completed_today': completed_today,
            'average_ease_factor': round(avg_ease, 2)
        }
    
    def get_learning_streak(self, user_id: int) -> int:
        """Calculate current learning streak (consecutive days with reviews)"""
        now = datetime.utcnow()
        current_date = now.date()
        streak = 0
        
        # Check each day backwards
        for i in range(365):  # Check up to a year back
            check_date = current_date - timedelta(days=i)
            day_start = datetime.combine(check_date, datetime.min.time())
            day_end = datetime.combine(check_date, datetime.max.time())
            
            reviews_on_day = self.db.query(ReviewRecord).filter(
                and_(
                    ReviewRecord.user_id == user_id,
                    ReviewRecord.last_reviewed >= day_start,
                    ReviewRecord.last_reviewed <= day_end
                )
            ).count()
            
            if reviews_on_day > 0:
                streak += 1
            else:
                break
        
        return streak
    
    def schedule_new_item(self, user_id: int, content_id: int, content_type: str) -> ReviewRecord:
        """Schedule a new item for spaced repetition"""
        return self.get_or_create_review_record(user_id, content_id, content_type)
    
    def get_upcoming_reviews(self, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming reviews for the next N days"""
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)
        
        upcoming_records = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.next_review > now,
                ReviewRecord.next_review <= end_date
            )
        ).order_by(ReviewRecord.next_review).all()
        
        # Group by date
        reviews_by_date = {}
        for record in upcoming_records:
            date_key = record.next_review.date().isoformat()
            if date_key not in reviews_by_date:
                reviews_by_date[date_key] = []
            
            reviews_by_date[date_key].append({
                'content_id': record.content_id,
                'content_type': record.content_type,
                'review_count': record.review_count,
                'ease_factor': record.ease_factor,
                'interval_days': record.interval_days
            })
        
        return reviews_by_date