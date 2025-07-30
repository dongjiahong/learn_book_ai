'use client';

import React, { useState, useEffect } from 'react';
import { Card, Statistic, Row, Col, Typography, Space, Progress, Divider } from 'antd';
import { TrophyOutlined, CalendarOutlined, FireOutlined, TargetOutlined } from '@ant-design/icons';
import { ReviewStatistics, DailySummary, WeeklySummary } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api';

const { Text } = Typography;

interface ReviewStatisticsCardProps {
  statistics: ReviewStatistics | null;
}

export default function ReviewStatisticsCard({ statistics }: ReviewStatisticsCardProps) {
  const { tokens } = useAuthStore();
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [weeklySummary, setWeeklySummary] = useState<WeeklySummary | null>(null);

  useEffect(() => {
    if (tokens?.access_token) {
      loadSummaryData();
    }
  }, [tokens]);

  const loadSummaryData = async () => {
    if (!tokens?.access_token) return;

    try {
      const [daily, weekly] = await Promise.all([
        apiClient.getDailySummary(tokens.access_token),
        apiClient.getWeeklySummary(tokens.access_token)
      ]);
      setDailySummary(daily);
      setWeeklySummary(weekly);
    } catch (error) {
      console.error('Failed to load summary data:', error);
    }
  };

  if (!statistics) {
    return (
      <Card title="Review Statistics" loading>
        <div style={{ height: '200px' }} />
      </Card>
    );
  }

  return (
    <Card 
      title={
        <Space>
          <TrophyOutlined />
          <span>Review Statistics</span>
        </Space>
      }
    >
      <Row gutter={[8, 16]}>
        <Col span={12}>
          <Statistic
            title="Due This Week"
            value={statistics.due_this_week}
            prefix={<CalendarOutlined />}
            valueStyle={{ fontSize: '16px' }}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="Avg Ease Factor"
            value={statistics.average_ease_factor}
            precision={2}
            prefix={<TargetOutlined />}
            valueStyle={{ fontSize: '16px' }}
          />
        </Col>
      </Row>

      {dailySummary && (
        <>
          <Divider />
          <div style={{ marginBottom: '16px' }}>
            <Text strong>Today's Progress</Text>
            <Progress
              percent={Math.round(dailySummary.completion_rate)}
              size="small"
              style={{ marginTop: '8px' }}
              format={(percent) => `${percent}%`}
            />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
              {dailySummary.completed_today} completed, {dailySummary.due_today} due
            </div>
          </div>
        </>
      )}

      {weeklySummary && (
        <>
          <Divider />
          <div>
            <Text strong>This Week</Text>
            <div style={{ marginTop: '8px' }}>
              <Statistic
                title="Total Completed"
                value={weeklySummary.total_completed}
                valueStyle={{ fontSize: '16px' }}
              />
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                Average: {weeklySummary.average_per_day.toFixed(1)} per day
              </div>
            </div>
          </div>
        </>
      )}
    </Card>
  );
}