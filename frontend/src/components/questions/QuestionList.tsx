'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Button,
  Select,
  Input,
  message,
  Typography,
  Space,
  Tag,
  Empty,
  Spin,
  Modal,
  Form,
  InputNumber,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Progress
} from 'antd';
import {
  PlusOutlined,
  QuestionCircleOutlined,
  FileTextOutlined,
  FolderOutlined,
  ReloadOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { 
  apiClient, 
  Question, 
  KnowledgeBase, 
  Document,
  DifficultyDistribution
} from '@/lib/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

interface QuestionListProps {
  onSelectQuestion?: (question: Question) => void;
}

interface FilterState {
  knowledgeBaseId?: number;
  documentId?: number;
  difficultyLevel?: number;
  searchText?: string;
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

export function QuestionList({ onSelectQuestion }: QuestionListProps) {
  const { tokens } = useAuth();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [generateModalVisible, setGenerateModalVisible] = useState(false);
  const [statsModalVisible, setStatsModalVisible] = useState(false);
  const [difficultyStats, setDifficultyStats] = useState<DifficultyDistribution | null>(null);
  const [filters, setFilters] = useState<FilterState>({});
  const [generateForm] = Form.useForm();

  const fetchKnowledgeBases = async () => {
    if (!tokens?.access_token) return;

    try {
      const response = await apiClient.getKnowledgeBases(tokens.access_token);
      setKnowledgeBases(response.knowledge_bases);
    } catch (error) {
      console.error('Error fetching knowledge bases:', error);
    }
  };

  const fetchDocuments = async (knowledgeBaseId?: number) => {
    if (!tokens?.access_token) return;

    try {
      const response = await apiClient.getDocuments(tokens.access_token, knowledgeBaseId);
      setDocuments(response.documents);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const fetchQuestions = async () => {
    if (!tokens?.access_token) return;

    setLoading(true);
    try {
      let response;
      
      if (filters.documentId) {
        response = await apiClient.getQuestionsByDocument(tokens.access_token, filters.documentId);
      } else if (filters.knowledgeBaseId) {
        response = await apiClient.getQuestionsByKnowledgeBase(tokens.access_token, filters.knowledgeBaseId);
      } else {
        // If no specific filter, get questions from all knowledge bases
        const allQuestions: Question[] = [];
        for (const kb of knowledgeBases) {
          try {
            const kbResponse = await apiClient.getQuestionsByKnowledgeBase(tokens.access_token, kb.id);
            allQuestions.push(...kbResponse.questions);
          } catch (error) {
            console.error(`Error fetching questions for KB ${kb.id}:`, error);
          }
        }
        response = { success: true, questions: allQuestions, count: allQuestions.length };
      }

      let filteredQuestions = response.questions;

      // Apply difficulty filter
      if (filters.difficultyLevel) {
        filteredQuestions = filteredQuestions.filter(q => q.difficulty_level === filters.difficultyLevel);
      }

      // Apply search filter
      if (filters.searchText) {
        const searchLower = filters.searchText.toLowerCase();
        filteredQuestions = filteredQuestions.filter(q => 
          q.question_text.toLowerCase().includes(searchLower) ||
          (q.context && q.context.toLowerCase().includes(searchLower))
        );
      }

      setQuestions(filteredQuestions);
    } catch (error) {
      message.error('获取问题列表失败');
      console.error('Error fetching questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDifficultyStats = async () => {
    if (!tokens?.access_token) return;

    try {
      const response = await apiClient.getDifficultyDistribution(
        tokens.access_token,
        filters.knowledgeBaseId
      );
      setDifficultyStats(response);
    } catch (error) {
      console.error('Error fetching difficulty stats:', error);
    }
  };

  useEffect(() => {
    fetchKnowledgeBases();
  }, [tokens]);

  useEffect(() => {
    if (knowledgeBases.length > 0) {
      fetchQuestions();
    }
  }, [knowledgeBases, filters]);

  useEffect(() => {
    if (filters.knowledgeBaseId) {
      fetchDocuments(filters.knowledgeBaseId);
    } else {
      setDocuments([]);
      setFilters(prev => ({ ...prev, documentId: undefined }));
    }
  }, [filters.knowledgeBaseId]);

  const handleGenerateQuestions = () => {
    generateForm.resetFields();
    setGenerateModalVisible(true);
  };

  const handleGenerateSubmit = async (values: {
    target_type: 'document' | 'knowledge_base';
    target_id: number;
    num_questions: number;
    min_quality_score: number;
  }) => {
    if (!tokens?.access_token) return;

    try {
      const { target_type, target_id, num_questions, min_quality_score } = values;
      
      let response;
      if (target_type === 'document') {
        response = await apiClient.generateQuestionsForDocument(
          tokens.access_token,
          target_id,
          { num_questions, min_quality_score }
        );
      } else {
        response = await apiClient.generateQuestionsForKnowledgeBase(
          tokens.access_token,
          target_id,
          { num_questions_per_document: num_questions, min_quality_score }
        );
      }

      if (response.success) {
        message.success(`成功生成 ${response.questions_generated || 0} 个问题`);
        setGenerateModalVisible(false);
        fetchQuestions();
      } else {
        message.error(response.error || '生成问题失败');
      }
    } catch (error) {
      message.error('生成问题失败');
      console.error('Error generating questions:', error);
    }
  };

  const handleDeleteQuestion = async (questionId: number) => {
    if (!tokens?.access_token) return;

    try {
      await apiClient.deleteQuestion(tokens.access_token, questionId);
      message.success('问题删除成功');
      fetchQuestions();
    } catch (error) {
      message.error('删除问题失败');
      console.error('Error deleting question:', error);
    }
  };

  const handleShowStats = () => {
    fetchDifficultyStats();
    setStatsModalVisible(true);
  };

  const handleFilterChange = (key: keyof FilterState, value: string | number | undefined) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleClearFilters = () => {
    setFilters({});
  };



  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <Title level={3}>问题管理</Title>
        <Space>
          <Button
            icon={<BarChartOutlined />}
            onClick={handleShowStats}
          >
            统计信息
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleGenerateQuestions}
          >
            生成问题
          </Button>
        </Space>
      </div>

      {/* Filters */}
      <Card className="mb-4">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="选择知识库"
              allowClear
              style={{ width: '100%' }}
              value={filters.knowledgeBaseId}
              onChange={(value) => handleFilterChange('knowledgeBaseId', value)}
            >
              {knowledgeBases.map(kb => (
                <Option key={kb.id} value={kb.id}>
                  <FolderOutlined /> {kb.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="选择文档"
              allowClear
              style={{ width: '100%' }}
              value={filters.documentId}
              onChange={(value) => handleFilterChange('documentId', value)}
              disabled={!filters.knowledgeBaseId}
            >
              {documents.map(doc => (
                <Option key={doc.id} value={doc.id}>
                  <FileTextOutlined /> {doc.filename}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="难度等级"
              allowClear
              style={{ width: '100%' }}
              value={filters.difficultyLevel}
              onChange={(value) => handleFilterChange('difficultyLevel', value)}
            >
              {Object.entries(difficultyLabels).map(([level, label]) => (
                <Option key={level} value={parseInt(level)}>
                  {label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <Search
                placeholder="搜索问题内容"
                allowClear
                style={{ width: 200 }}
                value={filters.searchText}
                onChange={(e) => handleFilterChange('searchText', e.target.value)}
                onSearch={() => fetchQuestions()}
              />
              <Button
                icon={<ReloadOutlined />}
                onClick={handleClearFilters}
                title="清除筛选"
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Question List */}
      {questions.length === 0 && !loading ? (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无问题"
          >
            <Button type="primary" icon={<PlusOutlined />} onClick={handleGenerateQuestions}>
              生成第一个问题
            </Button>
          </Empty>
        </Card>
      ) : (
        <Spin spinning={loading}>
          <List
            grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 3, xxl: 3 }}
            dataSource={questions}
            renderItem={(question) => (
              <List.Item>
                <Card
                  hoverable
                  actions={[
                    <Button
                      key="view"
                      type="link"
                      onClick={() => onSelectQuestion?.(question)}
                    >
                      查看详情
                    </Button>,
                    <Popconfirm
                      key="delete"
                      title="确定要删除这个问题吗？"
                      description="删除后将无法恢复。"
                      onConfirm={() => handleDeleteQuestion(question.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button type="link" danger>
                        删除
                      </Button>
                    </Popconfirm>,
                  ]}
                >
                  <Card.Meta
                    avatar={<QuestionCircleOutlined className="text-2xl text-blue-500" />}
                    title={
                      <div className="flex justify-between items-start">
                        <Text strong className="text-sm line-clamp-2">
                          {question.question_text}
                        </Text>
                      </div>
                    }
                    description={
                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-1">
                          <Tag 
                            color={difficultyColors[question.difficulty_level as keyof typeof difficultyColors]}
                          >
                            {difficultyLabels[question.difficulty_level as keyof typeof difficultyLabels]}
                          </Tag>
                          {question.knowledge_base_name && (
                            <Tag icon={<FolderOutlined />}>
                              {question.knowledge_base_name}
                            </Tag>
                          )}
                          {question.document_name && (
                            <Tag icon={<FileTextOutlined />}>
                              {question.document_name}
                            </Tag>
                          )}
                        </div>
                        {question.context && (
                          <Text type="secondary" className="text-xs line-clamp-2">
                            {question.context}
                          </Text>
                        )}
                        <Text type="secondary" className="text-xs">
                          {new Date(question.created_at).toLocaleString()}
                        </Text>
                      </div>
                    }
                  />
                </Card>
              </List.Item>
            )}
          />
        </Spin>
      )}

      {/* Generate Questions Modal */}
      <Modal
        title="生成问题"
        open={generateModalVisible}
        onCancel={() => setGenerateModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={generateForm}
          layout="vertical"
          onFinish={handleGenerateSubmit}
          initialValues={{
            num_questions: 5,
            min_quality_score: 6.0
          }}
        >
          <Form.Item
            name="target_type"
            label="生成目标"
            rules={[{ required: true, message: '请选择生成目标' }]}
          >
            <Select placeholder="选择要为哪个目标生成问题">
              <Option value="knowledge_base">知识库（为所有文档生成）</Option>
              <Option value="document">单个文档</Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.target_type !== currentValues.target_type
            }
          >
            {({ getFieldValue }) => {
              const targetType = getFieldValue('target_type');
              if (!targetType) return null;

              return (
                <Form.Item
                  name="target_id"
                  label={targetType === 'knowledge_base' ? '选择知识库' : '选择文档'}
                  rules={[{ required: true, message: '请选择目标' }]}
                >
                  <Select placeholder={`选择${targetType === 'knowledge_base' ? '知识库' : '文档'}`}>
                    {targetType === 'knowledge_base' 
                      ? knowledgeBases.map(kb => (
                          <Option key={kb.id} value={kb.id}>
                            <FolderOutlined /> {kb.name}
                          </Option>
                        ))
                      : documents.map(doc => (
                          <Option key={doc.id} value={doc.id}>
                            <FileTextOutlined /> {doc.filename}
                          </Option>
                        ))
                    }
                  </Select>
                </Form.Item>
              );
            }}
          </Form.Item>

          <Form.Item
            name="num_questions"
            label="问题数量"
            rules={[{ required: true, message: '请输入问题数量' }]}
          >
            <InputNumber
              min={1}
              max={20}
              style={{ width: '100%' }}
              placeholder="每个文档生成的问题数量"
            />
          </Form.Item>

          <Form.Item
            name="min_quality_score"
            label="最低质量分数"
            rules={[{ required: true, message: '请输入最低质量分数' }]}
          >
            <InputNumber
              min={0}
              max={10}
              step={0.1}
              style={{ width: '100%' }}
              placeholder="问题质量的最低要求（0-10分）"
            />
          </Form.Item>

          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={() => setGenerateModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                开始生成
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Statistics Modal */}
      <Modal
        title="问题统计信息"
        open={statsModalVisible}
        onCancel={() => setStatsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setStatsModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        {difficultyStats && (
          <div className="space-y-4">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="总问题数"
                  value={difficultyStats.total_questions}
                  prefix={<QuestionCircleOutlined />}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="知识库"
                  value={difficultyStats.knowledge_base_id ? '单个' : '全部'}
                />
              </Col>
            </Row>

            <div>
              <Title level={5}>难度分布</Title>
              {Object.entries(difficultyStats.distribution).map(([level, count]) => {
                const percentage = difficultyStats.total_questions > 0 
                  ? (count / difficultyStats.total_questions) * 100 
                  : 0;
                
                return (
                  <div key={level} className="mb-2">
                    <div className="flex justify-between items-center mb-1">
                      <span>{difficultyStats.difficulty_labels[level]}</span>
                      <span>{count} 个 ({percentage.toFixed(1)}%)</span>
                    </div>
                    <Progress
                      percent={percentage}
                      strokeColor={difficultyColors[parseInt(level) as keyof typeof difficultyColors]}
                      size="small"
                    />
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}