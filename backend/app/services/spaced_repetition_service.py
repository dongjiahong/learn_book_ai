"""
Spaced Repetition Service implementing SuperMemo SM-2 algorithm
"""
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any, Optional
from sqlalchemy.orm import Session
import math

from ..models.models import ReviewRecord
from ..models.crud import CRUDReviewRecord


class SpacedRepetitionService:
    """Service for calculating spaced repetition intervals using SuperMemo SM-2 algorithm"""
    
    def __init__(self, db: Session):
        self.db = db
        self.crud = CRUDReviewRecord(ReviewRecord)
    
    # Quality ratings mapping
    QUALITY_RATINGS = {
        0: 0,  # 不会 - Complete blackout
        1: 3,  # 学习中 - Correct response recalled with serious difficulty  
        2: 5   # 已学会 - Perfect response
    }
    
    @staticmethod
    def calculate_next_review(
        mastery_level: int,
        current_ease_factor: float = 2.5,
        current_interval: int = 1,
        review_count: int = 0
    ) -> Tuple[int, float, datetime]:
        """
        Calculate next review interval using SuperMemo SM-2 algorithm
        
        Args:
            mastery_level: User's mastery level (0: 不会, 1: 学习中, 2: 已学会)
            current_ease_factor: Current ease factor (1.3 - 3.0)
            current_interval: Current interval in days
            review_count: Number of times reviewed
            
        Returns:
            Tuple of (new_interval_days, new_ease_factor, next_review_datetime)
        """
        # Map mastery level to quality rating
        quality = SpacedRepetitionService.QUALITY_RATINGS.get(mastery_level, 0)
        
        # Calculate new ease factor
        new_ease_factor = current_ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ease_factor = max(1.3, new_ease_factor)  # Minimum ease factor is 1.3
        
        # Calculate new interval
        if quality < 3:  # If quality is less than 3 (not well remembered)
            new_interval = 1  # Start over
        else:
            if review_count == 0:
                new_interval = 1
            elif review_count == 1:
                new_interval = 6
            else:
                new_interval = math.ceil(current_interval * new_ease_factor)
        
        # Calculate next review date
        next_review = datetime.now() + timedelta(days=new_interval)
        
        return new_interval, new_ease_factor, next_review
    
    @staticmethod
    def get_initial_values() -> Tuple[int, float, datetime]:
        """
        Get initial values for a new learning record
        
        Returns:
            Tuple of (initial_interval, initial_ease_factor, initial_next_review)
        """
        return 1, 2.5, datetime.now() + timedelta(days=1)
    
    @staticmethod
    def is_due_for_review(next_review: datetime) -> bool:
        """
        Check if a knowledge point is due for review
        
        Args:
            next_review: Next scheduled review datetime
            
        Returns:
            True if due for review, False otherwise
        """
        return datetime.now() >= next_review
    
    @staticmethod
    def calculate_retention_rate(
        mastery_level: int,
        days_since_last_review: int,
        ease_factor: float
    ) -> float:
        """
        Estimate retention rate based on forgetting curve
        
        Args:
            mastery_level: Current mastery level
            days_since_last_review: Days since last review
            ease_factor: Current ease factor
            
        Returns:
            Estimated retention rate (0.0 - 1.0)
        """
        if mastery_level == 0:  # Not learned
            return 0.0
        elif mastery_level == 2:  # Mastered
            base_retention = 0.9
        else:  # Learning
            base_retention = 0.7
        
        # Apply forgetting curve: R(t) = R0 * e^(-t/S)
        # Where S is stability factor related to ease_factor
        stability = ease_factor * 2  # Simple mapping
        retention = base_retention * math.exp(-days_since_last_review / stability)
        
        return max(0.0, min(1.0, retention))
    
    @staticmethod
    def get_study_priority(
        mastery_level: int,
        next_review: datetime,
        importance_level: int = 1
    ) -> float:
        """
        Calculate study priority for a knowledge point
        
        Args:
            mastery_level: Current mastery level
            next_review: Next scheduled review datetime
            importance_level: Importance level of the knowledge point (1-5)
            
        Returns:
            Priority score (higher = more urgent)
        """
        now = datetime.now()
        
        # Base priority based on mastery level
        if mastery_level == 0:  # Not learned
            base_priority = 10.0
        elif mastery_level == 1:  # Learning
            base_priority = 5.0
        else:  # Mastered
            base_priority = 1.0
        
        # Adjust for overdue items
        if next_review is None or next_review <= now:
            if next_review is None:
                days_overdue = 0  # New item, not overdue
            else:
                days_overdue = (now - next_review).days
            overdue_multiplier = 1.0 + (days_overdue * 0.1)  # 10% increase per day overdue
        else:
            overdue_multiplier = 1.0
        
        # Adjust for importance
        importance_multiplier = importance_level / 3.0  # Normalize to ~1.0
        
        return base_priority * overdue_multiplier * importance_multiplier
    
    @staticmethod
    def get_recommended_study_time(mastery_level: int, importance_level: int = 1) -> int:
        """
        Get recommended study time in minutes
        
        Args:
            mastery_level: Current mastery level
            importance_level: Importance level (1-5)
            
        Returns:
            Recommended study time in minutes
        """
        base_times = {
            0: 5,   # Not learned - 5 minutes
            1: 3,   # Learning - 3 minutes  
            2: 1    # Mastered - 1 minute
        }
        
        base_time = base_times.get(mastery_level, 3)
        importance_factor = 1.0 + (importance_level - 1) * 0.2  # 20% increase per importance level
        
        return max(1, int(base_time * importance_factor))

    def get_due_reviews(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get items due for review"""
        try:
            due_records = self.crud.get_due_reviews(self.db, user_id, limit)
            
            result = []
            for record in due_records:
                result.append({
                    'id': record.id,
                    'content_id': record.content_id,
                    'content_type': record.content_type,
                    'review_count': record.review_count,
                    'last_reviewed': record.last_reviewed.isoformat() if record.last_reviewed else None,
                    'next_review': record.next_review.isoformat() if record.next_review else None,
                    'ease_factor': record.ease_factor,
                    'interval_days': record.interval_days
                })
            
            return result
        except Exception as e:
            raise Exception(f"Failed to get due reviews: {str(e)}")

    def update_review_record(
        self, 
        user_id: int, 
        content_id: int, 
        content_type: str, 
        quality: int
    ) -> ReviewRecord:
        """Update review record based on quality rating"""
        try:
            # Get existing record or create new one
            record = self.crud.get_by_content(self.db, user_id, content_id, content_type)
            
            if not record:
                # Create new record
                record = ReviewRecord(
                    user_id=user_id,
                    content_id=content_id,
                    content_type=content_type,
                    review_count=0,
                    ease_factor=2.5,
                    interval_days=1,
                    next_review=datetime.now()
                )
                self.db.add(record)
                self.db.commit()
                self.db.refresh(record)
            
            # Update using CRUD method
            updated_record = self.crud.update_review_schedule(self.db, record, quality)
            return updated_record
            
        except Exception as e:
            raise Exception(f"Failed to update review record: {str(e)}")

    def get_review_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get review statistics for a user"""
        try:
            from datetime import date
            
            # Get all user's review records
            all_records = self.crud.get_by_user(self.db, user_id, limit=1000)
            
            today = datetime.now().date()
            
            # Calculate statistics
            total_reviews = len(all_records)
            due_today = len([r for r in all_records if r.next_review and r.next_review.date() <= today])
            completed_today = len([r for r in all_records if r.last_reviewed and r.last_reviewed.date() == today])
            
            # Calculate average ease factor
            avg_ease_factor = sum(r.ease_factor for r in all_records) / len(all_records) if all_records else 2.5
            
            return {
                'total_reviews': total_reviews,
                'due_today': due_today,
                'completed_today': completed_today,
                'average_ease_factor': round(avg_ease_factor, 2),
                'learning_streak': self.get_learning_streak(user_id)
            }
            
        except Exception as e:
            raise Exception(f"Failed to get review statistics: {str(e)}")

    def get_learning_streak(self, user_id: int) -> int:
        """Calculate learning streak (consecutive days with reviews)"""
        try:
            from datetime import date, timedelta
            
            # Get recent review records
            records = self.crud.get_by_user(self.db, user_id, limit=1000)
            
            if not records:
                return 0
            
            # Group by date
            review_dates = set()
            for record in records:
                if record.last_reviewed:
                    review_dates.add(record.last_reviewed.date())
            
            if not review_dates:
                return 0
            
            # Calculate streak
            streak = 0
            current_date = date.today()
            
            while current_date in review_dates:
                streak += 1
                current_date -= timedelta(days=1)
            
            return streak
            
        except Exception as e:
            return 0

    def get_upcoming_reviews(self, user_id: int, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """Get upcoming reviews for the next N days"""
        try:
            from datetime import date, timedelta
            
            all_records = self.crud.get_by_user(self.db, user_id, limit=1000)
            
            result = {}
            today = date.today()
            
            for i in range(days):
                target_date = today + timedelta(days=i)
                date_str = target_date.isoformat()
                
                reviews_for_date = []
                for record in all_records:
                    if record.next_review and record.next_review.date() == target_date:
                        reviews_for_date.append({
                            'id': record.id,
                            'content_id': record.content_id,
                            'content_type': record.content_type,
                            'review_count': record.review_count,
                            'ease_factor': record.ease_factor,
                            'interval_days': record.interval_days
                        })
                
                result[date_str] = reviews_for_date
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to get upcoming reviews: {str(e)}")

    def schedule_new_item(self, user_id: int, content_id: int, content_type: str) -> ReviewRecord:
        """Schedule a new item for spaced repetition"""
        try:
            # Check if already exists
            existing = self.crud.get_by_content(self.db, user_id, content_id, content_type)
            if existing:
                return existing
            
            # Create new record
            record = ReviewRecord(
                user_id=user_id,
                content_id=content_id,
                content_type=content_type,
                review_count=0,
                ease_factor=2.5,
                interval_days=1,
                next_review=datetime.now() + timedelta(days=1)
            )
            
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            
            return record
            
        except Exception as e:
            raise Exception(f"Failed to schedule new item: {str(e)}")


# Note: Service instance creation moved to where it's needed since it requires db parameter