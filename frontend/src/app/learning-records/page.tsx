'use client';

import React, { useState, useEffect } from 'react';
import { Card, Tabs, message } from 'antd';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, LearningProgressResponse } from '@/lib/api';
import LearningRecordsList from '@/components/learning/LearningRecordsList';
import LearningStatistics from '@/components/learning/LearningStatistics';
import ReviewRecordsList from '@/components/learning/ReviewRecordsList';

const { TabPane } = Tabs;

export default function LearningRecordsPage() {
  const { tokens } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [progressData, setProgressData] = useState<LearningProgressResponse | null>(null);

  useEffect(() => {
    if (tokens?.access_token) {
      loadLearningProgress();
    }
  }, [tokens]);

  const loadLearningProgress = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getLearningProgress(tokens!.access_token);
      setProgressData(data);
    } catch (error) {
      console.error('Failed to load learning progress:', error);
      message.error('Failed to load learning progress');
    } finally {
      setLoading(false);
    }
  };

  const handleRecordUpdate = () => {
    // Refresh progress data when records are updated
    loadLearningProgress();
  };

  if (!tokens) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card>
          <p>Please log in to view your learning records.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Learning Records</h1>
        <p className="text-gray-600">
          Track your learning progress, review your answers, and manage your study schedule.
        </p>
      </div>

      <Tabs defaultActiveKey="overview" size="large">
        <TabPane tab="Overview" key="overview">
          <LearningStatistics 
            statistics={progressData?.statistics} 
            loading={loading}
            onRefresh={loadLearningProgress}
          />
        </TabPane>

        <TabPane tab="Answer Records" key="records">
          <LearningRecordsList 
            onRecordUpdate={handleRecordUpdate}
            recentRecords={progressData?.recent_records}
          />
        </TabPane>

        <TabPane tab="Review Schedule" key="reviews">
          <ReviewRecordsList 
            onRecordUpdate={handleRecordUpdate}
            dueReviews={progressData?.due_reviews}
          />
        </TabPane>
      </Tabs>
    </div>
  );
}