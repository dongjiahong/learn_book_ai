'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Card,
  Typography,
  Space,
  Button,
  Tag,
  Spin,
  Row,
  Col,
  Divider,
  Breadcrumb,
  Modal,
  App,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  BookOutlined,
  CalendarOutlined,
  StarOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, KnowledgePoint, Document } from '@/lib/api';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ResponsiveLayout } from '@/components/layout/ResponsiveLayout';
import KnowledgePointForm from '@/components/knowledge-points/KnowledgePointForm';
import ReactMarkdown from 'react-markdown';

const { Title, Text, Paragraph } = Typography;

const KnowledgePointDetailPage: React.FC = () => {
  const { message } = App.useApp();
  const params = useParams();
  const router = useRouter();
  const { tokens } = useAuthStore();
  const token = tokens?.access_token;
  
  const [knowledgePoint, setKnowledgePoint] = useState<KnowledgePoint | null>(null);
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);

  const knowledgePointId = params?.id as string;

  const loadKnowledgePointDetail = useCallback(async () => {
    if (!token || !knowledgePointId) return;

    setLoading(true);
    try {
      // 获取知识点详情
      const kpResponse = await apiClient.getKnowledgePoint(token, parseInt(knowledgePointId));
      const kpData = kpResponse.knowledge_point;
      setKnowledgePoint(kpData);

      // 获取关联文档信息
      if (kpData.document_id) {
        try {
          const docResponse = await apiClient.getDocument(token, kpData.document_id);
          setDocument(docResponse.document);
        } catch (error) {
          console.error('Failed to load document:', error);
        }
      }
    } catch (error) {
      console.error('Failed to load knowledge point:', error);
      message.error('加载知识点详情失败');
      router.push('/knowledge-points');
    } finally {
      setLoading(false);
    }
  }, [token, knowledgePointId, message, router]);

  useEffect(() => {
    if (knowledgePointId && token) {
      loadKnowledgePointDetail();
    }
  }, [knowledgePointId, token, loadKnowledgePointDetail]);

  const handleDelete = async () => {
    if (!token || !knowledgePointId) return;

    try {
      await apiClient.deleteKnowledgePoint(token, parseInt(knowledgePointId));
      message.success('知识点删除成功');
      router.push('/knowledge-points');
    } catch (error) {
      console.error('Failed to delete knowledge point:', error);
      message.error('删除知识点失败');
    }
  };

  const getImportanceColor = (level: number) => {
    const colors = ['default', 'blue', 'green', 'orange', 'red'];
    return colors[level - 1] || 'default';
  };

  const getImportanceText = (level: number) => {
    const texts = ['一般', '较低', '中等', '重要', '非常重要'];
    return texts[level - 1] || '未知';
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <ResponsiveLayout>
          <div style={{ textAlign: 'center', padding: '100px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">加载知识点详情中...</Text>
            </div>
          </div>
        </ResponsiveLayout>
      </ProtectedRoute>
    );
  }

  if (!knowledgePoint) {
    return (
      <ProtectedRoute>
        <ResponsiveLayout>
          <div style={{ textAlign: 'center', padding: '100px 0' }}>
            <Text type="secondary">知识点不存在</Text>
          </div>
        </ResponsiveLayout>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <ResponsiveLayout>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {/* 面包屑导航 */}
          <Breadcrumb style={{ marginBottom: 24 }}>
            <Breadcrumb.Item>
              <Button 
                type="link" 
                icon={<BookOutlined />}
                onClick={() => router.push('/knowledge-points')}
                style={{ padding: 0 }}
              >
                知识点管理
              </Button>
            </Breadcrumb.Item>
            <Breadcrumb.Item>知识点详情</Breadcrumb.Item>
          </Breadcrumb>

          {/* 头部操作区 */}
          <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
            <Col>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => router.back()}
              >
                返回
              </Button>
            </Col>
            <Col>
              <Space>
                <Button
                  type="primary"
                  icon={<EditOutlined />}
                  onClick={() => setEditModalVisible(true)}
                >
                  编辑
                </Button>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => setDeleteModalVisible(true)}
                >
                  删除
                </Button>
              </Space>
            </Col>
          </Row>

          {/* 主要内容 */}
          <Row gutter={24}>
            <Col span={18}>
              {/* 知识点内容卡片 */}
              <Card>
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  {/* 标题和重要性 */}
                  <div>
                    <Title level={2} style={{ marginBottom: 8 }}>
                      {knowledgePoint.title}
                    </Title>
                    <Space>
                      <Tag 
                        color={getImportanceColor(knowledgePoint.importance_level)}
                        icon={<StarOutlined />}
                      >
                        {getImportanceText(knowledgePoint.importance_level)}
                      </Tag>
                      <Text type="secondary">
                        <CalendarOutlined style={{ marginRight: 4 }} />
                        创建于 {new Date(knowledgePoint.created_at).toLocaleString('zh-CN')}
                      </Text>
                    </Space>
                  </div>

                  <Divider />

                  {/* 知识点内容 */}
                  <div>
                    <Title level={4} style={{ marginBottom: 16 }}>
                      内容详情
                    </Title>
                    <Card 
                      style={{ 
                        backgroundColor: '#fafafa',
                        border: '1px solid #f0f0f0'
                      }}
                    >
                      <div style={{ 
                        lineHeight: '1.8',
                        fontSize: '14px',
                        color: '#262626',
                        whiteSpace: 'pre-wrap'
                      }}>
                        <ReactMarkdown>
                          {knowledgePoint.content}
                        </ReactMarkdown>
                      </div>
                    </Card>
                  </div>
                </Space>
              </Card>
            </Col>

            <Col span={6}>
              {/* 侧边栏信息 */}
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {/* 来源文档信息 */}
                {document && (
                  <Card title="来源文档" size="small">
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <div>
                        <Text strong>
                          <FileTextOutlined style={{ marginRight: 4 }} />
                          文档名称
                        </Text>
                        <div style={{ marginTop: 4 }}>
                          <Text>{document.filename}</Text>
                        </div>
                      </div>
                      
                      <div>
                        <Text strong>文件类型</Text>
                        <div style={{ marginTop: 4 }}>
                          <Tag>{document.file_type.toUpperCase()}</Tag>
                        </div>
                      </div>
                      
                      <div>
                        <Text strong>文件大小</Text>
                        <div style={{ marginTop: 4 }}>
                          <Text type="secondary">
                            {(document.file_size / 1024).toFixed(1)} KB
                          </Text>
                        </div>
                      </div>
                      
                      <div>
                        <Text strong>上传时间</Text>
                        <div style={{ marginTop: 4 }}>
                          <Text type="secondary">
                            {new Date(document.created_at).toLocaleString('zh-CN')}
                          </Text>
                        </div>
                      </div>
                    </Space>
                  </Card>
                )}

                {/* 知识点统计信息 */}
                <Card title="统计信息" size="small">
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <div>
                      <Text strong>知识点ID</Text>
                      <div style={{ marginTop: 4 }}>
                        <Text type="secondary">#{knowledgePoint.id}</Text>
                      </div>
                    </div>
                    
                    <div>
                      <Text strong>重要性级别</Text>
                      <div style={{ marginTop: 4 }}>
                        <Tag color={getImportanceColor(knowledgePoint.importance_level)}>
                          级别 {knowledgePoint.importance_level}
                        </Tag>
                      </div>
                    </div>
                    
                    <div>
                      <Text strong>内容长度</Text>
                      <div style={{ marginTop: 4 }}>
                        <Text type="secondary">
                          {knowledgePoint.content.length} 字符
                        </Text>
                      </div>
                    </div>
                  </Space>
                </Card>
              </Space>
            </Col>
          </Row>

          {/* 编辑模态框 */}
          {knowledgePoint && (
            <KnowledgePointForm
              visible={editModalVisible}
              onCancel={() => setEditModalVisible(false)}
              onSuccess={() => {
                setEditModalVisible(false);
                loadKnowledgePointDetail();
                message.success('知识点更新成功');
              }}
              knowledgePoint={knowledgePoint}
            />
          )}

          {/* 删除确认模态框 */}
          <Modal
            title="确认删除"
            open={deleteModalVisible}
            onOk={handleDelete}
            onCancel={() => setDeleteModalVisible(false)}
            okText="确认删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <p>确定要删除这个知识点吗？此操作不可撤销。</p>
            <p><strong>标题：</strong>{knowledgePoint.title}</p>
          </Modal>
        </div>
      </ResponsiveLayout>
    </ProtectedRoute>
  );
};

export default KnowledgePointDetailPage;