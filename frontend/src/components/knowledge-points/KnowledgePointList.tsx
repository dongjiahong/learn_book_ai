'use client';

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  message,
  Input,
  Select,
  Card,
  Typography,
  Tooltip,
  Popconfirm,
  Badge,
  Row,
  Col,
  Statistic,
  Spin,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  ExportOutlined,
  ImportOutlined,
  FilterOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, KnowledgePoint, KnowledgeBase, Document } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;

interface KnowledgePointListProps {
  knowledgeBaseId?: number;
  documentId?: number;
  showFilters?: boolean;
  showActions?: boolean;
  height?: number;
}

interface FilterState {
  searchQuery: string;
  importanceLevel: number | undefined;
  knowledgeBaseId: number | undefined;
  documentId: number | undefined;
}

const KnowledgePointList: React.FC<KnowledgePointListProps> = ({
  knowledgeBaseId,
  documentId,
  showFilters = true,
  showActions = true,
  height,
}) => {
  const { token } = useAuthStore();
  const [knowledgePoints, setKnowledgePoints] = useState<KnowledgePoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [statistics, setStatistics] = useState<any>(null);
  
  const [filters, setFilters] = useState<FilterState>({
    searchQuery: '',
    importanceLevel: undefined,
    knowledgeBaseId: knowledgeBaseId,
    documentId: documentId,
  });

  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });

  // Modal states
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedKnowledgePoint, setSelectedKnowledgePoint] = useState<KnowledgePoint | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);

  useEffect(() => {
    loadKnowledgePoints();
    loadKnowledgeBases();
    loadStatistics();
  }, [filters, pagination.current, pagination.pageSize]);

  useEffect(() => {
    if (filters.knowledgeBaseId) {
      loadDocuments(filters.knowledgeBaseId);
    }
  }, [filters.knowledgeBaseId]);

  const loadKnowledgePoints = async () => {
    if (!token) return;

    setLoading(true);
    try {
      const response = await apiClient.getKnowledgePoints(token, {
        document_id: filters.documentId,
        knowledge_base_id: filters.knowledgeBaseId,
        importance_level: filters.importanceLevel,
        search_query: filters.searchQuery || undefined,
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      });

      setKnowledgePoints(response.knowledge_points);
      setPagination(prev => ({
        ...prev,
        total: response.count,
      }));
    } catch (error) {
      console.error('Failed to load knowledge points:', error);
      message.error('加载知识点失败');
    } finally {
      setLoading(false);
    }
  };

  const loadKnowledgeBases = async () => {
    if (!token) return;

    try {
      const response = await apiClient.getKnowledgeBases(token, 0, 100);
      setKnowledgeBases(response.knowledge_bases);
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
    }
  };

  const loadDocuments = async (kbId: number) => {
    if (!token) return;

    try {
      const response = await apiClient.getDocuments(token, kbId, 0, 100);
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const loadStatistics = async () => {
    if (!token) return;

    try {
      const response = await apiClient.getKnowledgePointStatistics(
        token,
        filters.knowledgeBaseId
      );
      setStatistics(response.statistics);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!token) return;

    try {
      await apiClient.deleteKnowledgePoint(token, id);
      message.success('知识点删除成功');
      loadKnowledgePoints();
      loadStatistics();
    } catch (error) {
      console.error('Failed to delete knowledge point:', error);
      message.error('删除知识点失败');
    }
  };

  const handleBatchDelete = async () => {
    if (!token || selectedRowKeys.length === 0) return;

    try {
      await apiClient.batchDeleteKnowledgePoints(token, selectedRowKeys as number[]);
      message.success(`成功删除 ${selectedRowKeys.length} 个知识点`);
      setSelectedRowKeys([]);
      loadKnowledgePoints();
      loadStatistics();
    } catch (error) {
      console.error('Failed to batch delete knowledge points:', error);
      message.error('批量删除失败');
    }
  };

  const handleExtractFromDocument = async (docId: number) => {
    if (!token) return;

    setLoading(true);
    try {
      const response = await apiClient.extractKnowledgePointsFromDocument(token, docId, false);
      message.success(`成功提取 ${response.count} 个知识点`);
      loadKnowledgePoints();
      loadStatistics();
    } catch (error) {
      console.error('Failed to extract knowledge points:', error);
      message.error('提取知识点失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractFromKnowledgeBase = async (kbId: number) => {
    if (!token) return;

    setLoading(true);
    try {
      const response = await apiClient.extractKnowledgePointsFromKnowledgeBase(token, kbId, false);
      message.success(`成功处理 ${response.processed_documents} 个文档，提取 ${response.total_knowledge_points} 个知识点`);
      loadKnowledgePoints();
      loadStatistics();
    } catch (error) {
      console.error('Failed to extract knowledge points:', error);
      message.error('批量提取知识点失败');
    } finally {
      setLoading(false);
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

  const columns: ColumnsType<KnowledgePoint> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      ellipsis: true,
      render: (text: string, record: KnowledgePoint) => (
        <Button
          type="link"
          onClick={() => {
            setSelectedKnowledgePoint(record);
            setDetailModalVisible(true);
          }}
          style={{ padding: 0, height: 'auto', textAlign: 'left' }}
        >
          <Text strong>{text}</Text>
        </Button>
      ),
    },
    {
      title: '内容预览',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text: string) => (
        <Text type="secondary">
          {text.length > 100 ? `${text.substring(0, 100)}...` : text}
        </Text>
      ),
    },
    {
      title: '重要性',
      dataIndex: 'importance_level',
      key: 'importance_level',
      width: 100,
      render: (level: number) => (
        <Tag color={getImportanceColor(level)}>
          {getImportanceText(level)}
        </Tag>
      ),
      sorter: (a, b) => a.importance_level - b.importance_level,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => new Date(date).toLocaleDateString('zh-CN'),
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
  ];

  if (showActions) {
    columns.push({
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record: KnowledgePoint) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedKnowledgePoint(record);
                setDetailModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                setSelectedKnowledgePoint(record);
                setEditModalVisible(true);
              }}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个知识点吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    });
  }

  const rowSelection = showActions ? {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  } : undefined;

  return (
    <div>
      {/* Statistics Cards */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总知识点数"
                value={statistics.total_knowledge_points}
                prefix={<Badge status="processing" />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="高重要性"
                value={statistics.by_importance_level['5'] || 0}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="中等重要性"
                value={statistics.by_importance_level['3'] || 0}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="一般重要性"
                value={statistics.by_importance_level['1'] || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filters */}
      {showFilters && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={16} align="middle">
            <Col span={6}>
              <Search
                placeholder="搜索知识点标题或内容"
                value={filters.searchQuery}
                onChange={(e) => setFilters(prev => ({ ...prev, searchQuery: e.target.value }))}
                onSearch={loadKnowledgePoints}
                enterButton={<SearchOutlined />}
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="选择知识库"
                value={filters.knowledgeBaseId}
                onChange={(value) => setFilters(prev => ({ ...prev, knowledgeBaseId: value, documentId: undefined }))}
                allowClear
                style={{ width: '100%' }}
              >
                {knowledgeBases.map(kb => (
                  <Option key={kb.id} value={kb.id}>{kb.name}</Option>
                ))}
              </Select>
            </Col>
            <Col span={4}>
              <Select
                placeholder="选择文档"
                value={filters.documentId}
                onChange={(value) => setFilters(prev => ({ ...prev, documentId: value }))}
                allowClear
                disabled={!filters.knowledgeBaseId}
                style={{ width: '100%' }}
              >
                {documents.map(doc => (
                  <Option key={doc.id} value={doc.id}>{doc.filename}</Option>
                ))}
              </Select>
            </Col>
            <Col span={4}>
              <Select
                placeholder="重要性级别"
                value={filters.importanceLevel}
                onChange={(value) => setFilters(prev => ({ ...prev, importanceLevel: value }))}
                allowClear
                style={{ width: '100%' }}
              >
                <Option value={1}>一般</Option>
                <Option value={2}>较低</Option>
                <Option value={3}>中等</Option>
                <Option value={4}>重要</Option>
                <Option value={5}>非常重要</Option>
              </Select>
            </Col>
            <Col span={6}>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={loadKnowledgePoints}>
                  刷新
                </Button>
                <Button icon={<FilterOutlined />} onClick={() => {
                  setFilters({
                    searchQuery: '',
                    importanceLevel: undefined,
                    knowledgeBaseId: knowledgeBaseId,
                    documentId: documentId,
                  });
                }}>
                  清除筛选
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* Action Bar */}
      {showActions && (
        <Card style={{ marginBottom: 16 }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setCreateModalVisible(true)}
                >
                  新建知识点
                </Button>
                {filters.documentId && (
                  <Button
                    icon={<ImportOutlined />}
                    onClick={() => handleExtractFromDocument(filters.documentId!)}
                    loading={loading}
                  >
                    从当前文档提取
                  </Button>
                )}
                {filters.knowledgeBaseId && (
                  <Button
                    icon={<ImportOutlined />}
                    onClick={() => handleExtractFromKnowledgeBase(filters.knowledgeBaseId!)}
                    loading={loading}
                  >
                    从知识库批量提取
                  </Button>
                )}
              </Space>
            </Col>
            <Col>
              <Space>
                {selectedRowKeys.length > 0 && (
                  <Popconfirm
                    title={`确定要删除选中的 ${selectedRowKeys.length} 个知识点吗？`}
                    onConfirm={handleBatchDelete}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button danger>
                      批量删除 ({selectedRowKeys.length})
                    </Button>
                  </Popconfirm>
                )}
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={knowledgePoints}
          rowKey="id"
          loading={loading}
          rowSelection={rowSelection}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, pageSize) => {
              setPagination(prev => ({
                ...prev,
                current: page,
                pageSize: pageSize || prev.pageSize,
              }));
            },
          }}
          scroll={{ y: height }}
          locale={{
            emptyText: (
              <Empty
                description="暂无知识点数据"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ),
          }}
        />
      </Card>

      {/* Detail Modal */}
      <Modal
        title="知识点详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="edit"
            type="primary"
            onClick={() => {
              setDetailModalVisible(false);
              setEditModalVisible(true);
            }}
          >
            编辑
          </Button>,
        ]}
        width={800}
      >
        {selectedKnowledgePoint && (
          <div>
            <Title level={4}>{selectedKnowledgePoint.title}</Title>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div>
                <Text strong>重要性级别：</Text>
                <Tag color={getImportanceColor(selectedKnowledgePoint.importance_level)}>
                  {getImportanceText(selectedKnowledgePoint.importance_level)}
                </Tag>
              </div>
              <div>
                <Text strong>创建时间：</Text>
                <Text>{new Date(selectedKnowledgePoint.created_at).toLocaleString('zh-CN')}</Text>
              </div>
              <div>
                <Text strong>内容：</Text>
                <Paragraph style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>
                  {selectedKnowledgePoint.content}
                </Paragraph>
              </div>
            </Space>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default KnowledgePointList;