'use client';

import React, { useState } from 'react';
import {
  Card,
  Button,
  Typography,
  Space,
  Tag,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Row,
  Col,
  Divider
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  CloseOutlined,
  QuestionCircleOutlined,
  FileTextOutlined,
  FolderOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, Question, QuestionUpdateRequest } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface QuestionDetailProps {
  question: Question;
  onBack: () => void;
  onUpdate: (question: Question) => void;
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

export function QuestionDetail({ question, onBack, onUpdate }: QuestionDetailProps) {
  const { tokens } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleEdit = () => {
    form.setFieldsValue({
      question_text: question.question_text,
      context: question.context || '',
      difficulty_level: question.difficulty_level
    });
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    form.resetFields();
  };

  const handleSave = async (values: QuestionUpdateRequest) => {
    if (!tokens?.access_token) return;

    setLoading(true);
    try {
      const response = await apiClient.updateQuestion(
        tokens.access_token,
        question.id,
        values
      );

      if (response.success) {
        message.success('问题更新成功');
        onUpdate(response.question);
        setIsEditing(false);
      } else {
        message.error('更新问题失败');
      }
    } catch (error) {
      message.error('更新问题失败');
      console.error('Error updating question:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!tokens?.access_token) return;

    try {
      await apiClient.deleteQuestion(tokens.access_token, question.id);
      message.success('问题删除成功');
      onBack();
    } catch (error) {
      message.error('删除问题失败');
      console.error('Error deleting question:', error);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={onBack}
          >
            返回列表
          </Button>
          <Title level={3} className="mb-0">问题详情</Title>
        </Space>
        
        <Space>
          {!isEditing && (
            <>
              <Button
                icon={<EditOutlined />}
                onClick={handleEdit}
              >
                编辑
              </Button>
              <Popconfirm
                title="确定要删除这个问题吗？"
                description="删除后将无法恢复。"
                onConfirm={handleDelete}
                okText="确定"
                cancelText="取消"
              >
                <Button
                  danger
                  icon={<DeleteOutlined />}
                >
                  删除
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          {/* Main Content */}
          <Card>
            {isEditing ? (
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSave}
                initialValues={{
                  question_text: question.question_text,
                  context: question.context || '',
                  difficulty_level: question.difficulty_level
                }}
              >
                <Form.Item
                  name="question_text"
                  label="问题内容"
                  rules={[
                    { required: true, message: '请输入问题内容' },
                    { max: 1000, message: '问题内容不能超过1000个字符' }
                  ]}
                >
                  <TextArea
                    rows={4}
                    placeholder="请输入问题内容"
                  />
                </Form.Item>

                <Form.Item
                  name="context"
                  label="上下文"
                  rules={[
                    { max: 2000, message: '上下文不能超过2000个字符' }
                  ]}
                >
                  <TextArea
                    rows={6}
                    placeholder="请输入问题的上下文信息（可选）"
                  />
                </Form.Item>

                <Form.Item
                  name="difficulty_level"
                  label="难度等级"
                  rules={[{ required: true, message: '请选择难度等级' }]}
                >
                  <Select placeholder="选择难度等级">
                    {Object.entries(difficultyLabels).map(([level, label]) => (
                      <Option key={level} value={parseInt(level)}>
                        <Tag color={difficultyColors[parseInt(level) as keyof typeof difficultyColors]}>
                          {label}
                        </Tag>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item className="mb-0">
                  <Space>
                    <Button
                      type="primary"
                      htmlType="submit"
                      icon={<SaveOutlined />}
                      loading={loading}
                    >
                      保存
                    </Button>
                    <Button
                      icon={<CloseOutlined />}
                      onClick={handleCancelEdit}
                    >
                      取消
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            ) : (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <QuestionCircleOutlined className="text-blue-500" />
                    <Text strong>问题内容</Text>
                  </div>
                  <Card size="small" className="bg-gray-50">
                    <Paragraph className="mb-0 text-base">
                      {question.question_text}
                    </Paragraph>
                  </Card>
                </div>

                {question.context && (
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <FileTextOutlined className="text-green-500" />
                      <Text strong>上下文</Text>
                    </div>
                    <Card size="small" className="bg-gray-50">
                      <Paragraph className="mb-0">
                        {question.context}
                      </Paragraph>
                    </Card>
                  </div>
                )}

                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <Text strong>难度等级</Text>
                  </div>
                  <Tag 
                    color={difficultyColors[question.difficulty_level as keyof typeof difficultyColors]}
                  >
                    {difficultyLabels[question.difficulty_level as keyof typeof difficultyLabels]}
                  </Tag>
                </div>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* Sidebar */}
          <Card title="问题信息" size="small">
            <div className="space-y-3">
              <div>
                <Text type="secondary" className="text-xs">问题ID</Text>
                <div>
                  <Text strong>#{question.id}</Text>
                </div>
              </div>

              <Divider className="my-2" />

              {question.knowledge_base_name && (
                <div>
                  <Text type="secondary" className="text-xs">所属知识库</Text>
                  <div className="flex items-center space-x-1">
                    <FolderOutlined className="text-blue-500" />
                    <Text>{question.knowledge_base_name}</Text>
                  </div>
                </div>
              )}

              {question.document_name && (
                <div>
                  <Text type="secondary" className="text-xs">来源文档</Text>
                  <div className="flex items-center space-x-1">
                    <FileTextOutlined className="text-green-500" />
                    <Text>{question.document_name}</Text>
                  </div>
                </div>
              )}

              <Divider className="my-2" />

              <div>
                <Text type="secondary" className="text-xs">创建时间</Text>
                <div className="flex items-center space-x-1">
                  <CalendarOutlined className="text-gray-500" />
                  <Text>{new Date(question.created_at).toLocaleString()}</Text>
                </div>
              </div>
            </div>
          </Card>

          {/* Quick Actions */}
          <Card title="快速操作" size="small" className="mt-4">
            <Space direction="vertical" className="w-full">
              <Button
                block
                icon={<QuestionCircleOutlined />}
                disabled
              >
                开始答题
              </Button>
              <Button
                block
                icon={<FileTextOutlined />}
                disabled
              >
                查看相关文档
              </Button>
              <Button
                block
                icon={<FolderOutlined />}
                disabled
              >
                浏览知识库
              </Button>
            </Space>
            <Text type="secondary" className="text-xs mt-2 block">
              这些功能将在后续版本中提供
            </Text>
          </Card>
        </Col>
      </Row>
    </div>
  );
}