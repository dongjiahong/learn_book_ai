'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Button,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Typography,
  Space,
  Tag,
  Empty
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  FolderOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate } from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface KnowledgeBaseListProps {
  onSelectKnowledgeBase?: (kb: KnowledgeBase) => void;
}

export function KnowledgeBaseList({ onSelectKnowledgeBase }: KnowledgeBaseListProps) {
  const { tokens } = useAuth();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null);
  const [form] = Form.useForm();

  const fetchKnowledgeBases = async () => {
    if (!tokens?.access_token) return;

    setLoading(true);
    try {
      const response = await apiClient.getKnowledgeBases(tokens.access_token);
      setKnowledgeBases(response.knowledge_bases);
    } catch (error) {
      message.error('获取知识库列表失败');
      console.error('Error fetching knowledge bases:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKnowledgeBases();
  }, [tokens]);

  const handleCreate = () => {
    setEditingKb(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (kb: KnowledgeBase) => {
    setEditingKb(kb);
    form.setFieldsValue({
      name: kb.name,
      description: kb.description,
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values: KnowledgeBaseCreate) => {
    if (!tokens?.access_token) return;

    try {
      if (editingKb) {
        // Update existing knowledge base
        await apiClient.updateKnowledgeBase(tokens.access_token, editingKb.id, values);
        message.success('知识库更新成功');
      } else {
        // Create new knowledge base
        await apiClient.createKnowledgeBase(tokens.access_token, values);
        message.success('知识库创建成功');
      }
      
      setModalVisible(false);
      form.resetFields();
      fetchKnowledgeBases();
    } catch (error) {
      message.error(editingKb ? '更新知识库失败' : '创建知识库失败');
      console.error('Error saving knowledge base:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!tokens?.access_token) return;

    try {
      await apiClient.deleteKnowledgeBase(tokens.access_token, id);
      message.success('知识库删除成功');
      fetchKnowledgeBases();
    } catch (error) {
      message.error('删除知识库失败');
      console.error('Error deleting knowledge base:', error);
    }
  };

  const handleCancel = () => {
    setModalVisible(false);
    form.resetFields();
    setEditingKb(null);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <Title level={3}>知识库管理</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          创建知识库
        </Button>
      </div>

      {knowledgeBases.length === 0 && !loading ? (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无知识库"
          >
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              创建第一个知识库
            </Button>
          </Empty>
        </Card>
      ) : (
        <List
          loading={loading}
          grid={{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 3, xl: 3, xxl: 4 }}
          dataSource={knowledgeBases}
          renderItem={(kb) => (
            <List.Item>
              <Card
                hoverable
                actions={[
                  <EditOutlined key="edit" onClick={() => handleEdit(kb)} />,
                  <Popconfirm
                    key="delete"
                    title="确定要删除这个知识库吗？"
                    description="删除后将无法恢复，包括其中的所有文档。"
                    onConfirm={() => handleDelete(kb.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <DeleteOutlined />
                  </Popconfirm>,
                ]}
                onClick={() => onSelectKnowledgeBase?.(kb)}
              >
                <Card.Meta
                  avatar={<FolderOutlined className="text-2xl text-blue-500" />}
                  title={
                    <div className="flex justify-between items-center">
                      <span className="truncate">{kb.name}</span>
                    </div>
                  }
                  description={
                    <div>
                      <Text type="secondary" className="text-sm">
                        {kb.description || '暂无描述'}
                      </Text>
                      <div className="mt-2 flex justify-between items-center">
                        <Tag icon={<FileTextOutlined />} color="blue">
                          {kb.document_count || 0} 个文档
                        </Tag>
                        <Text type="secondary" className="text-xs">
                          {new Date(kb.created_at).toLocaleDateString()}
                        </Text>
                      </div>
                    </div>
                  }
                />
              </Card>
            </List.Item>
          )}
        />
      )}

      <Modal
        title={editingKb ? '编辑知识库' : '创建知识库'}
        open={modalVisible}
        onCancel={handleCancel}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          autoComplete="off"
        >
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[
              { required: true, message: '请输入知识库名称' },
              { max: 100, message: '名称不能超过100个字符' },
            ]}
          >
            <Input placeholder="请输入知识库名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ max: 500, message: '描述不能超过500个字符' }]}
          >
            <TextArea
              rows={4}
              placeholder="请输入知识库描述（可选）"
            />
          </Form.Item>

          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={handleCancel}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingKb ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}