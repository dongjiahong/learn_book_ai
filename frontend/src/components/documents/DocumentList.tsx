'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Button,
  Upload,
  message,
  Popconfirm,
  Typography,
  Space,
  Tag,
  Empty,
  Modal,
  Progress,
  Tooltip
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileMarkdownOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { UploadProps } from 'antd';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, Document, KnowledgeBase } from '@/lib/api';

const { Title, Text } = Typography;

interface DocumentListProps {
  knowledgeBase: KnowledgeBase;
  onBack: () => void;
}

export function DocumentList({ knowledgeBase, onBack }: DocumentListProps) {
  const { tokens } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState<{
    filename: string;
    content: string;
    truncated: boolean;
  } | null>(null);
  const [processingStatuses, setProcessingStatuses] = useState<{[key: number]: {
    processed: boolean;
    processing_progress: number;
    error_message?: string;
  }}>({});

  const fetchDocuments = async () => {
    if (!tokens?.access_token) return;

    setLoading(true);
    try {
      const response = await apiClient.getDocuments(
        tokens.access_token,
        knowledgeBase.id
      );
      setDocuments(response.documents);
    } catch (error) {
      message.error('获取文档列表失败');
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [tokens, knowledgeBase.id]);

  // Poll processing status for unprocessed documents
  useEffect(() => {
    const unprocessedDocs = documents.filter(doc => !doc.processed);
    if (unprocessedDocs.length === 0) return;

    const pollProcessingStatus = async () => {
      if (!tokens?.access_token) return;

      const statusPromises = unprocessedDocs.map(async (doc) => {
        try {
          const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8800'}/api/documents/${doc.id}/processing-status`,
            {
              headers: {
                'Authorization': `Bearer ${tokens.access_token}`,
              },
            }
          );
          if (response.ok) {
            const status = await response.json();
            return { docId: doc.id, status };
          }
        } catch (error) {
          console.error(`Error getting status for document ${doc.id}:`, error);
        }
        return null;
      });

      const results = await Promise.all(statusPromises);
      const newStatuses: typeof processingStatuses = {};
      
      results.forEach((result) => {
        if (result) {
          newStatuses[result.docId] = result.status;
        }
      });

      setProcessingStatuses(prev => ({ ...prev, ...newStatuses }));

      // Refresh document list if any document completed processing
      const completedDocs = results.filter(result => 
        result && result.status.processed && !documents.find(doc => doc.id === result.docId)?.processed
      );
      
      if (completedDocs.length > 0) {
        fetchDocuments();
      }
    };

    // Poll every 3 seconds
    const interval = setInterval(pollProcessingStatus, 3000);
    
    // Initial poll
    pollProcessingStatus();

    return () => clearInterval(interval);
  }, [documents, tokens]);

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'pdf':
        return <FilePdfOutlined className="text-red-500" />;
      case 'md':
        return <FileMarkdownOutlined className="text-blue-500" />;
      case 'txt':
        return <FileTextOutlined className="text-gray-500" />;
      case 'epub':
        return <FileTextOutlined className="text-green-500" />;
      default:
        return <FileTextOutlined className="text-gray-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.epub,.txt,.md',
    beforeUpload: (file) => {
      const isValidType = ['application/pdf', 'application/epub+zip', 'text/plain', 'text/markdown'].includes(file.type) ||
                         file.name.endsWith('.md') || file.name.endsWith('.txt') || file.name.endsWith('.pdf') || file.name.endsWith('.epub');
      
      if (!isValidType) {
        message.error('只支持 PDF、EPUB、TXT、MD 格式的文件');
        return false;
      }

      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('文件大小不能超过 50MB');
        return false;
      }

      return true;
    },
    customRequest: async ({ file, onSuccess, onError }) => {
      if (!tokens?.access_token) {
        onError?.(new Error('未登录'));
        return;
      }

      setUploading(true);
      try {
        const response = await apiClient.uploadDocument(
          tokens.access_token,
          knowledgeBase.id,
          file as File
        );

        if (response.success) {
          message.success('文档上传成功');
          onSuccess?.(response);
          fetchDocuments();
        } else {
          throw new Error(response.message);
        }
      } catch (error) {
        message.error('文档上传失败');
        onError?.(error as Error);
        console.error('Error uploading document:', error);
      } finally {
        setUploading(false);
      }
    },
  };

  const handleDelete = async (id: number) => {
    if (!tokens?.access_token) return;

    try {
      await apiClient.deleteDocument(tokens.access_token, id);
      message.success('文档删除成功');
      fetchDocuments();
    } catch (error) {
      message.error('删除文档失败');
      console.error('Error deleting document:', error);
    }
  };

  const handlePreview = async (document: Document) => {
    if (!tokens?.access_token) return;

    // Only support text preview for txt and md files
    if (!['txt', 'md'].includes(document.file_type)) {
      message.info('该文件类型不支持预览，请下载查看');
      return;
    }

    try {
      const content = await apiClient.getDocumentContent(tokens.access_token, document.id);
      setPreviewContent(content);
      setPreviewVisible(true);
    } catch (error) {
      message.error('获取文档内容失败');
      console.error('Error getting document content:', error);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div>
          <Button type="link" onClick={onBack} className="p-0 mb-2">
            ← 返回知识库列表
          </Button>
          <Title level={3}>{knowledgeBase.name} - 文档管理</Title>
        </div>
        <Upload {...uploadProps} showUploadList={false}>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            loading={uploading}
          >
            上传文档
          </Button>
        </Upload>
      </div>

      {documents.length === 0 && !loading ? (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无文档"
          >
            <Upload {...uploadProps} showUploadList={false}>
              <Button type="primary" icon={<UploadOutlined />}>
                上传第一个文档
              </Button>
            </Upload>
          </Empty>
        </Card>
      ) : (
        <List
          loading={loading}
          dataSource={documents}
          renderItem={(doc) => (
            <List.Item
              actions={[
                <Tooltip key="preview" title="预览">
                  <Button
                    type="text"
                    icon={<EyeOutlined />}
                    onClick={() => handlePreview(doc)}
                    disabled={!['txt', 'md'].includes(doc.file_type)}
                  />
                </Tooltip>,
                <Popconfirm
                  key="delete"
                  title="确定要删除这个文档吗？"
                  description="删除后将无法恢复。"
                  onConfirm={() => handleDelete(doc.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button type="text" danger icon={<DeleteOutlined />} />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={getFileIcon(doc.file_type)}
                title={
                  <div className="flex items-center space-x-2">
                    <span>{doc.filename}</span>
                    {doc.processed ? (
                      <Tag icon={<CheckCircleOutlined />} color="success">
                        已处理
                      </Tag>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <Tag icon={<ClockCircleOutlined />} color="processing">
                          处理中
                        </Tag>
                        {processingStatuses[doc.id] && (
                          <Progress
                            percent={Math.round(processingStatuses[doc.id].processing_progress * 100)}
                            size="small"
                            style={{ width: 60 }}
                          />
                        )}
                      </div>
                    )}
                    {processingStatuses[doc.id]?.error_message && (
                      <Tag color="error">
                        处理失败
                      </Tag>
                    )}
                  </div>
                }
                description={
                  <div>
                    <Space size="middle">
                      <Text type="secondary">
                        类型: {doc.file_type.toUpperCase()}
                      </Text>
                      <Text type="secondary">
                        大小: {formatFileSize(doc.file_size)}
                      </Text>
                      <Text type="secondary">
                        上传时间: {new Date(doc.created_at).toLocaleString()}
                      </Text>
                    </Space>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}

      <Modal
        title={`预览: ${previewContent?.filename}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {previewContent && (
          <div>
            <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded max-h-96 overflow-y-auto">
              {previewContent.content}
            </pre>
            {previewContent.truncated && (
              <Text type="secondary" className="text-sm">
                * 内容已截断，仅显示前5000个字符
              </Text>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}