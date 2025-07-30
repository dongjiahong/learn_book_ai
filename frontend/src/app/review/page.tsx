'use client';

import React, { useState, useEffect } from 'react';
import { Card, Button, Typography, Space, Statistic, Row, Col, Progress, message, Spin, Empty, Badge, Alert } from 'antd';
import { ClockCircleOutlined, TrophyOutlined, FireOutlined, BookOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, DueReviewItem, ReviewStatistics, ReviewReminder } from '@/lib/api';
import ReviewSession from '@/components/learning/ReviewSession';
import ReviewStatisticsCard from '@/components/learning/ReviewStatisticsCard';
import UpcomingReviewsCard from '@/components/learning/UpcomingReviewsCard';

const { Title, Text, Paragraph } = Typography;

export default function ReviewPage() {
  const { tokens } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [dueReviews, setDueReviews] = useState<DueReviewItem[]>([]);
  const [statistics, setStatistics] = useState<ReviewStatistics | null>(null);
  const [reminders, setReminders] = useState<ReviewReminder[]>([]);
  const [currentReview, setCurrentReview] = useState<DueReviewItem | null>(null);
  const [reviewMode, setReviewMode] = useState(false);

  useEffect(() => {
    if (tokens?.access_token) {
      loadReviewData();
    }
  }, [tokens]);

  const loadReviewData = async () => {
    if (!tokens?.access_token) return;

    try {
      setLoading(true);
      const [dueReviewsData, statisticsData, remindersData] = await Promise.all([
        apiClient.getDueReviews(tokens.access_token),
        apiClient.getReviewStatistics(tokens.access_token),
        apiClient.getReviewReminders(tokens.access_token)
      ]);

      setDueReviews(dueReviewsData);
      setStatistics(statisticsData);
      setReminders(remindersData);
    } catch (error) {
      console.error('Failed to load review data:', error);
      message.error('Failed to load review data');
    } finally {
      setLoading(false);
    }
  };

  const startReviewSession = () => {
    if (dueReviews.length > 0) {
      setCurrentReview(dueReviews[0]);
      setReviewMode(true);
    }
  };

  const handleReviewComplete = async (quality: number) => {
    if (!currentReview || !tokens?.access_token) return;

    try {
      await apiClient.completeReview(tokens.access_token, {
        content_id: currentReview.content_id,
        content_type: currentReview.content_type,
        quality
      });

      // Remove completed review from list
      const updatedReviews = dueReviews.filter(review => 
        review.review_record_id !== currentReview.review_record_id
      );
      setDueReviews(updatedReviews);

      // Move to next review or exit review mode
      if (updatedReviews.length > 0) {
        setCurrentReview(updatedReviews[0]);
      } else {
        setReviewMode(false);
        setCurrentReview(null);
        message.success('All reviews completed! 🎉');
      }

      // Reload statistics
      const updatedStats = await apiClient.getReviewStatistics(tokens.access_token);
      setStatistics(updatedStats);
    } catch (error) {
      console.error('Failed to complete review:', error);
      message.error('Failed to complete review');
    }
  };

  const exitReviewMode = () => {
    setReviewMode(false);
    setCurrentReview(null);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (reviewMode && currentReview) {
    return (
      <ReviewSession
        reviewItem={currentReview}
        onComplete={handleReviewComplete}
        onExit={exitReviewMode}
        remainingCount={dueReviews.length}
      />
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <BookOutlined style={{ marginRight: '8px' }} />
          Spaced Repetition Review
        </Title>
        <Paragraph type="secondary">
          Review your learning materials using scientifically-proven spaced repetition to improve long-term retention.
        </Paragraph>
      </div>

      {/* Reminders */}
      {reminders.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          {reminders.map((reminder, index) => (
            <Alert
              key={index}
              type={reminder.priority === 'high' ? 'error' : 'warning'}
              message={reminder.title || `${reminder.content_type} review`}
              description={reminder.message}
              showIcon
              icon={reminder.type === 'overdue' ? <ExclamationCircleOutlined /> : <ClockCircleOutlined />}
              style={{ marginBottom: '8px' }}
            />
          ))}
        </div>
      )}

      {/* Statistics Overview */}
      {statistics && (
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Due Today"
                value={statistics.due_today}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: statistics.due_today > 0 ? '#f5222d' : '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Completed Today"
                value={statistics.completed_today}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Learning Streak"
                value={statistics.learning_streak}
                prefix={<FireOutlined />}
                suffix="days"
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Total Items"
                value={statistics.total_items}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Main Review Section */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card
            title={
              <Space>
                <BookOutlined />
                <span>Review Session</span>
                {dueReviews.length > 0 && (
                  <Badge count={dueReviews.length} style={{ backgroundColor: '#f5222d' }} />
                )}
              </Space>
            }
            extra={
              dueReviews.length > 0 && (
                <Button type="primary" size="large" onClick={startReviewSession}>
                  Start Review Session
                </Button>
              )
            }
          >
            {dueReviews.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <div>
                    <Text>No reviews due right now!</Text>
                    <br />
                    <Text type="secondary">Great job staying on top of your learning! 🎉</Text>
                  </div>
                }
              />
            ) : (
              <div>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>
                    You have {dueReviews.length} item{dueReviews.length !== 1 ? 's' : ''} ready for review
                  </Text>
                </div>
                
                <div style={{ marginBottom: '16px' }}>
                  <Text type="secondary">Review types:</Text>
                  <div style={{ marginTop: '8px' }}>
                    {Object.entries(
                      dueReviews.reduce((acc, review) => {
                        acc[review.content_type] = (acc[review.content_type] || 0) + 1;
                        return acc;
                      }, {} as Record<string, number>)
                    ).map(([type, count]) => (
                      <Badge
                        key={type}
                        count={count}
                        style={{ backgroundColor: type === 'question' ? '#1890ff' : '#52c41a', marginRight: '8px' }}
                        text={type === 'question' ? 'Questions' : 'Knowledge Points'}
                      />
                    ))}
                  </div>
                </div>

                {statistics && (
                  <Progress
                    percent={Math.round((statistics.completed_today / Math.max(1, statistics.completed_today + statistics.due_today)) * 100)}
                    status="active"
                    format={(percent) => `${percent}% completed today`}
                  />
                )}
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <ReviewStatisticsCard statistics={statistics} />
            <UpcomingReviewsCard />
          </Space>
        </Col>
      </Row>
    </div>
  );
}