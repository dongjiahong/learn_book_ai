'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
  message,
} from 'antd';
import { SearchOutlined, EyeOutlined, FilterOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, KnowledgeBase, Document } from '@/lib/api';

const { Text, Paragraph } = Typography;
const { Option } = Select;

interface KnowledgePointSearchProps {
  documentId?: number;
  onKnowledgePointSelect?: (kpId: number) => void;
}

interface SearchFilters {
  knowledgeBaseId?: number;
  documentId?: number;
  nResults: number;
  keywords: string;
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
  const router = useRouter();
  const { tokens } = useAuthStore();
  const token = tokens?.access_token;
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({
    knowledgeBaseId: undefined,
    documentId: documentId,
    nResults: 10,
    keywords: '',
  });

  // 加载知识库列表
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

  // 当选择知识库时，加载对应的文档列表
  const handleKnowledgeBaseChange = async (kbId?: number) => {
    setSearchFilters(prev => ({ 
      ...prev, 
      knowledgeBaseId: kbId,
      documentId: undefined // 重置文档选择
    }));
    setDocuments([]);

    if (!kbId || !token) return;

    setLoadingDocuments(true);
    try {
      const response = await apiClient.getDocuments(token, kbId, 0, 100);
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to load documents:', error);
      message.error('加载文档失败');
    } finally {
      setLoadingDocuments(false);
    }
  };

  const handleSearch = async () => {
    if (!token) {
      message.error('请先登录');
      return;
    }

    // 验证搜索条件：至少需要关键词或知识库/文档
    const hasKeywords = searchFilters.keywords.trim();
    const hasKnowledgeBase = searchFilters.knowledgeBaseId;
    const hasDocument = searchFilters.documentId;

    if (!hasKeywords && !hasKnowledgeBase && !hasDocument) {
      message.warning('请输入关键词或选择知识库/文档进行搜索');
      return;
    }

    setLoading(true);
    try {
      // 只有当有关键词时才传递查询字符串，否则传递空字符串让后端使用过滤器搜索
      const queryString = hasKeywords ? searchFilters.keywords.trim() : '';
      
      const response = await apiClient.searchKnowledgePoints(token, queryString, {
        knowledge_base_id: searchFilters.knowledgeBaseId,
        document_id: searchFilters.documentId,
        n_results: searchFilters.nResults,
      });

      setSearchResults(response.results);
      
      if (response.results.length === 0) {
        if (hasKeywords) {
          message.info('未找到相关知识点，请尝试其他关键词或调整搜索条件');
        } else {
          message.info('所选范围内没有知识点');
        }
      } else {
        message.success(`找到 ${response.results.length} 个相关知识点`);
      }
    } catch (error) {
      console.error('Failed to search knowledge points:', error);
      message.error('搜索失败，请稍后重试');
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
    <Card title="智能搜索" style={{ height: '100%' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 搜索选项 */}
        <Card size="small" title={<><FilterOutlined /> 搜索选项</>}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text strong>知识库：</Text>
                <Select
                  placeholder="选择知识库"
                  value={searchFilters.knowledgeBaseId}
                  onChange={handleKnowledgeBaseChange}
                  allowClear
                  style={{ width: '100%' }}
                  showSearch
                  optionFilterProp="children"
                >
                  {knowledgeBases.map(kb => (
                    <Option key={kb.id} value={kb.id}>
                      {kb.name}
                    </Option>
                  ))}
                </Select>
              </Space>
            </Col>
            
            <Col xs={24} sm={12} md={6}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text strong>文档：</Text>
                <Select
                  placeholder="选择文档"
                  value={searchFilters.documentId}
                  onChange={(value) => setSearchFilters(prev => ({ ...prev, documentId: value }))}
                  allowClear
                  style={{ width: '100%' }}
                  disabled={!searchFilters.knowledgeBaseId}
                  loading={loadingDocuments}
                  showSearch
                  optionFilterProp="children"
                >
                  {documents.map(doc => (
                    <Option key={doc.id} value={doc.id}>
                      {doc.filename}
                    </Option>
                  ))}
                </Select>
              </Space>
            </Col>
            
            <Col xs={24} sm={12} md={6}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text strong>检索数量：</Text>
                <InputNumber
                  min={1}
                  max={50}
                  value={searchFilters.nResults}
                  onChange={(value) => setSearchFilters(prev => ({ ...prev, nResults: value || 10 }))}
                  style={{ width: '100%' }}
                  placeholder="1-50"
                />
              </Space>
            </Col>
            
            <Col xs={24} sm={12} md={6}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text strong>关键词：</Text>
                <Input
                  placeholder="输入搜索关键词"
                  value={searchFilters.keywords}
                  onChange={(e) => setSearchFilters(prev => ({ ...prev, keywords: e.target.value }))}
                  onPressEnter={handleSearch}
                />
              </Space>
            </Col>
          </Row>
          
          <Row style={{ marginTop: 16 }}>
            <Col span={24}>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={handleSearch}
                loading={loading}
                disabled={!searchFilters.keywords.trim() && !searchFilters.knowledgeBaseId && !searchFilters.documentId}
                size="large"
              >
                开始搜索
              </Button>
            </Col>
          </Row>
        </Card>

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
              renderItem={(item) => (
                <List.Item
                  key={item.id}
                  actions={[
                    <Button
                      key="view"
                      type="link"
                      icon={<EyeOutlined />}
                      onClick={() => {
                        if (onKnowledgePointSelect) {
                          onKnowledgePointSelect(item.metadata.knowledge_point_id);
                        } else {
                          router.push(`/knowledge-points/${item.metadata.knowledge_point_id}`);
                        }
                      }}
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
          ) : searchFilters.keywords ? (
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
              description="请设置搜索条件"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Text type="secondary">
                输入关键词进行语义搜索，或选择知识库/文档进行浏览
              </Text>
            </Empty>
          )}
        </div>

        {/* 搜索提示 */}
        {!searchFilters.keywords && !searchFilters.knowledgeBaseId && !searchFilters.documentId && (
          <Alert
            message="搜索提示"
            description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li><strong>搜索方式：</strong>可以单独使用关键词搜索，或选择知识库/文档浏览，也可以组合使用</li>
                <li><strong>关键词搜索：</strong>支持中文语义搜索，会显示相似度评分</li>
                <li><strong>知识库浏览：</strong>选择知识库可以浏览该库中的所有知识点</li>
                <li><strong>文档浏览：</strong>选择特定文档可以查看该文档的知识点</li>
                <li><strong>组合搜索：</strong>在特定知识库/文档范围内进行关键词搜索</li>
                <li><strong>检索数量：</strong>控制返回结果的数量，建议设置为10-20个</li>
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