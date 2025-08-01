'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  DatePicker,
  Space,
  Tag,
  Modal,
  Tooltip,
  Popconfirm,
  Row,
  Col,
  Drawer,
  App,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, LearningAnswerRecord, KnowledgeBase } from '@/lib/api';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { TextArea } = Input;

interface LearningRecordsListProps {
  onRecordUpdate?: () => void;
  recentRecords?: LearningAnswerRecord[];
}

export default function LearningRecordsList({
  onRecordUpdate,
  recentRecords
}: LearningRecordsListProps) {
  const { message } = App.useApp();
  const { tokens } = useAuthStore();
  const [records, setRecords] = useState<LearningAnswerRecord[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<LearningAnswerRecord | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<number | undefined>();
  const [scoreRange, setScoreRange] = useState<[number, number] | undefined>();
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

  // Pagination
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });

  useEffect(() => {
    if (tokens?.access_token) {
      loadKnowledgeBases();
      loadRecords();
    }
  }, [tokens?.access_token]);

  useEffect(() => {
    if (recentRecords) {
      setRecords(recentRecords);
    }
  }, [recentRecords]);

  const loadKnowledgeBases = async () => {
    try {
      const response = await apiClient.getKnowledgeBases(tokens!.access_token);
      setKnowledgeBases(response.knowledge_bases);
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
    }
  };

  const loadRecords = async (page = 1, pageSize = 20) => {
    try {
      setLoading(true);
      const filters: Record<string, string | number> = {};

      if (selectedKnowledgeBase) {
        filters.knowledge_base_id = selectedKnowledgeBase;
      }
      if (scoreRange) {
        filters.score_min = scoreRange[0];
        filters.score_max = scoreRange[1];
      }
      if (dateRange) {
        filters.date_from = dateRange[0].toISOString();
        filters.date_to = dateRange[1].toISOString();
      }

      const searchRequest = {
        query: searchQuery || undefined,
        filters,
        skip: (page - 1) * pageSize,
        limit: pageSize,
        sort_by: 'answered_at',
        sort_order: 'desc' as const,
      };

      const data = searchQuery || Object.keys(filters).length > 0
        ? await apiClient.searchLearningAnswerRecords(tokens!.access_token, searchRequest)
        : await apiClient.getLearningAnswerRecords(
          tokens!.access_token,
          (page - 1) * pageSize,
          pageSize,
          filters
        );

      setRecords(data);
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: data.length, // Note: This is approximate since we don't get total count
      }));
    } catch (error) {
      console.error('Failed to load records:', error);
      message.error('Failed to load learning records');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadRecords(1, pagination.pageSize);
  };

  const handleReset = () => {
    setSearchQuery('');
    setSelectedKnowledgeBase(undefined);
    setScoreRange(undefined);
    setDateRange(null);
    loadRecords(1, pagination.pageSize);
  };

  const handleEdit = (record: LearningAnswerRecord) => {
    setSelectedRecord(record);
    setEditModalVisible(true);
  };

  const handleDelete = async (recordId: number) => {
    try {
      await apiClient.deleteLearningAnswerRecord(tokens!.access_token, recordId);
      message.success('Record deleted successfully');
      loadRecords(pagination.current, pagination.pageSize);
      onRecordUpdate?.();
    } catch (error) {
      console.error('Failed to delete record:', error);
      message.error('Failed to delete record');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select records to delete');
      return;
    }

    try {
      const recordIds = selectedRowKeys.map(key => Number(key));
      await apiClient.bulkDeleteLearningAnswerRecords(tokens!.access_token, recordIds);
      message.success(`Successfully deleted ${recordIds.length} records`);
      setSelectedRowKeys([]);
      loadRecords(pagination.current, pagination.pageSize);
      onRecordUpdate?.();
    } catch (error) {
      console.error('Failed to bulk delete records:', error);
      message.error('Failed to delete records');
    }
  };

  const handleEditSubmit = async (values: Record<string, string | number>) => {
    if (!selectedRecord) return;

    try {
      await apiClient.updateLearningAnswerRecord(
        tokens!.access_token,
        selectedRecord.id,
        values
      );
      message.success('Record updated successfully');
      setEditModalVisible(false);
      setSelectedRecord(null);
      loadRecords(pagination.current, pagination.pageSize);
      onRecordUpdate?.();
    } catch (error) {
      console.error('Failed to update record:', error);
      message.error('Failed to update record');
    }
  };

  const getScoreColor = (score?: number) => {
    if (!score) return 'default';
    if (score >= 8) return 'green';
    if (score >= 6) return 'orange';
    return 'red';
  };

  const columns: ColumnsType<LearningAnswerRecord> = [
    {
      title: 'Question',
      dataIndex: 'question_text',
      key: 'question_text',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <span>{text?.substring(0, 50)}...</span>
        </Tooltip>
      ),
    },
    {
      title: 'Knowledge Base',
      dataIndex: 'knowledge_base_name',
      key: 'knowledge_base_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: 'Document',
      dataIndex: 'document_filename',
      key: 'document_filename',
      width: 150,
      ellipsis: true,
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      width: 80,
      render: (score: number) => (
        <Tag color={getScoreColor(score)}>
          {score ? `${score.toFixed(1)}/10` : 'N/A'}
        </Tag>
      ),
    },
    {
      title: 'Answered At',
      dataIndex: 'answered_at',
      key: 'answered_at',
      width: 120,
      render: (date: string) => dayjs(date).format('MM/DD HH:mm'),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedRecord(record);
                setDetailDrawerVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Are you sure you want to delete this record?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="Search questions, answers, or feedback"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="Select Knowledge Base"
              value={selectedKnowledgeBase}
              onChange={setSelectedKnowledgeBase}
              allowClear
              style={{ width: '100%' }}
            >
              {knowledgeBases.map(kb => (
                <Option key={kb.id} value={kb.id}>
                  {kb.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="Score Range"
              value={scoreRange}
              onChange={setScoreRange}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value={[8, 10]}>Excellent (8-10)</Option>
              <Option value={[6, 8]}>Good (6-8)</Option>
              <Option value={[4, 6]}>Fair (4-6)</Option>
              <Option value={[0, 4]}>Poor (0-4)</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
              style={{ width: '100%' }}
            />
          </Col>
        </Row>
        <Row gutter={[16, 16]} className="mt-4">
          <Col>
            <Space>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={handleSearch}
              >
                Search
              </Button>
              <Button
                icon={<FilterOutlined />}
                onClick={handleReset}
              >
                Reset
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => loadRecords(pagination.current, pagination.pageSize)}
                loading={loading}
              >
                Refresh
              </Button>
              {selectedRowKeys.length > 0 && (
                <Popconfirm
                  title={`Are you sure you want to delete ${selectedRowKeys.length} records?`}
                  onConfirm={handleBulkDelete}
                  okText="Yes"
                  cancelText="No"
                >
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                  >
                    Delete Selected ({selectedRowKeys.length})
                  </Button>
                </Popconfirm>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Records Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          rowSelection={rowSelection}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} records`,
            onChange: (page, pageSize) => {
              loadRecords(page, pageSize);
            },
          }}
        />
      </Card>

      {/* Edit Modal */}
      <Modal
        title="Edit Learning Record"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setSelectedRecord(null);
        }}
        onOk={() => {
          // Handle form submission
        }}
        width={800}
      >
        {selectedRecord && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">User Answer</label>
              <TextArea
                defaultValue={selectedRecord.user_answer}
                rows={4}
                placeholder="Enter your answer"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Reference Answer</label>
              <TextArea
                defaultValue={selectedRecord.reference_answer}
                rows={4}
                placeholder="Enter reference answer"
              />
            </div>
            <Row gutter={16}>
              <Col span={12}>
                <label className="block text-sm font-medium mb-2">Score</label>
                <Input
                  type="number"
                  min={0}
                  max={10}
                  step={0.1}
                  defaultValue={selectedRecord.score}
                  placeholder="Score (0-10)"
                />
              </Col>
            </Row>
            <div>
              <label className="block text-sm font-medium mb-2">Feedback</label>
              <TextArea
                defaultValue={selectedRecord.feedback}
                rows={3}
                placeholder="Enter feedback"
              />
            </div>
          </div>
        )}
      </Modal>

      {/* Detail Drawer */}
      <Drawer
        title="Learning Record Details"
        placement="right"
        width={600}
        open={detailDrawerVisible}
        onClose={() => {
          setDetailDrawerVisible(false);
          setSelectedRecord(null);
        }}
      >
        {selectedRecord && (
          <div className="space-y-6">
            <div>
              <h4 className="font-medium mb-2">Question</h4>
              <p className="text-gray-700 bg-gray-50 p-3 rounded">
                {selectedRecord.question_text}
              </p>
            </div>

            <div>
              <h4 className="font-medium mb-2">Your Answer</h4>
              <p className="text-gray-700 bg-blue-50 p-3 rounded">
                {selectedRecord.user_answer}
              </p>
            </div>

            {selectedRecord.reference_answer && (
              <div>
                <h4 className="font-medium mb-2">Reference Answer</h4>
                <p className="text-gray-700 bg-green-50 p-3 rounded">
                  {selectedRecord.reference_answer}
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">Score</h4>
                <Tag color={getScoreColor(selectedRecord.score)} className="text-lg">
                  {selectedRecord.score ? `${selectedRecord.score.toFixed(1)}/10` : 'N/A'}
                </Tag>
              </div>
              <div>
                <h4 className="font-medium mb-2">Answered At</h4>
                <p className="text-gray-700">
                  {dayjs(selectedRecord.answered_at).format('YYYY-MM-DD HH:mm:ss')}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">Knowledge Base</h4>
                <p className="text-gray-700">{selectedRecord.knowledge_base_name}</p>
              </div>
              <div>
                <h4 className="font-medium mb-2">Document</h4>
                <p className="text-gray-700">{selectedRecord.document_filename}</p>
              </div>
            </div>

            {selectedRecord.feedback && (
              <div>
                <h4 className="font-medium mb-2">Feedback</h4>
                <p className="text-gray-700 bg-yellow-50 p-3 rounded">
                  {selectedRecord.feedback}
                </p>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}