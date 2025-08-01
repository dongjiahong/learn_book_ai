'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, Tabs, Typography, App } from 'antd';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ResponsiveLayout } from '@/components/layout/ResponsiveLayout';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, LearningProgressResponse } from '@/lib/api';
import LearningRecordsList from '@/components/learning/LearningRecordsList';
import LearningStatistics from '@/components/learning/LearningStatistics';
import ReviewRecordsList from '@/components/learning/ReviewRecordsList';

const { Title, Paragraph } = Typography;

export default function LearningRecordsPage() {
  const { message } = App.useApp();
  const { tokens } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [progressData, setProgressData] = useState<LearningProgressResponse | null>(null);

  const loadLearningProgress = useCallback(async () => {
    if (!tokens?.access_token) return;
    
    try {
      setLoading(true);
      const data = await apiClient.getLearningProgress(tokens.access_token);
      setProgressData(data);
    } catch (error) {
      console.error('Failed to load learning progress:', error);
      message.error('Failed to load learning progress');
    } finally {
      setLoading(false);
    }
  }, [tokens?.access_token, message]);

  useEffect(() => {
    loadLearningProgress();
  }, [loadLearningProgress]);

  const handleRecordUpdate = () => {
    // Refresh progress data when records are updated
    loadLearningProgress();
  };

  return (
    <ProtectedRoute>
      <ResponsiveLayout>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <div style={{ marginBottom: 24 }}>
            <Title level={2}>Learning Records</Title>
            <Paragraph type="secondary">
              Track your learning progress, review your answers, and manage your study schedule.
            </Paragraph>
          </div>

          <Tabs 
        defaultActiveKey="overview" 
        size="large"
        items={[
          {
            key: "overview",
            label: "Overview",
            children: (
              <LearningStatistics 
                statistics={progressData?.statistics} 
                loading={loading}
                onRefresh={loadLearningProgress}
              />
            )
          },
          {
            key: "records",
            label: "Answer Records",
            children: (
              <LearningRecordsList 
                onRecordUpdate={handleRecordUpdate}
                recentRecords={progressData?.recent_records}
              />
            )
          },
          {
            key: "reviews",
            label: "Review Schedule",
            children: (
              <ReviewRecordsList 
                onRecordUpdate={handleRecordUpdate}
                dueReviews={progressData?.due_reviews}
              />
            )
          }
        ]}
      />
        </div>
      </ResponsiveLayout>
    </ProtectedRoute>
  );
}