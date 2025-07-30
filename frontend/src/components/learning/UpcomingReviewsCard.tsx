'use client';

import React, { useState, useEffect } from 'react';
import { Card, List, Typography, Space, Badge, Empty, Spin } from 'antd';
import { CalendarOutlined, BookOutlined, BulbOutlined } from '@ant-design/icons';
import { UpcomingReviews } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api';

const { Text } = Typography;

export default function UpcomingReviewsCard() {
  const { tokens } = useAuthStore();
  const [upcomingReviews, setUpcomingReviews] = useState<UpcomingReviews | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (tokens?.access_token) {
      loadUpcomingReviews();
    }
  }, [tokens]);

  const loadUpcomingReviews = async () => {
    if (!tokens?.access_token) return;

    try {
      setLoading(true);
      const data = await apiClient.getUpcomingReviews(tokens.access_token, 7);
      setUpcomingReviews(data);
    } catch (error) {
      console.error('Failed to load upcoming reviews:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  const upcomingData = upcomingReviews ? Object.entries(upcomingReviews).map(([date, reviews]) => ({
    date,
    reviews,
    formattedDate: formatDate(date)
  })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()) : [];

  return (
    <Card 
      title={
        <Space>
          <CalendarOutlined />
          <span>Upcoming Reviews</span>
        </Space>
      }
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin />
        </div>
      ) : upcomingData.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No upcoming reviews"
          style={{ margin: '20px 0' }}
        />
      ) : (
        <List
          size="small"
          dataSource={upcomingData}
          renderItem={(item) => {
            const questionCount = item.reviews.filter(r => r.content_type === 'question').length;
            const knowledgePointCount = item.reviews.filter(r => r.content_type === 'knowledge_point').length;
            
            return (
              <List.Item>
                <div style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong>{item.formattedDate}</Text>
                    <Badge count={item.reviews.length} style={{ backgroundColor: '#1890ff' }} />
                  </div>
                  <div style={{ marginTop: '4px', fontSize: '12px', color: '#666' }}>
                    <Space size="small">
                      {questionCount > 0 && (
                        <span>
                          <BookOutlined style={{ marginRight: '2px' }} />
                          {questionCount} questions
                        </span>
                      )}
                      {knowledgePointCount > 0 && (
                        <span>
                          <BulbOutlined style={{ marginRight: '2px' }} />
                          {knowledgePointCount} knowledge points
                        </span>
                      )}
                    </Space>
                  </div>
                </div>
              </List.Item>
            );
          }}
        />
      )}
    </Card>
  );
}