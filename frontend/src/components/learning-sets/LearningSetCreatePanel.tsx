'use client';

import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  Checkbox,
  Button,
  Space,
  Typography,
  List,
  Tag,
  Empty,
  App
} from 'antd';
import {
  FileTextOutlined,
  FilePdfOutlined,
  FileMarkdownOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, Document, KnowledgeBase, LearningSetCreate } from '@/lib/api';
import { useRouter } from 'next/navigation';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface LearningSetCreatePanelProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  knowledgeBase: KnowledgeBase;
  documents: Document[];
}

export function LearningSetCreatePanel({
  visible,
  onCancel,
  onSuccess,
  knowledgeBase,
  documents
}: LearningSetCreatePanelProps) {
  const { tokens } = useAuth();
  const { message } = App.useApp();
  const router = useRouter();
  const [form] = Form.useForm();
  const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  // 只显示已处理的文档
  const processedDocuments = documents.filter(doc => doc.processed);

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'pdf':
        return <FilePdfOutlined className="text-red-500" />;
      case 'md':
        return <FileMarkdownOutlined className="text-blue-500" />;
      case 'txt':
        return <FileTextOutlined className="text-gray-500" />;
      case 'epub':
        return <FileTextOutlined className="text-green-500" />;
      default:
        return <FileTextOutlined className="text-gray-500" />;
    }
  };

  const handleDocumentSelect = (documentId: number, checked: boolean) => {
    if (checked) {
      setSelectedDocuments(prev => [...prev, documentId]);
    } else {
      setSelectedDocuments(prev => prev.filter(id => id !== documentId));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedDocuments(processedDocuments.map(doc => doc.id));
    } else {
      setSelectedDocuments([]);
    }
  };

  const handleSubmit = async (values: { name: string; description?: string }) => {
    if (!tokens?.access_token) {
      message.error('未找到认证令牌，请重新登录');
      return;
    }

    if (selectedDocuments.length === 0) {
      message.error('请至少选择一个文档');
      return;
    }

    setLoading(true);
    try {
      const createData: LearningSetCreate = {
        name: values.name.trim(),
        description: values.description?.trim(),
        knowledge_base_id: knowledgeBase.id,
        document_ids: selectedDocuments
      };

      await apiClient.createLearningSet(tokens.access_token, createData);
      message.success('学习集创建成功');
      form.resetFields();
      setSelectedDocuments([]);
      onSuccess();
      
      // 跳转到学习集管理页面
      router.push('/questions');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      message.error(`创建学习集失败: ${errorMessage}`);
      console.error('Error creating learning set:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setSelectedDocuments([]);
    onCancel();
  };

  return (
    <Modal
      title="创建学习集"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={800}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
      >
        <Form.Item
          name="name"
          label="学习集名称"
          rules={[
            { required: true, message: '请输入学习集名称' },
            { max: 200, message: '名称不能超过200个字符' },
          ]}
        >
          <Input placeholder="请输入学习集名称" />
        </Form.Item>

        <Form.Item
          name="description"
          label="描述"
          rules={[{ max: 500, message: '描述不能超过500个字符' }]}
        >
          <TextArea
            rows={3}
            placeholder="请输入学习集描述（可选）"
          />
        </Form.Item>

        <Form.Item label="选择文档">
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <Text strong>从 {knowledgeBase.name} 中选择文档：</Text>
              <Checkbox
                checked={selectedDocuments.length === processedDocuments.length && processedDocuments.length > 0}
                indeterminate={selectedDocuments.length > 0 && selectedDocuments.length < processedDocuments.length}
                onChange={(e) => handleSelectAll(e.target.checked)}
              >
                全选
              </Checkbox>
            </div>
            
            {processedDocuments.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无已处理的文档"
              />
            ) : (
              <div className="border rounded-lg max-h-60 overflow-y-auto">
                <List
                  dataSource={processedDocuments}
                  renderItem={(doc) => (
                    <List.Item className="px-4">
                      <List.Item.Meta
                        avatar={
                          <Checkbox
                            checked={selectedDocuments.includes(doc.id)}
                            onChange={(e) => handleDocumentSelect(doc.id, e.target.checked)}
                          />
                        }
                        title={
                          <div className="flex items-center space-x-2">
                            {getFileIcon(doc.file_type)}
                            <span>{doc.filename}</span>
                            <Tag icon={<CheckCircleOutlined />} color="success">
                              已处理
                            </Tag>
                          </div>
                        }
                        description={
                          <Space size="middle">
                            <Text type="secondary" className="text-sm">
                              类型: {doc.file_type.toUpperCase()}
                            </Text>
                            <Text type="secondary" className="text-sm">
                              知识点: {doc.knowledge_point_count || 0} 个
                            </Text>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              </div>
            )}
            
            {selectedDocuments.length > 0 && (
              <div className="mt-2">
                <Text type="secondary">
                  已选择 {selectedDocuments.length} 个文档
                </Text>
              </div>
            )}
          </div>
        </Form.Item>

        <Form.Item className="mb-0">
          <Space className="w-full justify-end">
            <Button onClick={handleCancel}>
              取消
            </Button>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              disabled={selectedDocuments.length === 0}
            >
              创建学习集
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}