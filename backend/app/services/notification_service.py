"""
Notification service for review reminders and learning notifications
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.models import ReviewRecord, User, Question, KnowledgePoint
from ..models.database import get_db


class NotificationService:
    """Service for managing learning notifications and reminders"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_due_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all due review reminders for a user"""
        now = datetime.utcnow()
        
        # Get overdue items
        overdue_records = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.next_review < now - timedelta(hours=1)  # 1 hour grace period
            )
        ).all()
        
        # Get items due soon (within next 2 hours)
        due_soon_records = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.next_review <= now + timedelta(hours=2),
                ReviewRecord.next_review >= now - timedelta(hours=1)
            )
        ).all()
        
        reminders = []
        
        # Process overdue items
        for record in overdue_records:
            hours_overdue = (now - record.next_review).total_seconds() / 3600
            reminder = {
                'type': 'overdue',
                'content_id': record.content_id,
                'content_type': record.content_type,
                'hours_overdue': int(hours_overdue),
                'priority': 'high',
                'message': f"Review overdue by {int(hours_overdue)} hours"
            }
            
            # Add content details
            if record.content_type == 'question':
                question = self.db.query(Question).filter(Question.id == record.content_id).first()
                if question:
                    reminder['title'] = question.question_text[:100] + "..."
            elif record.content_type == 'knowledge_point':
                kp = self.db.query(KnowledgePoint).filter(KnowledgePoint.id == record.content_id).first()
                if kp:
                    reminder['title'] = kp.title
            
            reminders.append(reminder)
        
        # Process due soon items
        for record in due_soon_records:
            hours_until_due = (record.next_review - now).total_seconds() / 3600
            reminder = {
                'type': 'due_soon',
                'content_id': record.content_id,
                'content_type': record.content_type,
                'hours_until_due': max(0, hours_until_due),
                'priority': 'medium',
                'message': f"Review due in {max(0, int(hours_until_due))} hours"
            }
            
            # Add content details
            if record.content_type == 'question':
                question = self.db.query(Question).filter(Question.id == record.content_id).first()
                if question:
                    reminder['title'] = question.question_text[:100] + "..."
            elif record.content_type == 'knowledge_point':
                kp = self.db.query(KnowledgePoint).filter(KnowledgePoint.id == record.content_id).first()
                if kp:
                    reminder['title'] = kp.title
            
            reminders.append(reminder)
        
        return reminders
    
    def get_daily_summary(self, user_id: int) -> Dict[str, Any]:
        """Get daily learning summary for a user"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Reviews completed today
        completed_today = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.last_reviewed >= today_start
            )
        ).count()
        
        # Reviews due today
        due_today = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.next_review <= now
            )
        ).count()
        
        # Reviews scheduled for tomorrow
        tomorrow_start = now + timedelta(days=1)
        tomorrow_start = tomorrow_start.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        
        due_tomorrow = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.next_review >= tomorrow_start,
                ReviewRecord.next_review < tomorrow_end
            )
        ).count()
        
        return {
            'date': now.date().isoformat(),
            'completed_today': completed_today,
            'due_today': due_today,
            'due_tomorrow': due_tomorrow,
            'completion_rate': (completed_today / max(1, completed_today + due_today)) * 100
        }
    
    def get_weekly_summary(self, user_id: int) -> Dict[str, Any]:
        """Get weekly learning summary for a user"""
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Reviews completed this week
        completed_this_week = self.db.query(ReviewRecord).filter(
            and_(
                ReviewRecord.user_id == user_id,
                ReviewRecord.last_reviewed >= week_start
            )
        ).count()
        
        # Daily breakdown
        daily_counts = []
        for i in range(7):
            day_start = week_start + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_count = self.db.query(ReviewRecord).filter(
                and_(
                    ReviewRecord.user_id == user_id,
                    ReviewRecord.last_reviewed >= day_start,
                    ReviewRecord.last_reviewed < day_end
                )
            ).count()
            
            daily_counts.append({
                'date': day_start.date().isoformat(),
                'count': day_count
            })
        
        return {
            'week_start': week_start.date().isoformat(),
            'total_completed': completed_this_week,
            'daily_breakdown': daily_counts,
            'average_per_day': completed_this_week / 7
        }
    
    def create_achievement_notification(self, user_id: int, achievement_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Create achievement notification"""
        achievements = {
            'first_review': {
                'title': '🎉 First Review Complete!',
                'message': 'You completed your first spaced repetition review!',
                'icon': '🎯'
            },
            'streak_milestone': {
                'title': f'🔥 {details.get("streak", 0)} Day Streak!',
                'message': f'Amazing! You\'ve maintained a {details.get("streak", 0)} day learning streak!',
                'icon': '🔥'
            },
            'review_milestone': {
                'title': f'📚 {details.get("count", 0)} Reviews Complete!',
                'message': f'You\'ve completed {details.get("count", 0)} reviews! Keep up the great work!',
                'icon': '📚'
            },
            'perfect_day': {
                'title': '⭐ Perfect Day!',
                'message': 'You completed all your reviews for today!',
                'icon': '⭐'
            }
        }
        
        achievement = achievements.get(achievement_type, {
            'title': '🎉 Achievement Unlocked!',
            'message': 'You\'ve reached a new milestone!',
            'icon': '🏆'
        })
        
        return {
            'user_id': user_id,
            'type': 'achievement',
            'achievement_type': achievement_type,
            'title': achievement['title'],
            'message': achievement['message'],
            'icon': achievement['icon'],
            'created_at': datetime.utcnow().isoformat(),
            'details': details
        }
    
    def check_streak_milestones(self, user_id: int, current_streak: int) -> List[Dict[str, Any]]:
        """Check if user has reached streak milestones"""
        milestones = [7, 14, 30, 60, 100, 365]  # Days
        notifications = []
        
        for milestone in milestones:
            if current_streak == milestone:
                notification = self.create_achievement_notification(
                    user_id, 
                    'streak_milestone', 
                    {'streak': milestone}
                )
                notifications.append(notification)
        
        return notifications
    
    def check_review_milestones(self, user_id: int, total_reviews: int) -> List[Dict[str, Any]]:
        """Check if user has reached review count milestones"""
        milestones = [10, 50, 100, 250, 500, 1000]  # Review counts
        notifications = []
        
        for milestone in milestones:
            if total_reviews == milestone:
                notification = self.create_achievement_notification(
                    user_id, 
                    'review_milestone', 
                    {'count': milestone}
                )
                notifications.append(notification)
        
        return notifications