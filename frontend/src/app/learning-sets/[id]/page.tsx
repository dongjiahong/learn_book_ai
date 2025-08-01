'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Card,
  Typography,
  Button,
  Space,
  Tag,
  Spin,
  Empty,
  Progress,
  Row,
  Col,
  Statistic,
  List,
  Avatar,
  Tooltip,
  App
} from 'antd';
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  BookOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  QuestionCircleOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, LearningSetDetailResponse, LearningSetItem } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

export default function LearningSetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { tokens } = useAuth();
  const { message } = App.useApp();
  
  const [learningSet, setLearningSet] = useState<LearningSetDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const learningSetId = parseInt(params.id as string);

  const fetchLearningSetDetail = useCallback(async () => {
    if (!tokens?.access_token || !learningSetId) return;

    setLoading(true);
    try {
      const response = await apiClient.getLearningSet(tokens.access_token, learningSetId);
      setLearningSet(response);
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

  const handleStartLearning = () => {
    if (learningSet) {
      router.push(`/learning-sets/${learningSet.id}/study`);
    }
  };

  const handleBack = () => {
    router.push('/learning-sets');
  };

  const getMasteryIcon = (masteryLevel?: number) => {
    switch (masteryLevel) {
      case 0:
        return <QuestionCircleOutlined className="text-gray-400" />;
      case 1:
        return <ExclamationCircleOutlined className="text-orange-500" />;
      case 2:
        return <CheckCircleOutlined className="text-green-500" />;
      default:
        return <QuestionCircleOutlined className="text-gray-400" />;
    }
  };

  const getMasteryText = (masteryLevel?: number) => {
    switch (masteryLevel) {
      case 0:
        return '未学习';
      case 1:
        return '学习中';
      case 2:
        return '已掌握';
      default:
        return '未知';
    }
  };

  const getMasteryColor = (masteryLevel?: number) => {
    switch (masteryLevel) {
      case 0:
        return 'default';
      case 1:
        return 'orange';
      case 2:
        return 'green';
      default:
        return 'default';
    }
  };

  const formatNextReview = (nextReview?: string) => {
    if (!nextReview) return '无';
    
    const reviewDate = new Date(nextReview);
    const now = new Date();
    const diffTime = reviewDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return '需要复习';
    } else if (diffDays === 0) {
      return '今天';
    } else if (diffDays === 1) {
      return '明天';
    } else {
      return `${diffDays}天后`;
    }
  };

  const getNextReviewColor = (nextReview?: string) => {
    if (!nextReview) return 'default';
    
    const reviewDate = new Date(nextReview);
    const now = new Date();
    const diffTime = reviewDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return 'red';
    } else if (diffDays === 0) {
      return 'orange';
    } else {
      return 'default';
    }
  };

  const getDueItemsCount = () => {
    if (!learningSet?.items) return 0;
    
    const now = new Date();
    return learningSet.items.filter(item => {
      if (!item.next_review) return false;
      return new Date(item.next_review) <= now;
    }).length;
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

  if (!learningSet) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Card>
          <Empty description="学习集不存在" />
        </Card>
      </div>
    );
  }

  const progress = (learningSet.total_items || 0) > 0 
    ? ((learningSet.mastered_items || 0) / (learningSet.total_items || 0)) * 100 
    : 0;
  const dueItemsCount = getDueItemsCount();

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={handleBack}
            className="mb-2"
          >
            返回学习集列表
          </Button>
          <Space>
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />}
              onClick={handleStartLearning}
              size="large"
            >
              开始学习
            </Button>
          </Space>
        </div>
        
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <Title level={2} className="mb-2">
              <BookOutlined className="mr-2" />
              {learningSet.name}
            </Title>
            {learningSet.description && (
              <Paragraph type="secondary" className="mb-4">
                {learningSet.description}
              </Paragraph>
            )}
            <Space wrap>
              <Tag icon={<BookOutlined />}>
                {learningSet.knowledge_base_name}
              </Tag>
              <Tag>
                创建于 {new Date(learningSet.created_at).toLocaleDateString()}
              </Tag>
            </Space>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总知识点"
              value={learningSet.total_items}
              prefix={<BookOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已掌握"
              value={learningSet.mastered_items}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="学习中"
              value={learningSet.learning_items}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待复习"
              value={dueItemsCount}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: dueItemsCount > 0 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Progress Card */}
      <Card className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <Title level={4} className="mb-0">学习进度</Title>
          <Text strong>{progress.toFixed(1)}%</Text>
        </div>
        <Progress
          percent={progress}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          className="mb-4"
        />
        <Row gutter={16}>
          <Col span={8}>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {learningSet.new_items}
              </div>
              <div className="text-sm text-gray-500">新学习</div>
            </div>
          </Col>
          <Col span={8}>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {learningSet.learning_items}
              </div>
              <div className="text-sm text-gray-500">学习中</div>
            </div>
          </Col>
          <Col span={8}>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {learningSet.mastered_items}
              </div>
              <div className="text-sm text-gray-500">已掌握</div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Knowledge Points List */}
      <Card title="知识点列表" className="mb-6">
        {learningSet.items && learningSet.items.length > 0 ? (
          <List
            itemLayout="horizontal"
            dataSource={learningSet.items}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `第 ${range[0]}-${range[1]} 项，共 ${total} 项`,
            }}
            renderItem={(item: LearningSetItem) => (
              <List.Item
                actions={[
                  <Tag 
                    key="mastery" 
                    color={getMasteryColor(item.mastery_level)}
                    icon={getMasteryIcon(item.mastery_level)}
                  >
                    {getMasteryText(item.mastery_level)}
                  </Tag>,
                  <Tooltip key="next-review" title="下次复习时间">
                    <Tag 
                      color={getNextReviewColor(item.next_review)}
                      icon={<CalendarOutlined />}
                    >
                      {formatNextReview(item.next_review)}
                    </Tag>
                  </Tooltip>,
                  <Text key="review-count" type="secondary">
                    复习 {item.review_count} 次
                  </Text>
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <Avatar 
                      icon={getMasteryIcon(item.mastery_level)} 
                      style={{
                        backgroundColor: item.mastery_level === 2 ? '#f6ffed' : 
                                        item.mastery_level === 1 ? '#fff7e6' : '#fafafa',
                        border: '1px solid #d9d9d9'
                      }}
                    />
                  }
                  title={
                    <div className="flex items-center justify-between">
                      <Text strong className="text-base">
                        {item.knowledge_point_title}
                      </Text>
                      <Text type="secondary" className="text-sm">
                        重要性: {item.knowledge_point_importance}/5
                      </Text>
                    </div>
                  }
                  description={
                    <div className="space-y-2">
                      {item.knowledge_point_question && (
                        <div>
                          <Text strong className="text-blue-600">问题：</Text>
                          <Text className="ml-2">{item.knowledge_point_question}</Text>
                        </div>
                      )}
                      <div>
                        <Text type="secondary" className="line-clamp-2">
                          {item.knowledge_point_content}
                        </Text>
                      </div>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          <Empty description="暂无知识点" />
        )}
      </Card>
    </div>
  );
}