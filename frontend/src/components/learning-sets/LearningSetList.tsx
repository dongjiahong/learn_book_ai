'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  List,
  Button,
  Typography,
  Space,
  Tag,
  Empty,
  Spin,
  Modal,
  Form,
  Input,
  Select,
  Checkbox,
  Popconfirm,
  Progress,
  Row,
  Col,
  App
} from 'antd';
import {
  PlusOutlined,
  BookOutlined,
  FolderOutlined,
  FileTextOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { 
  apiClient, 
  LearningSet, 
  KnowledgeBase, 
  Document,
  LearningSetCreate,
  LearningSetUpdate
} from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface LearningSetListProps {
  onSelectLearningSet?: (learningSet: LearningSet) => void;
}

export function LearningSetList({ onSelectLearningSet }: LearningSetListProps) {
  const { tokens } = useAuth();
  const { message } = App.useApp();
  const [learningSets, setLearningSets] = useState<LearningSet[]>([]);
  
  // 调试状态变化
  useEffect(() => {
    console.log('Learning sets state updated:', learningSets);
    console.log('Learning sets length:', learningSets.length);
  }, [learningSets]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingLearningSet, setEditingLearningSet] = useState<LearningSet | null>(null);
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState<number | undefined>();
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<number[]>([]);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const fetchLearningSets = useCallback(async () => {
    if (!tokens?.access_token) return;

    setLoading(true);
    try {
      const response = await apiClient.getLearningSets(tokens.access_token);
      console.log('Learning sets response:', response); // 调试日志
      
      // 后端返回的是数组格式
      if (Array.isArray(response)) {
        setLearningSets(response);
      } else {
        console.warn('Unexpected response structure:', response);
        setLearningSets([]);
      }
    } catch (error) {
      message.error('获取学习集列表失败');
      console.error('Error fetching learning sets:', error);
      setLearningSets([]); // 确保在错误时设置为空数组
    } finally {
      setLoading(false);
    }
  }, [tokens?.access_token, message]);

  const fetchKnowledgeBases = useCallback(async () => {
    if (!tokens?.access_token) return;

    try {
      const response = await apiClient.getKnowledgeBases(tokens.access_token);
      setKnowledgeBases(response.knowledge_bases || []);
    } catch (error) {
      console.error('Error fetching knowledge bases:', error);
      setKnowledgeBases([]);
    }
  }, [tokens?.access_token]);

  const fetchDocuments = useCallback(async (knowledgeBaseId: number) => {
    if (!tokens?.access_token) return;

    try {
      const response = await apiClient.getDocuments(tokens.access_token, knowledgeBaseId);
      setDocuments(response.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setDocuments([]);
    }
  }, [tokens?.access_token]);

  useEffect(() => {
    fetchLearningSets();
    fetchKnowledgeBases();
  }, [tokens, fetchLearningSets, fetchKnowledgeBases]);

  useEffect(() => {
    if (selectedKnowledgeBaseId) {
      fetchDocuments(selectedKnowledgeBaseId);
    } else {
      setDocuments([]);
      setSelectedDocumentIds([]);
    }
  }, [selectedKnowledgeBaseId, fetchDocuments]);

  const handleCreateLearningSet = () => {
    createForm.resetFields();
    setSelectedKnowledgeBaseId(undefined);
    setSelectedDocumentIds([]);
    setCreateModalVisible(true);
  };

  const handleCreateSubmit = async (values: {
    name: string;
    description?: string;
    knowledge_base_id: number;
  }) => {
    if (!tokens?.access_token) return;

    if (selectedDocumentIds.length === 0) {
      message.error('请至少选择一个文档');
      return;
    }

    try {
      const createData: LearningSetCreate = {
        name: values.name,
        description: values.description,
        knowledge_base_id: values.knowledge_base_id,
        document_ids: selectedDocumentIds,
      };

      const result = await apiClient.createLearningSet(tokens.access_token, createData);
      console.log('Create learning set result:', result); // 调试日志
      message.success('学习集创建成功');
      setCreateModalVisible(false);
      // 重置表单和状态
      createForm.resetFields();
      setSelectedKnowledgeBaseId(undefined);
      setSelectedDocumentIds([]);
      // 刷新列表
      await fetchLearningSets();
    } catch (error) {
      message.error('创建学习集失败');
      console.error('Error creating learning set:', error);
    }
  };

  const handleEditLearningSet = (learningSet: LearningSet) => {
    setEditingLearningSet(learningSet);
    editForm.setFieldsValue({
      name: learningSet.name,
      description: learningSet.description,
    });
    setEditModalVisible(true);
  };

  const handleEditSubmit = async (values: LearningSetUpdate) => {
    if (!tokens?.access_token || !editingLearningSet) return;

    try {
      await apiClient.updateLearningSet(tokens.access_token, editingLearningSet.id, values);
      message.success('学习集更新成功');
      setEditModalVisible(false);
      setEditingLearningSet(null);
      fetchLearningSets();
    } catch (error) {
      message.error('更新学习集失败');
      console.error('Error updating learning set:', error);
    }
  };

  const handleDeleteLearningSet = async (id: number) => {
    if (!tokens?.access_token) return;

    try {
      await apiClient.deleteLearningSet(tokens.access_token, id);
      message.success('学习集删除成功');
      fetchLearningSets();
    } catch (error) {
      message.error('删除学习集失败');
      console.error('Error deleting learning set:', error);
    }
  };

  const handleKnowledgeBaseChange = (knowledgeBaseId: number) => {
    setSelectedKnowledgeBaseId(knowledgeBaseId);
    createForm.setFieldsValue({ knowledge_base_id: knowledgeBaseId });
  };

  const handleDocumentSelectionChange = (documentIds: number[]) => {
    setSelectedDocumentIds(documentIds);
  };

  const getMasteryProgress = (learningSet: LearningSet) => {
    const total = learningSet.total_items || 0;
    const mastered = learningSet.mastered_items || 0;
    return total > 0 ? (mastered / total) * 100 : 0;
  };

  const getMasteryColor = (progress: number) => {
    if (progress >= 80) return '#52c41a';
    if (progress >= 60) return '#faad14';
    if (progress >= 40) return '#fa8c16';
    return '#f5222d';
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <Title level={3}>学习集管理</Title>
        <Space>
          <Button
            icon={<PlusOutlined />}
            onClick={fetchLearningSets}
            loading={loading}
          >
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateLearningSet}
          >
            创建学习集
          </Button>
        </Space>
      </div>

      {/* Learning Set List */}
      {learningSets.length === 0 && !loading ? (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无学习集"
          >
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateLearningSet}>
              创建第一个学习集
            </Button>
          </Empty>
        </Card>
      ) : (
        <Spin spinning={loading}>
          <List
            grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 3, xxl: 3 }}
            dataSource={learningSets}
            renderItem={(learningSet) => {
              const progress = getMasteryProgress(learningSet);
              return (
                <List.Item>
                  <Card
                    hoverable
                    actions={[
                      <Button
                        key="start"
                        type="link"
                        icon={<PlayCircleOutlined />}
                        onClick={() => onSelectLearningSet?.(learningSet)}
                      >
                        开始学习
                      </Button>,
                      <Button
                        key="edit"
                        type="link"
                        icon={<EditOutlined />}
                        onClick={() => handleEditLearningSet(learningSet)}
                      >
                        编辑
                      </Button>,
                      <Popconfirm
                        key="delete"
                        title="确定要删除这个学习集吗？"
                        description="删除后将无法恢复。"
                        onConfirm={() => handleDeleteLearningSet(learningSet.id)}
                        okText="确定"
                        cancelText="取消"
                      >
                        <Button type="link" danger icon={<DeleteOutlined />}>
                          删除
                        </Button>
                      </Popconfirm>,
                    ]}
                  >
                    <Card.Meta
                      avatar={<BookOutlined className="text-2xl text-blue-500" />}
                      title={
                        <div className="flex justify-between items-start">
                          <Text strong className="text-sm line-clamp-2">
                            {learningSet.name}
                          </Text>
                        </div>
                      }
                      description={
                        <div className="space-y-3">
                          {learningSet.description && (
                            <Text type="secondary" className="text-xs line-clamp-2">
                              {learningSet.description}
                            </Text>
                          )}
                          
                          <div className="flex flex-wrap gap-1">
                            <Tag icon={<FolderOutlined />}>
                              {learningSet.knowledge_base_name}
                            </Tag>
                            <Tag>
                              {learningSet.total_items || 0} 个知识点
                            </Tag>
                          </div>

                          {/* Progress Statistics */}
                          <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                              <span>掌握进度</span>
                              <span>{progress.toFixed(1)}%</span>
                            </div>
                            <Progress
                              percent={progress}
                              strokeColor={getMasteryColor(progress)}
                              size="small"
                              showInfo={false}
                            />
                            
                            <Row gutter={8}>
                              <Col span={8}>
                                <div className="text-center">
                                  <div className="text-xs text-gray-500">新学习</div>
                                  <div className="text-sm font-medium text-blue-600">
                                    {learningSet.new_items || 0}
                                  </div>
                                </div>
                              </Col>
                              <Col span={8}>
                                <div className="text-center">
                                  <div className="text-xs text-gray-500">学习中</div>
                                  <div className="text-sm font-medium text-orange-600">
                                    {learningSet.learning_items || 0}
                                  </div>
                                </div>
                              </Col>
                              <Col span={8}>
                                <div className="text-center">
                                  <div className="text-xs text-gray-500">已掌握</div>
                                  <div className="text-sm font-medium text-green-600">
                                    {learningSet.mastered_items || 0}
                                  </div>
                                </div>
                              </Col>
                            </Row>
                          </div>

                          <Text type="secondary" className="text-xs">
                            创建于 {new Date(learningSet.created_at).toLocaleString()}
                          </Text>
                        </div>
                      }
                    />
                  </Card>
                </List.Item>
              );
            }}
          />
        </Spin>
      )}

      {/* Create Learning Set Modal */}
      <Modal
        title="创建学习集"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateSubmit}
        >
          <Form.Item
            name="name"
            label="学习集名称"
            rules={[{ required: true, message: '请输入学习集名称' }]}
          >
            <Input placeholder="输入学习集名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              placeholder="输入学习集描述（可选）"
              rows={3}
            />
          </Form.Item>

          <Form.Item
            name="knowledge_base_id"
            label="选择知识库"
            rules={[{ required: true, message: '请选择知识库' }]}
          >
            <Select
              placeholder="选择知识库"
              onChange={handleKnowledgeBaseChange}
            >
              {knowledgeBases.map(kb => (
                <Option key={kb.id} value={kb.id}>
                  <FolderOutlined /> {kb.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          {selectedKnowledgeBaseId && (
            <Form.Item
              label="选择文档"
              required
            >
              <div className="max-h-60 overflow-y-auto border border-gray-200 rounded p-3">
                <Checkbox.Group
                  value={selectedDocumentIds}
                  onChange={handleDocumentSelectionChange}
                  className="w-full"
                >
                  <div className="space-y-2">
                    {documents.map(doc => (
                      <div key={doc.id} className="flex items-center">
                        <Checkbox value={doc.id} className="mr-2" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <FileTextOutlined className="text-gray-400" />
                            <span className="text-sm truncate">{doc.filename}</span>
                            {doc.knowledge_point_count && (
                              <Tag>
                                {doc.knowledge_point_count} 个知识点
                              </Tag>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Checkbox.Group>
              </div>
              <div className="mt-2 text-xs text-gray-500">
                已选择 {selectedDocumentIds.length} 个文档
              </div>
            </Form.Item>
          )}

          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={() => setCreateModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建学习集
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Learning Set Modal */}
      <Modal
        title="编辑学习集"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingLearningSet(null);
        }}
        footer={null}
        width={500}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditSubmit}
        >
          <Form.Item
            name="name"
            label="学习集名称"
            rules={[{ required: true, message: '请输入学习集名称' }]}
          >
            <Input placeholder="输入学习集名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              placeholder="输入学习集描述（可选）"
              rows={3}
            />
          </Form.Item>

          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={() => {
                setEditModalVisible(false);
                setEditingLearningSet(null);
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存更改
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}