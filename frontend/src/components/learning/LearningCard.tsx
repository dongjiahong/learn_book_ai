'use client';

import React, { useState } from 'react';
import { Card, Button, Typography, Space, Tag, Divider } from 'antd';
import {
  EyeOutlined,
  EyeInvisibleOutlined,
  QuestionCircleOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  BulbOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

export interface LearningCardData {
  knowledge_point_id: number;
  title: string;
  question?: string;
  content: string;
  importance_level: number;
  mastery_level?: number;
  next_review?: string;
}

export interface LearningCardProps {
  knowledgePoint: LearningCardData;
  onAnswer: (masteryLevel: 0 | 1 | 2) => void;
  loading?: boolean;
  showProgress?: boolean;
  currentIndex?: number;
  totalCount?: number;
}

export default function LearningCard({
  knowledgePoint,
  onAnswer,
  loading = false,
  showProgress = false,
  currentIndex = 0,
  totalCount = 1
}: LearningCardProps) {
  const [showContent, setShowContent] = useState(false);

  const handleToggleContent = () => {
    setShowContent(!showContent);
  };

  const handleAnswer = (masteryLevel: 0 | 1 | 2) => {
    onAnswer(masteryLevel);
    // 重置状态为下一张卡片做准备
    setShowContent(false);
  };

  const getMasteryLevelColor = (level: number) => {
    switch (level) {
      case 0: return 'red';
      case 1: return 'orange';
      case 2: return 'green';
      default: return 'default';
    }
  };

  const getMasteryLevelText = (level: number) => {
    switch (level) {
      case 0: return '不会';
      case 1: return '学习中';
      case 2: return '已掌握';
      default: return '未学习';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Progress indicator */}
      {showProgress && (
        <div className="mb-4 text-center">
          <Text type="secondary">
            {currentIndex + 1} / {totalCount}
          </Text>
        </div>
      )}

      <Card className="shadow-lg">
        {/* Header with title and metadata */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <BulbOutlined className="text-blue-500" />
              <Title level={4} className="mb-0">
                {knowledgePoint.title}
              </Title>
            </div>
            <div className="flex items-center space-x-2">
              <Tag color="blue">
                重要性: {knowledgePoint.importance_level}/5
              </Tag>
              {knowledgePoint.mastery_level !== undefined && (
                <Tag color={getMasteryLevelColor(knowledgePoint.mastery_level)}>
                  {getMasteryLevelText(knowledgePoint.mastery_level)}
                </Tag>
              )}
            </div>
          </div>
        </div>

        {/* Question Section */}
        {knowledgePoint.question && (
          <Card 
            type="inner" 
            title={
              <div className="flex items-center">
                <QuestionCircleOutlined className="mr-2 text-orange-500" />
                <span>思考问题</span>
              </div>
            }
            className="mb-4"
            headStyle={{ backgroundColor: '#fff7e6', borderBottom: '1px solid #ffd591' }}
          >
            <Paragraph className="text-lg mb-0 text-center font-medium">
              {knowledgePoint.question}
            </Paragraph>
          </Card>
        )}

        {/* Content Section */}
        <Card 
          type="inner" 
          title={
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <BulbOutlined className="mr-2 text-green-500" />
                <span>知识内容</span>
              </div>
              <Button
                type="link"
                icon={showContent ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                onClick={handleToggleContent}
                className="flex items-center"
              >
                {showContent ? '隐藏内容' : '查看内容'}
              </Button>
            </div>
          }
          className="mb-6"
          headStyle={{ backgroundColor: '#f6ffed', borderBottom: '1px solid #b7eb8f' }}
        >
          {showContent ? (
            <div className="min-h-[120px]">
              <Paragraph className="text-base leading-relaxed mb-0">
                {knowledgePoint.content}
              </Paragraph>
            </div>
          ) : (
            <div className="min-h-[120px] flex items-center justify-center">
              <div className="text-center py-8">
                <EyeOutlined className="text-4xl text-gray-300 mb-3" />
                <Text type="secondary" className="text-base">
                  点击"查看内容"按钮查看知识点详细内容
                </Text>
              </div>
            </div>
          )}
        </Card>

        <Divider />

        {/* Answer Buttons */}
        <div className="text-center">
          <Title level={5} className="mb-4 text-gray-700">
            请选择您的掌握程度：
          </Title>
          <Space size="large" className="flex justify-center">
            <Button
              size="large"
              icon={<QuestionCircleOutlined />}
              onClick={() => handleAnswer(0)}
              loading={loading}
              className="min-w-[100px] h-12 bg-red-50 border-red-200 text-red-600 hover:bg-red-100 hover:border-red-300 hover:text-red-700 transition-all duration-200"
            >
              不会
            </Button>
            <Button
              size="large"
              icon={<ExclamationCircleOutlined />}
              onClick={() => handleAnswer(1)}
              loading={loading}
              className="min-w-[100px] h-12 bg-orange-50 border-orange-200 text-orange-600 hover:bg-orange-100 hover:border-orange-300 hover:text-orange-700 transition-all duration-200"
            >
              学习中
            </Button>
            <Button
              size="large"
              icon={<CheckCircleOutlined />}
              onClick={() => handleAnswer(2)}
              loading={loading}
              className="min-w-[100px] h-12 bg-green-50 border-green-200 text-green-600 hover:bg-green-100 hover:border-green-300 hover:text-green-700 transition-all duration-200"
            >
              已掌握
            </Button>
          </Space>
          
          {/* Hint text */}
          <div className="mt-4 text-center">
            <Text type="secondary" className="text-sm">
              💡 建议先思考问题，查看内容后再选择掌握程度
            </Text>
          </div>
        </div>

        {/* Next review info */}
        {knowledgePoint.next_review && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <Text type="secondary" className="text-sm">
              下次复习时间: {new Date(knowledgePoint.next_review).toLocaleString('zh-CN')}
            </Text>
          </div>
        )}
      </Card>
    </div>
  );
}