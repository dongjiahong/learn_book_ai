'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  message,
  Tooltip,
  Popconfirm,
  Rate,
  Progress,
  Empty,
  Tabs,
} from 'antd';
import {
  PlayCircleOutlined,
  DeleteOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, ReviewRecord } from '@/lib/api';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

interface ReviewRecordsListProps {
  onRecordUpdate?: () => void;
  dueReviews?: ReviewRecord[];
}

export default function ReviewRecordsList({ 
  onRecordUpdate,
  dueReviews 
}: ReviewRecordsListProps) {
  const { tokens } = useAuthStore();
  const [allReviews, setAllReviews] = useState<ReviewRecord[]>([]);
  const [dueReviewsList, setDueReviewsList] = useState<ReviewRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [reviewModalVisible, setReviewModalVisible] = useState(false);
  const [selectedReview, setSelectedReview] = useState<ReviewRecord | null>(null);
  const [reviewQuality, setReviewQuality] = useState(3);

  useEffect(() => {
    if (tokens?.access_token) {
      loadReviews();
      loadDueReviews();
    }
  }, [loadDueReviews, loadReviews, tokens]);

  useEffect(() => {
    if (dueReviews) {
      setDueReviewsList(dueReviews);
    }
  }, [dueReviews]);

  const loadReviews = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getReviewRecords(tokens!.access_token, 0, 100);
      setAllReviews(data);
    } catch (error) {
      console.error('Failed to load review records:', error);
      message.error('Failed to load review records');
    } finally {
      setLoading(false);
    }
  };

  const loadDueReviews = async () => {
    try {
      const data = await apiClient.getDueReviews(tokens!.access_token, 50);
      setDueReviewsList(data);
    } catch (error) {
      console.error('Failed to load due reviews:', error);
    }
  };

  const handleStartReview = (record: ReviewRecord) => {
    setSelectedReview(record);
    setReviewQuality(3);
    setReviewModalVisible(true);
  };

  const handleCompleteReview = async () => {
    if (!selectedReview) return;

    try {
      await apiClient.completeReview(
        tokens!.access_token,
        selectedReview.id,
        reviewQuality
      );
      message.success('Review completed successfully');
      setReviewModalVisible(false);
      setSelectedReview(null);
      loadReviews();
      loadDueReviews();
      onRecordUpdate?.();
    } catch (error) {
      console.error('Failed to complete review:', error);
      message.error('Failed to complete review');
    }
  };

  const handleDeleteReview = async (recordId: number) => {
    try {
      await apiClient.deleteReviewRecord(tokens!.access_token, recordId);
      message.success('Review record deleted successfully');
      loadReviews();
      loadDueReviews();
      onRecordUpdate?.();
    } catch (error) {
      console.error('Failed to delete review record:', error);
      message.error('Failed to delete review record');
    }
  };

  const getStatusColor = (record: ReviewRecord) => {
    if (!record.next_review) return 'default';
    const now = dayjs();
    const nextReview = dayjs(record.next_review);
    
    if (nextReview.isBefore(now)) return 'red';
    if (nextReview.diff(now, 'hours') < 24) return 'orange';
    return 'green';
  };

  const getStatusText = (record: ReviewRecord) => {
    if (!record.next_review) return 'Not scheduled';
    const now = dayjs();
    const nextReview = dayjs(record.next_review);
    
    if (nextReview.isBefore(now)) return 'Due now';
    return `Due ${nextReview.fromNow()}`;
  };

  const dueColumns: ColumnsType<ReviewRecord> = [
    {
      title: 'Content',
      dataIndex: 'content_title',
      key: 'content_title',
      ellipsis: true,
      render: (text: string, record) => (
        <div>
          <div className="font-medium">
            {text || `${record.content_type} #${record.content_id}`}
          </div>
          <div className="text-sm text-gray-500">
            {record.document_filename} • {record.knowledge_base_name}
          </div>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'content_type',
      key: 'content_type',
      width: 100,
      render: (type: string) => (
        <Tag color={type === 'question' ? 'blue' : 'green'}>
          {type === 'question' ? 'Question' : 'Knowledge Point'}
        </Tag>
      ),
    },
    {
      title: 'Reviews',
      dataIndex: 'review_count',
      key: 'review_count',
      width: 80,
      render: (count: number) => (
        <span className="font-medium">{count}</span>
      ),
    },
    {
      title: 'Interval',
      dataIndex: 'interval_days',
      key: 'interval_days',
      width: 100,
      render: (days: number) => (
        <span>{days} day{days !== 1 ? 's' : ''}</span>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Start Review">
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleStartReview(record)}
            >
              Review
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  const allColumns: ColumnsType<ReviewRecord> = [
    {
      title: 'Content',
      dataIndex: 'content_title',
      key: 'content_title',
      ellipsis: true,
      render: (text: string, record) => (
        <div>
          <div className="font-medium">
            {text || `${record.content_type} #${record.content_id}`}
          </div>
          <div className="text-sm text-gray-500">
            {record.document_filename} • {record.knowledge_base_name}
          </div>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'content_type',
      key: 'content_type',
      width: 100,
      render: (type: string) => (
        <Tag color={type === 'question' ? 'blue' : 'green'}>
          {type === 'question' ? 'Question' : 'Knowledge Point'}
        </Tag>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 120,
      render: (_, record) => (
        <Tag color={getStatusColor(record)}>
          {getStatusText(record)}
        </Tag>
      ),
    },
    {
      title: 'Reviews',
      dataIndex: 'review_count',
      key: 'review_count',
      width: 80,
      render: (count: number) => (
        <span className="font-medium">{count}</span>
      ),
    },
    {
      title: 'Ease Factor',
      dataIndex: 'ease_factor',
      key: 'ease_factor',
      width: 100,
      render: (factor: number) => (
        <Progress
          percent={(factor - 1.3) / (3.0 - 1.3) * 100}
          size="small"
          format={() => factor.toFixed(1)}
        />
      ),
    },
    {
      title: 'Last Reviewed',
      dataIndex: 'last_reviewed',
      key: 'last_reviewed',
      width: 120,
      render: (date: string) => 
        date ? dayjs(date).format('MM/DD HH:mm') : 'Never',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Start Review">
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              onClick={() => handleStartReview(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Are you sure you want to delete this review record?"
            onConfirm={() => handleDeleteReview(record.id)}
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

  return (
    <div className="space-y-4">
      <Tabs 
        defaultActiveKey="due"
        items={[
          {
            key: "due",
            label: (
              <span>
                <ClockCircleOutlined />
                Due Reviews ({dueReviewsList.length})
              </span>
            ),
            children: (
              <Card>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium">Reviews Due Now</h3>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={loadDueReviews}
                    loading={loading}
                  >
                    Refresh
                  </Button>
                </div>
                
                {dueReviewsList.length > 0 ? (
                  <Table
                    columns={dueColumns}
                    dataSource={dueReviewsList}
                    rowKey="id"
                    loading={loading}
                    pagination={false}
                  />
                ) : (
                  <Empty
                    description="No reviews due at the moment"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                )}
              </Card>
            )
          },
          {
            key: "all",
            label: (
              <span>
                <CheckCircleOutlined />
                All Reviews ({allReviews.length})
              </span>
            ),
            children: (
              <Card>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium">All Review Records</h3>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={loadReviews}
                    loading={loading}
                  >
                    Refresh
                  </Button>
                </div>
                
                <Table
                  columns={allColumns}
                  dataSource={allReviews}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) =>
                      `${range[0]}-${range[1]} of ${total} records`,
                  }}
                />
              </Card>
            )
          }
        ]}
      />

      {/* Review Modal */}
      <Modal
        title="Complete Review"
        open={reviewModalVisible}
        onCancel={() => {
          setReviewModalVisible(false);
          setSelectedReview(null);
        }}
        onOk={handleCompleteReview}
        okText="Complete Review"
        width={600}
      >
        {selectedReview && (
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Content</h4>
              <div className="bg-gray-50 p-3 rounded">
                <div className="font-medium">
                  {selectedReview.content_title || 
                   `${selectedReview.content_type} #${selectedReview.content_id}`}
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  Type: {selectedReview.content_type} • 
                  Document: {selectedReview.document_filename} • 
                  Knowledge Base: {selectedReview.knowledge_base_name}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">Review Count</h4>
                <p className="text-lg">{selectedReview.review_count}</p>
              </div>
              <div>
                <h4 className="font-medium mb-2">Current Interval</h4>
                <p className="text-lg">{selectedReview.interval_days} days</p>
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-2">Ease Factor</h4>
              <Progress
                percent={(selectedReview.ease_factor - 1.3) / (3.0 - 1.3) * 100}
                format={() => selectedReview.ease_factor.toFixed(1)}
              />
            </div>

            <div>
              <h4 className="font-medium mb-2">
                How well did you remember this content?
              </h4>
              <div className="space-y-2">
                <Rate
                  count={6}
                  value={reviewQuality}
                  onChange={setReviewQuality}
                  character={({ index }) => (
                    <span className="text-lg">
                      {index === 0 ? '😰' : 
                       index === 1 ? '😕' : 
                       index === 2 ? '😐' : 
                       index === 3 ? '🙂' : 
                       index === 4 ? '😊' : '🤩'}
                    </span>
                  )}
                />
                <div className="text-sm text-gray-600">
                  {reviewQuality === 0 && 'Complete blackout'}
                  {reviewQuality === 1 && 'Incorrect response; correct one remembered'}
                  {reviewQuality === 2 && 'Incorrect response; correct one seemed easy to recall'}
                  {reviewQuality === 3 && 'Correct response recalled with serious difficulty'}
                  {reviewQuality === 4 && 'Correct response after a hesitation'}
                  {reviewQuality === 5 && 'Perfect response'}
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}