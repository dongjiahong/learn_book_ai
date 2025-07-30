'use client';

import React, { useState } from 'react';
import {
  Card,
  Tabs,
  Row,
  Col,
  Typography,
  Space,
  Button,
  Modal,
} from 'antd';
import {
  BookOutlined,
  SearchOutlined,
  BarChartOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ResponsiveLayout } from '@/components/layout/ResponsiveLayout';
import KnowledgePointList from '@/components/knowledge-points/KnowledgePointList';
import KnowledgePointSearch from '@/components/knowledge-points/KnowledgePointSearch';
import KnowledgePointForm from '@/components/knowledge-points/KnowledgePointForm';

const { Title, Paragraph } = Typography;

const KnowledgePointsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('list');
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [selectedKnowledgePointId, setSelectedKnowledgePointId] = useState<number | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  const handleKnowledgePointSelect = (kpId: number) => {
    setSelectedKnowledgePointId(kpId);
    setDetailModalVisible(true);
  };

  const handleCreateSuccess = () => {
    // Refresh the list by switching tabs or triggering a refresh
    setActiveTab('list');
  };

  return (
    <ProtectedRoute>
      <ResponsiveLayout>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          {/* Header */}
          <div style={{ marginBottom: 24 }}>
            <Title level={2}>
              <BookOutlined style={{ marginRight: 8 }} />
              知识点管理
            </Title>
            <Paragraph type="secondary">
              管理和组织从文档中提取的知识点，支持自动提取、手动编辑和智能搜索
            </Paragraph>
          </div>

          {/* Main Content */}
          <Card>
              <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                tabBarExtraContent={
                  <Space>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => setCreateModalVisible(true)}
                    >
                      新建知识点
                    </Button>
                  </Space>
                }
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

            {/* Create Knowledge Point Modal */}
            <KnowledgePointForm
              visible={createModalVisible}
              onCancel={() => setCreateModalVisible(false)}
              onSuccess={handleCreateSuccess}
              mode="create"
            />

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