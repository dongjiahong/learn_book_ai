'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Card,
  Typography,
  Button,
  Space,
  Progress,
  Spin,
  Empty,
  App
} from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, LearningSetDetailResponse } from '@/lib/api';
import LearningCard, { LearningCardData } from '@/components/learning/LearningCard';

const { Title, Text } = Typography;

// 使用 LearningCardData 类型替代 StudyItem
type StudyItem = LearningCardData;

export default function StudyPage() {
  const params = useParams();
  const router = useRouter();
  const { tokens } = useAuth();
  const { message } = App.useApp();
  
  const [learningSet, setLearningSet] = useState<LearningSetDetailResponse | null>(null);
  const [studyItems, setStudyItems] = useState<StudyItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [sessionStats, setSessionStats] = useState({
    total: 0,
    completed: 0,
    mastered: 0,
    learning: 0,
    notLearned: 0
  });
  
  const learningSetId = parseInt(params.id as string);

  const fetchLearningSetDetail = useCallback(async () => {
    if (!tokens?.access_token || !learningSetId) return;

    setLoading(true);
    try {
      const response = await apiClient.getLearningSet(tokens.access_token, learningSetId);
      setLearningSet(response);
      
      // 转换为学习项目格式
      const items: StudyItem[] = response.items.map(item => ({
        knowledge_point_id: item.knowledge_point_id,
        title: item.knowledge_point_title,
        question: item.knowledge_point_question,
        content: item.knowledge_point_content,
        importance_level: item.knowledge_point_importance,
        mastery_level: item.mastery_level,
        next_review: item.next_review
      }));
      
      setStudyItems(items);
      setSessionStats({
        total: items.length,
        completed: 0,
        mastered: 0,
        learning: 0,
        notLearned: 0
      });
    } catch (error) {
      message.error('获取学习集详情失败');
      console.error('Error fetching learning set detail:', error);
    } finally {
      setLoading(false);
    }
  }, [tokens?.access_token, learningSetId, message]);

  useEffect(() => {
    fetchLearningSetDetail();
  }, [fetchLearningSetDetail]);

  const handleBack = () => {
    router.push(`/learning-sets/${learningSetId}`);
  };

  const handleAnswer = async (masteryLevel: 0 | 1 | 2) => {
    if (!tokens?.access_token || !learningSet) return;

    const currentItem = studyItems[currentIndex];
    if (!currentItem) return;

    setSubmitting(true);
    try {
      await apiClient.createOrUpdateLearningRecord(tokens.access_token, {
        knowledge_point_id: currentItem.knowledge_point_id,
        learning_set_id: learningSet.id,
        mastery_level: masteryLevel
      });

      // 更新统计信息
      setSessionStats(prev => ({
        ...prev,
        completed: prev.completed + 1,
        mastered: masteryLevel === 2 ? prev.mastered + 1 : prev.mastered,
        learning: masteryLevel === 1 ? prev.learning + 1 : prev.learning,
        notLearned: masteryLevel === 0 ? prev.notLearned + 1 : prev.notLearned
      }));

      // 移动到下一个项目
      if (currentIndex < studyItems.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else {
        setSessionComplete(true);
      }
    } catch (error) {
      message.error('提交学习记录失败');
      console.error('Error submitting learning record:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRestartSession = () => {
    setCurrentIndex(0);
    setSessionComplete(false);
    setSessionStats({
      total: studyItems.length,
      completed: 0,
      mastered: 0,
      learning: 0,
      notLearned: 0
    });
  };

  const handleFinishSession = () => {
    router.push(`/learning-sets/${learningSetId}`);
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center items-center h-64">
          <Spin size="large" />
        </div>
      </div>
    );
  }

  if (!learningSet || studyItems.length === 0) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Card>
          <Empty description="没有可学习的知识点" />
          <div className="text-center mt-4">
            <Button onClick={handleBack}>返回学习集</Button>
          </div>
        </Card>
      </div>
    );
  }

  const currentItem = studyItems[currentIndex];
  const progress = sessionStats.total > 0 ? (sessionStats.completed / sessionStats.total) * 100 : 0;

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={handleBack}
          >
            返回学习集
          </Button>
          <div className="text-center">
            <Text type="secondary">
              {sessionStats.completed + 1} / {sessionStats.total}
            </Text>
          </div>
        </div>
        
        <Title level={3} className="text-center mb-4">
          {learningSet.name} - 学习模式
        </Title>
        
        <Progress 
          percent={progress} 
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          className="mb-4"
        />
      </div>

      {!sessionComplete ? (
        /* Learning Card */
        <LearningCard
          knowledgePoint={currentItem}
          onAnswer={handleAnswer}
          loading={submitting}
          showProgress={true}
          currentIndex={currentIndex}
          totalCount={studyItems.length}
        />
      ) : (
        /* Session Complete */
        <Card className="text-center">
          <div className="py-8">
            <CheckCircleOutlined className="text-6xl text-green-500 mb-4" />
            <Title level={2} className="mb-4">
              学习完成！
            </Title>
            
            <div className="mb-6">
              <Space size="large">
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {sessionStats.mastered}
                  </div>
                  <div className="text-sm text-gray-500">已掌握</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-orange-600">
                    {sessionStats.learning}
                  </div>
                  <div className="text-sm text-gray-500">学习中</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">
                    {sessionStats.notLearned}
                  </div>
                  <div className="text-sm text-gray-500">需要加强</div>
                </div>
              </Space>
            </div>
            
            <Space>
              <Button size="large" onClick={handleRestartSession}>
                重新学习
              </Button>
              <Button type="primary" size="large" onClick={handleFinishSession}>
                完成学习
              </Button>
            </Space>
          </div>
        </Card>
      )}
    </div>
  );
}