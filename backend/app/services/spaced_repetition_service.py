"""
Spaced Repetition Service implementing SuperMemo SM-2 algorithm
"""
from datetime import datetime, timedelta
from typing import Tuple
import math


class SpacedRepetitionService:
    """Service for calculating spaced repetition intervals using SuperMemo SM-2 algorithm"""
    
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


# Service instance
spaced_repetition_service = SpacedRepetitionService()