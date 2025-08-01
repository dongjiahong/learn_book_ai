#!/usr/bin/env python3
"""
Test script for learning records and spaced repetition functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.services.spaced_repetition_service import spaced_repetition_service


def test_spaced_repetition_service():
    """Test the spaced repetition service"""
    print("Testing Spaced Repetition Service...")
    
    # Test initial values
    print("\n1. Testing initial values:")
    interval, ease_factor, next_review = spaced_repetition_service.get_initial_values()
    print(f"Initial interval: {interval} days")
    print(f"Initial ease factor: {ease_factor}")
    print(f"Initial next review: {next_review}")
    
    # Test calculate_next_review for different mastery levels
    print("\n2. Testing calculate_next_review for different mastery levels:")
    
    # Test case 1: Not learned (mastery_level = 0)
    print("\nCase 1: Not learned (mastery_level = 0)")
    interval, ease_factor, next_review = spaced_repetition_service.calculate_next_review(
        mastery_level=0,
        current_ease_factor=2.5,
        current_interval=1,
        review_count=0
    )
    print(f"New interval: {interval} days")
    print(f"New ease factor: {ease_factor}")
    print(f"Next review: {next_review}")
    
    # Test case 2: Learning (mastery_level = 1)
    print("\nCase 2: Learning (mastery_level = 1)")
    interval, ease_factor, next_review = spaced_repetition_service.calculate_next_review(
        mastery_level=1,
        current_ease_factor=2.5,
        current_interval=1,
        review_count=1
    )
    print(f"New interval: {interval} days")
    print(f"New ease factor: {ease_factor}")
    print(f"Next review: {next_review}")
    
    # Test case 3: Mastered (mastery_level = 2)
    print("\nCase 3: Mastered (mastery_level = 2)")
    interval, ease_factor, next_review = spaced_repetition_service.calculate_next_review(
        mastery_level=2,
        current_ease_factor=2.5,
        current_interval=1,
        review_count=1
    )
    print(f"New interval: {interval} days")
    print(f"New ease factor: {ease_factor}")
    print(f"Next review: {next_review}")
    
    # Test progressive learning
    print("\n3. Testing progressive learning scenario:")
    current_ease = 2.5
    current_interval = 1
    review_count = 0
    
    for i in range(5):
        mastery_level = 2 if i > 2 else 1  # Start learning, then master
        interval, ease_factor, next_review = spaced_repetition_service.calculate_next_review(
            mastery_level=mastery_level,
            current_ease_factor=current_ease,
            current_interval=current_interval,
            review_count=review_count
        )
        
        print(f"Review {i+1}: mastery={mastery_level}, interval={interval}, ease={ease_factor:.2f}")
        
        # Update for next iteration
        current_ease = ease_factor
        current_interval = interval
        review_count += 1
    
    # Test priority calculation
    print("\n4. Testing priority calculation:")
    now = datetime.now()
    
    # High priority: not learned and overdue
    priority = spaced_repetition_service.get_study_priority(
        mastery_level=0,
        next_review=now - timedelta(days=2),
        importance_level=5
    )
    print(f"Not learned, overdue, high importance: {priority:.2f}")
    
    # Medium priority: learning and due
    priority = spaced_repetition_service.get_study_priority(
        mastery_level=1,
        next_review=now,
        importance_level=3
    )
    print(f"Learning, due, medium importance: {priority:.2f}")
    
    # Low priority: mastered and not due
    priority = spaced_repetition_service.get_study_priority(
        mastery_level=2,
        next_review=now + timedelta(days=5),
        importance_level=1
    )
    print(f"Mastered, not due, low importance: {priority:.2f}")
    
    # Test recommended study time
    print("\n5. Testing recommended study time:")
    for mastery in [0, 1, 2]:
        for importance in [1, 3, 5]:
            time = spaced_repetition_service.get_recommended_study_time(mastery, importance)
            print(f"Mastery {mastery}, Importance {importance}: {time} minutes")
    
    print("\n✅ All spaced repetition tests completed successfully!")


def test_is_due_for_review():
    """Test the is_due_for_review function"""
    print("\n6. Testing is_due_for_review:")
    
    now = datetime.now()
    
    # Past date - should be due
    past_date = now - timedelta(hours=1)
    is_due = spaced_repetition_service.is_due_for_review(past_date)
    print(f"Past date ({past_date}): {is_due}")
    
    # Future date - should not be due
    future_date = now + timedelta(hours=1)
    is_due = spaced_repetition_service.is_due_for_review(future_date)
    print(f"Future date ({future_date}): {is_due}")
    
    # Current time - should be due
    is_due = spaced_repetition_service.is_due_for_review(now)
    print(f"Current time ({now}): {is_due}")


def test_retention_rate():
    """Test retention rate calculation"""
    print("\n7. Testing retention rate calculation:")
    
    test_cases = [
        (0, 1, 2.5),  # Not learned
        (1, 1, 2.5),  # Learning, 1 day
        (1, 7, 2.5),  # Learning, 1 week
        (2, 1, 2.5),  # Mastered, 1 day
        (2, 7, 2.5),  # Mastered, 1 week
        (2, 30, 2.5), # Mastered, 1 month
    ]
    
    for mastery, days, ease in test_cases:
        retention = spaced_repetition_service.calculate_retention_rate(mastery, days, ease)
        print(f"Mastery {mastery}, {days} days, ease {ease}: {retention:.2%} retention")


if __name__ == "__main__":
    print("🧠 Testing Learning Records and Spaced Repetition Functionality")
    print("=" * 60)
    
    try:
        test_spaced_repetition_service()
        test_is_due_for_review()
        test_retention_rate()
        
        print("\n🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)