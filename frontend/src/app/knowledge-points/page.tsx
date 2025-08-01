'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Row,
  Col,
  Typography,
  Space,
  Button,
  Modal,
  Select,
  Input,
  App,
} from 'antd';
import {
  BookOutlined,
  SearchOutlined,
  ImportOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, KnowledgeBase, Document } from '@/lib/api';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ResponsiveLayout } from '@/components/layout/ResponsiveLayout';
import KnowledgePointList from '@/components/knowledge-points/KnowledgePointList';
import KnowledgePointSearch from '@/components/knowledge-points/KnowledgePointSearch';


const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

const KnowledgePointsPage: React.FC = () => {
  const { message } = App.useApp();
  const { tokens } = useAuthStore();
  const token = tokens?.access_token;
  const [activeTab, setActiveTab] = useState('list');
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState<number | undefined>();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  
  // 搜索和提取相关状态
  const [searchQuery, setSearchQuery] = useState('');
  const [extractModalVisible, setExtractModalVisible] = useState(false);
  const [extractType, setExtractType] = useState<'document' | 'knowledge_base' | null>(null);
  const [extractKnowledgeBaseId, setExtractKnowledgeBaseId] = useState<number | undefined>();
  const [extractDocumentId, setExtractDocumentId] = useState<number | undefined>();
  const [extractDocuments, setExtractDocuments] = useState<Document[]>([]);
  const [targetCount, setTargetCount] = useState<number | undefined>();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadKnowledgeBases = async () => {
      if (!token) return;

      try {
        const response = await apiClient.getKnowledgeBases(token, 0, 100);
        setKnowledgeBases(response.knowledge_bases);
      } catch (error) {
        console.error('Failed to load knowledge bases:', error);
        message.error('加载知识库失败');
      }
    };

    loadKnowledgeBases();
  }, [token, message]);

  const handleKnowledgePointSelect = (kpId: number) => {
    // 直接跳转到详情页面
    window.open(`/knowledge-points/${kpId}`, '_blank');
  };

  const openExtractModal = (type: 'document' | 'knowledge_base') => {
    setExtractType(type);
    setExtractKnowledgeBaseId(undefined);
    setExtractDocumentId(undefined);
    setExtractDocuments([]);
    setTargetCount(undefined);
    setExtractModalVisible(true);
  };

  const handleExtractKnowledgeBaseChange = async (kbId: number) => {
    setExtractKnowledgeBaseId(kbId);
    setExtractDocumentId(undefined);
    
    if (extractType === 'document') {
      try {
        const response = await apiClient.getDocuments(token!, kbId, 0, 100);
        setExtractDocuments(response.documents);
      } catch (error) {
        console.error('Failed to load documents:', error);
        message.error('加载文档失败');
      }
    }
  };

  const handleExtractFromDocument = async (docId: number) => {
    if (!token) return;

    setLoading(true);
    try {
      const response = await apiClient.extractKnowledgePointsFromDocument(token, docId, targetCount);
      
      // Show detailed success message
      const successMessage = response.message || `成功提取 ${response.count} 个知识点`;
      message.success(successMessage, 4); // Show for 4 seconds
      
      // Show additional info if staged extraction was used
      if (response.extraction_stages && response.extraction_stages > 1) {
        message.info(`采用分阶段提取，共${response.extraction_stages}个阶段完成`, 3);
      }
      
      setExtractModalVisible(false);
      
      // Trigger refresh of the knowledge points list
      setRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error('Failed to extract knowledge points:', error);
      message.error('提取知识点失败，请检查文档内容或稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractFromKnowledgeBase = async (kbId: number) => {
    if (!token) return;

    setLoading(true);
    try {
      const response = await apiClient.extractKnowledgePointsFromKnowledgeBase(token, kbId, targetCount);
      
      // Show detailed success message
      let successMessage = `批量提取完成！成功处理 ${response.processed_documents} 个文档，提取 ${response.total_knowledge_points} 个知识点`;
      if (targetCount) {
        successMessage += `（每个文档目标：${targetCount}个）`;
      }
      message.success(successMessage, 5); // Show for 5 seconds
      
      // Show errors if any
      if (response.errors && response.errors.length > 0) {
        message.warning(`部分文档处理失败：${response.errors.length} 个错误`, 3);
      }
      
      setExtractModalVisible(false);
      
      // Trigger refresh of the knowledge points list
      setRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error('Failed to extract knowledge points:', error);
      message.error('批量提取知识点失败，请检查网络连接或稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmExtract = () => {
    if (extractType === 'document' && extractDocumentId) {
      handleExtractFromDocument(extractDocumentId);
    } else if (extractType === 'knowledge_base' && extractKnowledgeBaseId) {
      handleExtractFromKnowledgeBase(extractKnowledgeBaseId);
    } else {
      message.warning('请选择要提取的源');
    }
  };



  return (
    <ProtectedRoute>
      <ResponsiveLayout>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          {/* Header */}
          <div style={{ marginBottom: 24 }}>
            <Row justify="space-between" align="middle">
              <Col>
                <Title level={2} style={{ margin: 0 }}>
                  <BookOutlined style={{ marginRight: 8 }} />
                  知识点管理
                </Title>
                <Paragraph type="secondary" style={{ margin: '8px 0 0 0' }}>
                  管理和组织从文档中提取的知识点，支持自动提取、手动编辑和智能搜索
                </Paragraph>
              </Col>
              <Col>
                <Space>
                  <Select
                    placeholder="选择知识库"
                    value={selectedKnowledgeBaseId}
                    onChange={setSelectedKnowledgeBaseId}
                    allowClear
                    style={{ width: 200 }}
                  >
                    {knowledgeBases.map(kb => (
                      <Option key={kb.id} value={kb.id}>
                        {kb.name}
                      </Option>
                    ))}
                  </Select>
                </Space>
              </Col>
            </Row>
          </div>

          {/* Main Content */}
          <Card>
            <div style={{ marginBottom: 16 }}>
              <Row justify="space-between" align="middle">
                <Col>
                  <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    items={[
                      {
                        key: "list",
                        label: (
                          <span>
                            <BookOutlined />
                            知识点列表
                          </span>
                        )
                      },
                      {
                        key: "search",
                        label: (
                          <span>
                            <SearchOutlined />
                            智能搜索
                          </span>
                        )
                      }
                    ]}
                  />
                </Col>
                <Col>
                  <Space>
                    <Search
                      placeholder="搜索知识点标题或内容"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      style={{ width: 250 }}
                      enterButton={<SearchOutlined />}
                    />
                    <Button
                      type="default"
                      icon={<ImportOutlined />}
                      onClick={() => openExtractModal('document')}
                      loading={loading}
                    >
                      从文档提取
                    </Button>
                    <Button
                      type="default"
                      icon={<ImportOutlined />}
                      onClick={() => openExtractModal('knowledge_base')}
                      loading={loading}
                    >
                      从知识库批量提取
                    </Button>
                  </Space>
                </Col>
              </Row>
            </div>

            <div>
              {activeTab === 'list' && (
                <KnowledgePointList
                  showActions={true}
                  height={600}
                  refreshTrigger={refreshTrigger}
                  knowledgeBaseId={selectedKnowledgeBaseId}
                />
              )}
              {activeTab === 'search' && (
                <Row gutter={24}>
                  <Col span={24}>
                    <KnowledgePointSearch
                      onKnowledgePointSelect={handleKnowledgePointSelect}
                    />
                  </Col>
                </Row>
              )}

            </div>
          </Card>





            {/* Extract Modal */}
            <Modal
              title={extractType === 'document' ? '从文档提取知识点' : '从知识库批量提取知识点'}
              open={extractModalVisible}
              onCancel={() => setExtractModalVisible(false)}
              onOk={handleConfirmExtract}
              confirmLoading={loading}
              okText="开始提取"
              cancelText="取消"
              width={600}
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text strong>选择知识库：</Text>
                  <Select
                    placeholder="请选择知识库"
                    value={extractKnowledgeBaseId}
                    onChange={handleExtractKnowledgeBaseChange}
                    style={{ width: '100%', marginTop: 8 }}
                  >
                    {knowledgeBases.map(kb => (
                      <Option key={kb.id} value={kb.id}>
                        {kb.name}
                      </Option>
                    ))}
                  </Select>
                </div>

                {extractType === 'document' && (
                  <div>
                    <Text strong>选择文档：</Text>
                    <Select
                      placeholder="请选择文档"
                      value={extractDocumentId}
                      onChange={setExtractDocumentId}
                      disabled={!extractKnowledgeBaseId}
                      style={{ width: '100%', marginTop: 8 }}
                    >
                      {extractDocuments.map(doc => (
                        <Option key={doc.id} value={doc.id}>
                          {doc.filename}
                        </Option>
                      ))}
                    </Select>
                  </div>
                )}

                <div>
                  <Text strong>
                    {extractType === 'document' ? '目标知识点数量：' : '每个文档的目标知识点数量：'}
                  </Text>
                  <Input
                    type="number"
                    placeholder={extractType === 'document' ? '留空使用默认数量(3-8个)' : '留空使用默认数量(3-8个)'}
                    value={targetCount}
                    onChange={(e) => {
                      const value = e.target.value;
                      setTargetCount(value ? parseInt(value) : undefined);
                    }}
                    min={1}
                    max={100}
                    style={{ width: '100%', marginTop: 8 }}
                  />
                  <Text type="secondary" style={{ fontSize: '12px', marginTop: 4, display: 'block' }}>
                    {targetCount && targetCount > 15 
                      ? `大于15个知识点将分阶段提取，预计需要${Math.ceil(targetCount / 15)}个阶段`
                      : '建议范围：1-100个知识点'
                    }
                  </Text>
                </div>



                <div style={{ padding: '16px', backgroundColor: '#f6f8fa', borderRadius: '6px' }}>
                  <Text type="secondary">
                    {extractType === 'document' 
                      ? '将从选定的文档中增量提取知识点，新提取的知识点会添加到现有知识点中，不会删除已有内容。'
                      : '将从选定知识库中的所有文档增量提取知识点，新提取的知识点会添加到现有知识点中，不会删除已有内容。'
                    }
                  </Text>
                </div>
              </Space>
            </Modal>
        </div>
      </ResponsiveLayout>
    </ProtectedRoute>
  );
};

export default KnowledgePointsPage;