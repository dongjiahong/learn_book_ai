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
  message,
} from 'antd';
import {
  BookOutlined,
  SearchOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, KnowledgeBase } from '@/lib/api';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ResponsiveLayout } from '@/components/layout/ResponsiveLayout';
import KnowledgePointList from '@/components/knowledge-points/KnowledgePointList';
import KnowledgePointSearch from '@/components/knowledge-points/KnowledgePointSearch';


const { Title, Paragraph } = Typography;
const { Option } = Select;

const KnowledgePointsPage: React.FC = () => {
  const { tokens } = useAuthStore();
  const token = tokens?.access_token;
  const [activeTab, setActiveTab] = useState('list');
  const [selectedKnowledgePointId, setSelectedKnowledgePointId] = useState<number | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState<number | undefined>();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);

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
  }, [token]);

  const handleKnowledgePointSelect = (kpId: number) => {
    setSelectedKnowledgePointId(kpId);
    setDetailModalVisible(true);
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
                    ),
                    children: (
                      <KnowledgePointList
                        showFilters={true}
                        showActions={true}
                        height={600}
                      />
                    )
                  },
                  {
                    key: "search",
                    label: (
                      <span>
                        <SearchOutlined />
                        智能搜索
                      </span>
                    ),
                    children: (
                      <Row gutter={24}>
                        <Col span={24}>
                          <KnowledgePointSearch
                            onKnowledgePointSelect={handleKnowledgePointSelect}
                          />
                        </Col>
                      </Row>
                    )
                  },
                  {
                    key: "statistics",
                    label: (
                      <span>
                        <BarChartOutlined />
                        统计分析
                      </span>
                    ),
                    children: (
                      <Row gutter={24}>
                        <Col span={24}>
                          <Card title="知识点统计" loading={false}>
                            <Paragraph>
                              统计分析功能正在开发中，将提供知识点分布、重要性分析、学习进度等统计信息。
                            </Paragraph>
                          </Card>
                        </Col>
                      </Row>
                    )
                  }
                ]}
              />
            </Card>



            {/* Knowledge Point Detail Modal */}
            <Modal
              title="知识点详情"
              open={detailModalVisible}
              onCancel={() => setDetailModalVisible(false)}
              footer={[
                <Button key="close" onClick={() => setDetailModalVisible(false)}>
                  关闭
                </Button>,
              ]}
              width={800}
            >
              {selectedKnowledgePointId && (
                <div>
                  <Paragraph>
                    知识点详情功能正在完善中，将显示完整的知识点信息、相关文档、学习记录等。
                  </Paragraph>
                  <Paragraph type="secondary">
                    知识点ID: {selectedKnowledgePointId}
                  </Paragraph>
                </div>
              )}
            </Modal>
        </div>
      </ResponsiveLayout>
    </ProtectedRoute>
  );
};

export default KnowledgePointsPage;