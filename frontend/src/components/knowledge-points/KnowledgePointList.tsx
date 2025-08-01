'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Table,
  Button,
  Space,
  Tag,
  Card,
  Typography,
  Tooltip,
  Popconfirm,
  Badge,
  Row,
  Col,
  Statistic,
  Empty,
  App,
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, KnowledgePoint, KnowledgeBase } from '@/lib/api';
import KnowledgePointForm from './KnowledgePointForm';

const { Text } = Typography;

interface KnowledgePointListProps {
  knowledgeBaseId?: number;
  documentId?: number;
  showActions?: boolean;
  height?: number;
  refreshTrigger?: number;
}



const KnowledgePointList: React.FC<KnowledgePointListProps> = ({
  knowledgeBaseId,
  documentId,
  showActions = true,
  height,
  refreshTrigger,
}) => {
  const router = useRouter();
  const { tokens } = useAuthStore();
  const token = tokens?.access_token;
  const { message } = App.useApp();
  const [knowledgePoints, setKnowledgePoints] = useState<KnowledgePoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [statistics, setStatistics] = useState<{
    total_knowledge_points: number;
    by_importance_level: Record<string, number>;
  } | null>(null);
  


  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });



  // Modal states
  const [selectedKnowledgePoint, setSelectedKnowledgePoint] = useState<KnowledgePoint | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);

  const loadKnowledgePoints = useCallback(async (page = 1, pageSize = 20) => {
    if (!token) return;

    setLoading(true);
    try {
      const response = await apiClient.getKnowledgePoints(token, {
        document_id: documentId,
        knowledge_base_id: knowledgeBaseId,
        importance_level: undefined,
        search_query: undefined,
        skip: (page - 1) * pageSize,
        limit: pageSize,
      });

      setKnowledgePoints(response.knowledge_points);
      setPagination({
        current: page,
        pageSize: pageSize,
        total: response.count,
      });
    } catch (error) {
      console.error('Failed to load knowledge points:', error);
      message.error('加载知识点失败');
    } finally {
      setLoading(false);
    }
  }, [token, documentId, knowledgeBaseId, message]);

  const handlePaginationChange = useCallback((page: number, pageSize?: number) => {
    loadKnowledgePoints(page, pageSize || pagination.pageSize);
  }, [loadKnowledgePoints, pagination.pageSize]);

  const loadKnowledgeBases = useCallback(async () => {
    if (!token) return;

    try {
      const response = await apiClient.getKnowledgeBases(token, 0, 100);
      setKnowledgeBases(response.knowledge_bases);
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
    }
  }, [token]);

  const loadStatistics = useCallback(async () => {
    if (!token) return;

    try {
      const response = await apiClient.getKnowledgePointStatistics(
        token,
        knowledgeBaseId
      );
      setStatistics(response.statistics);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  }, [token, knowledgeBaseId]);

  useEffect(() => {
    loadKnowledgePoints(1, 20);
    loadKnowledgeBases();
    loadStatistics();
  }, [loadKnowledgePoints, loadKnowledgeBases, loadStatistics]);

  // Refresh when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      loadKnowledgePoints(pagination.current, pagination.pageSize);
      loadStatistics();
    }
  }, [refreshTrigger, loadKnowledgePoints, loadStatistics, pagination.pageSize, pagination]);



  const handleDelete = async (id: number) => {
    if (!token) return;

    try {
      await apiClient.deleteKnowledgePoint(token, id);
      message.success('知识点删除成功');
      loadKnowledgePoints(pagination.current, pagination.pageSize);
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
      loadKnowledgePoints(pagination.current, pagination.pageSize);
      loadStatistics();
    } catch (error) {
      console.error('Failed to batch delete knowledge points:', error);
      message.error('批量删除失败');
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
          onClick={() => router.push(`/knowledge-points/${record.id}`)}
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
              onClick={() => router.push(`/knowledge-points/${record.id}`)}
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



      {/* Batch Actions */}
      {showActions && selectedRowKeys.length > 0 && (
        <Card style={{ marginBottom: 16 }}>
          <Row justify="end" align="middle">
            <Col>
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
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: handlePaginationChange,
            onShowSizeChange: handlePaginationChange,
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



      {/* Edit Modal */}
      {selectedKnowledgePoint && (
        <KnowledgePointForm
          visible={editModalVisible}
          onCancel={() => setEditModalVisible(false)}
          onSuccess={() => {
            loadKnowledgePoints(pagination.current, pagination.pageSize);
            loadStatistics();
          }}
          knowledgePoint={selectedKnowledgePoint}
        />
      )}


    </div>
  );
};

export default KnowledgePointList;