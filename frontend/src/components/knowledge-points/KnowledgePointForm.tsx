'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  Button,
  message,
  Space,
  Typography,
  Card,
  Row,
  Col,
} from 'antd';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, KnowledgePoint, Document, KnowledgeBase } from '@/lib/api';

const { TextArea } = Input;
const { Option } = Select;
const { Title, Text } = Typography;

interface KnowledgePointFormProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  knowledgePoint: KnowledgePoint;
}

interface FormValues {
  document_id: number;
  title: string;
  question: string;
  content: string;
  importance_level: number;
}

const KnowledgePointForm: React.FC<KnowledgePointFormProps> = ({
  visible,
  onCancel,
  onSuccess,
  knowledgePoint,
}) => {
  const { tokens } = useAuthStore();
  const token = tokens?.access_token;
  const [form] = Form.useForm<FormValues>();
  const [loading, setLoading] = useState(false);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState<number | undefined>();

  const loadKnowledgeBases = useCallback(async () => {
    if (!token) return;

    try {
      const response = await apiClient.getKnowledgeBases(token, 0, 100);
      setKnowledgeBases(response.knowledge_bases);
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
      message.error('加载知识库失败');
    }
  }, [token]);

  const loadDocuments = useCallback(async (kbId: number) => {
    if (!token) return;

    try {
      const response = await apiClient.getDocuments(token, kbId, 0, 100);
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to load documents:', error);
      message.error('加载文档失败');
    }
  }, [token]);

  const loadDocumentInfo = useCallback(async (docId: number) => {
    if (!token) return;

    try {
      const document = await apiClient.getDocument(token, docId);
      const kbResponse = await apiClient.getKnowledgeBase(token, document.knowledge_base_id);
      
      setSelectedKnowledgeBaseId(document.knowledge_base_id);
      setKnowledgeBases(prev => {
        const exists = prev.find(kb => kb.id === document.knowledge_base_id);
        if (!exists) {
          return [...prev, kbResponse];
        }
        return prev;
      });
      
      await loadDocuments(document.knowledge_base_id);
    } catch (error) {
      console.error('Failed to load document info:', error);
    }
  }, [token, loadDocuments]);

  useEffect(() => {
    if (visible && knowledgePoint) {
      loadKnowledgeBases();
      form.setFieldsValue({
        document_id: knowledgePoint.document_id,
        title: knowledgePoint.title,
        question: knowledgePoint.question || '',
        content: knowledgePoint.content,
        importance_level: knowledgePoint.importance_level,
      });
      // Load documents for the knowledge point's document
      loadDocumentInfo(knowledgePoint.document_id);
    }
  }, [visible, knowledgePoint, form, loadKnowledgeBases, loadDocuments, loadDocumentInfo]);

  const handleKnowledgeBaseChange = (kbId: number) => {
    setSelectedKnowledgeBaseId(kbId);
    setDocuments([]);
    form.setFieldValue('document_id', undefined);
    loadDocuments(kbId);
  };

  const handleSubmit = async (values: FormValues) => {
    if (!token || !knowledgePoint) return;

    setLoading(true);
    try {
      const updateData = {
        title: values.title,
        content: values.content,
        importance_level: values.importance_level,
      };
      await apiClient.updateKnowledgePoint(token, knowledgePoint.id, updateData);
      message.success('知识点更新成功');
      
      form.resetFields();
      onSuccess();
      onCancel();
    } catch (error) {
      console.error('Failed to update knowledge point:', error);
      message.error('更新知识点失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };



  return (
    <Modal
      title="编辑知识点"
      open={visible}
      onCancel={handleCancel}
      width={800}
      footer={null}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          importance_level: 3,
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="知识库"
            >
              <Select
                placeholder="选择知识库"
                value={selectedKnowledgeBaseId}
                onChange={handleKnowledgeBaseChange}
                disabled={true}
              >
                {knowledgeBases.map(kb => (
                  <Option key={kb.id} value={kb.id}>
                    {kb.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="文档"
              name="document_id"
              rules={[{ required: true, message: '请选择文档' }]}
            >
              <Select
                placeholder="选择文档"
                disabled={true}
              >
                {documents.map(doc => (
                  <Option key={doc.id} value={doc.id}>
                    {doc.filename}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          label="知识点标题"
          name="title"
          rules={[
            { required: true, message: '请输入知识点标题' },
            { max: 200, message: '标题长度不能超过200个字符' },
          ]}
        >
          <Input
            placeholder="请输入简洁明确的知识点标题"
            showCount
            maxLength={200}
          />
        </Form.Item>

        <Form.Item
          label="知识点内容"
          name="content"
          rules={[
            { required: true, message: '请输入知识点内容' },
            { min: 10, message: '内容至少需要10个字符' },
          ]}
        >
          <TextArea
            placeholder="请输入详细的知识点内容，支持换行"
            rows={8}
            showCount
            maxLength={2000}
          />
        </Form.Item>

        <Form.Item
          label="重要性级别"
          name="importance_level"
          rules={[{ required: true, message: '请选择重要性级别' }]}
        >
          <Select placeholder="选择重要性级别">
            <Option value={1}>
              <Space>
                <span>1 - 一般</span>
                <Text type="secondary">（基础概念）</Text>
              </Space>
            </Option>
            <Option value={2}>
              <Space>
                <span>2 - 较低</span>
                <Text type="secondary">（辅助信息）</Text>
              </Space>
            </Option>
            <Option value={3}>
              <Space>
                <span>3 - 中等</span>
                <Text type="secondary">（常规知识点）</Text>
              </Space>
            </Option>
            <Option value={4}>
              <Space>
                <span>4 - 重要</span>
                <Text type="secondary">（核心概念）</Text>
              </Space>
            </Option>
            <Option value={5}>
              <Space>
                <span>5 - 非常重要</span>
                <Text type="secondary">（关键知识点）</Text>
              </Space>
            </Option>
          </Select>
        </Form.Item>

        <Form.Item>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={handleCancel}>
              取消
            </Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              更新
            </Button>
          </Space>
        </Form.Item>
      </Form>

      {/* Help Information */}
      <Card size="small" style={{ marginTop: 16, backgroundColor: '#f6f8fa' }}>
        <Title level={5}>编辑提示</Title>
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          <li>标题应该简洁明确，概括知识点的核心内容</li>
          <li>内容应该详细完整，包含必要的解释和说明</li>
          <li>重要性级别用于学习优先级排序和复习安排</li>
          <li>知识点来源文档不可修改，如需更改请重新从文档提取</li>
        </ul>
      </Card>
    </Modal>
  );
};

export default KnowledgePointForm;