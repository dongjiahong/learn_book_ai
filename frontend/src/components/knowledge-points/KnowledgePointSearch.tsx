'use client';

import React, { useState } from 'react';
import {
  Card,
  Input,
  Button,
  List,
  Typography,
  Tag,
  Space,
  Empty,
  Spin,
  Alert,
  Row,
  Col,
  Select,
  InputNumber,
} from 'antd';
import { SearchOutlined, EyeOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, KnowledgePointSearchResponse } from '@/lib/api';

const { Search } = Input;
const { Text, Paragraph } = Typography;
const { Option } = Select;

interface KnowledgePointSearchProps {
  documentId?: number;
  onKnowledgePointSelect?: (kpId: number) => void;
}

interface SearchResult {
  content: string;
  metadata: {
    knowledge_point_id: number;
    document_id: number;
    title: string;
    importance_level: number;
  };
  distance?: number;
  id: string;
}

const KnowledgePointSearch: React.FC<KnowledgePointSearchProps> = ({
  documentId,
  onKnowledgePointSelect,
}) => {
  const { token } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOptions, setSearchOptions] = useState({
    document_id: documentId,
    importance_level: undefined as number | undefined,
    n_results: 10,
  });

  const handleSearch = async (query: string) => {
    if (!token || !query.trim()) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.searchKnowledgePoints(token, query.trim(), {
        document_id: searchOptions.document_id,
        importance_level: searchOptions.importance_level,
        n_results: searchOptions.n_results,
      });

      setSearchResults(response.results);
    } catch (error) {
      console.error('Failed to search knowledge points:', error);
      setSearchResults([]);
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

  const getSimilarityScore = (distance?: number) => {
    if (distance === undefined) return '未知';
    // Convert distance to similarity percentage (assuming cosine distance)
    const similarity = Math.max(0, (1 - distance) * 100);
    return `${similarity.toFixed(1)}%`;
  };

  const getSimilarityColor = (distance?: number) => {
    if (distance === undefined) return 'default';
    const similarity = (1 - distance) * 100;
    if (similarity >= 80) return 'green';
    if (similarity >= 60) return 'blue';
    if (similarity >= 40) return 'orange';
    return 'red';
  };

  return (
    <Card title="知识点搜索" style={{ height: '100%' }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* Search Options */}
        <Card size="small" title="搜索选项">
          <Row gutter={16} align="middle">
            <Col span={8}>
              <Text strong>最小重要性级别：</Text>
              <Select
                placeholder="不限制"
                value={searchOptions.importance_level}
                onChange={(value) => setSearchOptions(prev => ({ ...prev, importance_level: value }))}
                allowClear
                style={{ width: '100%', marginTop: 4 }}
                size="small"
              >
                <Option value={1}>一般</Option>
                <Option value={2}>较低</Option>
                <Option value={3}>中等</Option>
                <Option value={4}>重要</Option>
                <Option value={5}>非常重要</Option>
              </Select>
            </Col>
            <Col span={8}>
              <Text strong>结果数量：</Text>
              <InputNumber
                min={1}
                max={50}
                value={searchOptions.n_results}
                onChange={(value) => setSearchOptions(prev => ({ ...prev, n_results: value || 10 }))}
                style={{ width: '100%', marginTop: 4 }}
                size="small"
              />
            </Col>
            <Col span={8}>
              <Text strong>文档范围：</Text>
              <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: '12px' }}>
                {documentId ? '限制在当前文档' : '搜索所有文档'}
              </Text>
            </Col>
          </Row>
        </Card>

        {/* Search Input */}
        <Search
          placeholder="输入关键词搜索相关知识点..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onSearch={handleSearch}
          enterButton={<SearchOutlined />}
          size="large"
          loading={loading}
        />

        {/* Search Results */}
        <div style={{ minHeight: 400, maxHeight: 600, overflowY: 'auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px 0' }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">正在搜索知识点...</Text>
              </div>
            </div>
          ) : searchResults.length > 0 ? (
            <List
              dataSource={searchResults}
              renderItem={(item, index) => (
                <List.Item
                  key={item.id}
                  actions={[
                    <Button
                      key="view"
                      type="link"
                      icon={<EyeOutlined />}
                      onClick={() => onKnowledgePointSelect?.(item.metadata.knowledge_point_id)}
                    >
                      查看详情
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        <Text strong>{item.metadata.title}</Text>
                        <Tag color={getImportanceColor(item.metadata.importance_level)}>
                          {getImportanceText(item.metadata.importance_level)}
                        </Tag>
                        <Tag color={getSimilarityColor(item.distance)}>
                          相似度: {getSimilarityScore(item.distance)}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <Paragraph
                          ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
                          style={{ marginBottom: 8 }}
                        >
                          {item.content}
                        </Paragraph>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          文档ID: {item.metadata.document_id} | 知识点ID: {item.metadata.knowledge_point_id}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          ) : searchQuery ? (
            <Empty
              description="未找到相关知识点"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Text type="secondary">
                尝试使用不同的关键词或调整搜索选项
              </Text>
            </Empty>
          ) : (
            <Empty
              description="输入关键词开始搜索"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Text type="secondary">
                使用语义搜索找到最相关的知识点
              </Text>
            </Empty>
          )}
        </div>

        {/* Search Tips */}
        {!searchQuery && (
          <Alert
            message="搜索提示"
            description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li>支持中文关键词搜索，会找到语义相关的知识点</li>
                <li>可以搜索概念、定义、问题等不同类型的内容</li>
                <li>相似度越高表示内容越相关</li>
                <li>重要性级别可以帮助筛选核心知识点</li>
              </ul>
            }
            type="info"
            showIcon
          />
        )}
      </Space>
    </Card>
  );
};

export default KnowledgePointSearch;