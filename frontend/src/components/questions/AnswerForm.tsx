'use client';

import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  Space,
  Tag,
  message,
  Spin,
  Alert,
  Divider
} from 'antd';
import {
  SendOutlined,
  QuestionCircleOutlined,
  FileTextOutlined,
  FolderOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, Question, AnswerEvaluationResponse } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface AnswerFormProps {
  question: Question;
  onSubmitSuccess?: (result: AnswerEvaluationResponse) => void;
  onBack?: () => void;
}

const difficultyLabels = {
  1: '基础记忆',
  2: '简单理解',
  3: '应用分析',
  4: '综合评价',
  5: '复杂推理'
};

const difficultyColors = {
  1: 'green',
  2: 'blue',
  3: 'orange',
  4: 'red',
  5: 'purple'
};

export function AnswerForm({ question, onSubmitSuccess, onBack }: AnswerFormProps) {
  const { tokens } = useAuth();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [startTime] = useState(Date.now());

  const handleSubmit = async (values: { user_answer: string }) => {
    if (!tokens?.access_token) {
      message.error('请先登录');
      return;
    }

    if (!values.user_answer.trim()) {
      message.error('请输入答案');
      return;
    }

    setLoading(true);
    try {
      const result = await apiClient.submitAnswer(tokens.access_token, {
        question_id: question.id,
        user_answer: values.user_answer.trim(),
        save_record: true
      });

      if (result.success) {
        message.success('答案提交成功！');
        onSubmitSuccess?.(result);
      } else {
        message.error('答案提交失败');
      }
    } catch (error) {
      message.error('答案提交失败');
      console.error('Error submitting answer:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAnswerTime = () => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <Title level={2} className="mb-2">答题练习</Title>
            <Text type="secondary">请仔细阅读问题，然后输入您的答案</Text>
          </div>
          <div className="text-right">
            <div className="flex items-center space-x-2 text-gray-500 mb-2">
              <ClockCircleOutlined />
              <Text type="secondary">答题时间: {getAnswerTime()}</Text>
            </div>
            {onBack && (
              <Button onClick={onBack}>
                返回
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Question Card */}
      <Card className="mb-6">
        <div className="space-y-4">
          {/* Question Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2">
              <QuestionCircleOutlined className="text-blue-500 text-lg" />
              <Title level={4} className="mb-0">问题</Title>
            </div>
            <div className="flex items-center space-x-2">
              <Tag 
                color={difficultyColors[question.difficulty_level as keyof typeof difficultyColors]}
              >
                {difficultyLabels[question.difficulty_level as keyof typeof difficultyLabels]}
              </Tag>
            </div>
          </div>

          {/* Question Content */}
          <Card size="small" className="bg-blue-50 border-blue-200">
            <Paragraph className="mb-0 text-base font-medium">
              {question.question_text}
            </Paragraph>
          </Card>

          {/* Context */}
          {question.context && (
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <FileTextOutlined className="text-green-500" />
                <Text strong>参考上下文</Text>
              </div>
              <Card size="small" className="bg-green-50 border-green-200">
                <Paragraph className="mb-0 text-sm">
                  {question.context}
                </Paragraph>
              </Card>
            </div>
          )}

          {/* Question Meta */}
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            {question.knowledge_base_name && (
              <div className="flex items-center space-x-1">
                <FolderOutlined />
                <span>知识库: {question.knowledge_base_name}</span>
              </div>
            )}
            {question.document_name && (
              <div className="flex items-center space-x-1">
                <FileTextOutlined />
                <span>文档: {question.document_name}</span>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Answer Form */}
      <Card title="您的答案">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="user_answer"
            rules={[
              { required: true, message: '请输入您的答案' },
              { min: 10, message: '答案至少需要10个字符' },
              { max: 2000, message: '答案不能超过2000个字符' }
            ]}
          >
            <TextArea
              rows={8}
              placeholder="请在此输入您的答案...&#10;&#10;提示：&#10;• 请尽量详细和准确地回答问题&#10;• 可以结合上下文信息进行回答&#10;• 答案将通过AI进行自动评估"
              disabled={loading}
              showCount
              maxLength={2000}
            />
          </Form.Item>

          <Form.Item className="mb-0">
            <div className="flex justify-between items-center">
              <Alert
                message="答案提交后将进行AI评估，包括评分、反馈和参考答案对比"
                type="info"
                showIcon
                className="flex-1 mr-4"
              />
              <Button
                type="primary"
                htmlType="submit"
                icon={<SendOutlined />}
                loading={loading}
                size="large"
              >
                {loading ? '评估中...' : '提交答案'}
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Card>

      {/* Tips */}
      <Card size="small" className="mt-4 bg-gray-50">
        <Title level={5} className="mb-2">答题提示</Title>
        <ul className="text-sm text-gray-600 space-y-1 mb-0">
          <li>• 仔细阅读问题和上下文信息</li>
          <li>• 答案要准确、完整、清晰</li>
          <li>• 可以适当展开说明，但要紧扣主题</li>
          <li>• 提交后将获得详细的评估反馈</li>
        </ul>
      </Card>
    </div>
  );
}