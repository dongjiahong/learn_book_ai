'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Typography,
  Space,
  Tag,
  Button,
  Select,
  Input,
  message,
  Empty,
  Spin,
  Progress,
  Row,
  Col,
  Statistic,
  Modal,
  Popconfirm,
  Tooltip
} from 'antd';
import {
  HistoryOutlined,
  TrophyOutlined,
  CalendarOutlined,
  QuestionCircleOutlined,
  EyeOutlined,
  DeleteOutlined,
  ReloadOutlined,
  BarChartOutlined,
  FolderOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { 
  apiClient, 
  AnswerRecord, 
  KnowledgeBase, 
  EvaluationStatistics,
  PerformanceTrend
} from '@/lib/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

interface AnswerHistoryProps {
  questionId?: number;
  knowledgeBaseId?: number;
  onViewRecord?: (record: AnswerRecord) => void;
  onBack?: () => void;
}

const getScoreColor = (score: number): string => {
  if (score >= 9) return '#52c41a';
  if (score >= 7) return '#1890ff';
  if (score >= 5) return '#faad14';
  if (score >= 3) return '#fa8c16';
  return '#f5222d';
};

const getScoreLevel = (score: number): string => {
  if (score >= 9) return '优秀';
  if (score >= 7) return '良好';
  if (score >= 5) return '及格';
  return '需改进';
};

export function AnswerHistory({ 
  questionId, 
  knowledgeBaseId, 
  onViewRecord, 
  onBack 
}: AnswerHistoryProps) {
  const { tokens } = useAuth();
  const [records, setRecords] = useState<AnswerRecord[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [statistics, setStatistics] = useState<EvaluationStatistics | null>(null);
  const [trends, setTrends] = useState<PerformanceTrend[]>([]);
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<number | undefined>(knowledgeBaseId);
  const [searchText, setSearchText] = useState('');
  const [statsModalVisible, setStatsModalVisible] = useState(false);

  const fetchKnowledgeBases = async () => {
    if (!tokens?.access_token) return;

    try {
      const response = await apiClient.getKnowledgeBases(tokens.access_token);
      setKnowledgeBases(response.knowledge_bases);
    } catch (error) {
      console.error('Error fetching knowledge bases:', error);
    }
  };

  const fetchRecords = async () => {
    if (!tokens?.access_token) return;

    setLoading(true);
    try {
      const response = await apiClient.getAnswerRecords(
        tokens.access_token,
        questionId,
        selectedKnowledgeBase,
        0,
        100
      );

      let filteredRecords = response.records;

      // Apply search filter
      if (searchText) {
        const searchLower = searchText.toLowerCase();
        filteredRecords = filteredRecords.filter(record => 
          record.question_text.toLowerCase().includes(searchLower) ||
          record.user_answer.toLowerCase().includes(searchLower) ||
          record.feedback.toLowerCase().includes(searchLower)
        );
      }

      setRecords(filteredRecords);
    } catch (error) {
      message.error('获取答题记录失败');
      console.error('Error fetching answer records:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    if (!tokens?.access_token) return;

    setStatsLoading(true);
    try {
      const [statsResponse, trendsResponse] = await Promise.all([
        apiClient.getEvaluationStatistics(tokens.access_token, selectedKnowledgeBase),
        apiClient.getPerformanceTrends(tokens.access_token, selectedKnowledgeBase, 30)
      ]);

      setStatistics(statsResponse.statistics);
      setTrends(trendsResponse.trends);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    } finally {
      setStatsLoading(false);
    }
  };

  useEffect(() => {
    fetchKnowledgeBases();
  }, [tokens]);

  useEffect(() => {
    fetchRecords();
  }, [tokens, questionId, selectedKnowledgeBase, searchText]);

  const handleDeleteRecord = async (recordId: number) => {
    if (!tokens?.access_token) return;

    try {
      await apiClient.deleteAnswerRecord(tokens.access_token, recordId);
      message.success('记录删除成功');
      fetchRecords();
    } catch (error) {
      message.error('删除记录失败');
      console.error('Error deleting record:', error);
    }
  };

  const handleShowStats = () => {
    fetchStatistics();
    setStatsModalVisible(true);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={2} className="mb-2">
            <HistoryOutlined className="mr-2" />
            答题历史
          </Title>
          <Text type="secondary">
            {questionId ? '单题答题记录' : '全部答题记录'}
          </Text>
        </div>
        <Space>
          {onBack && (
            <Button onClick={onBack}>
              返回
            </Button>
          )}
          <Button icon={<BarChartOutlined />} onClick={handleShowStats}>
            统计分析
          </Button>
          <Button icon={<ReloadOutlined />} onClick={fetchRecords}>
            刷新
          </Button>
        </Space>
      </div>

      {/* Filters */}
      {!questionId && (
        <Card className="mb-6">
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Select
                placeholder="选择知识库"
                allowClear
                style={{ width: '100%' }}
                value={selectedKnowledgeBase}
                onChange={setSelectedKnowledgeBase}
              >
                {knowledgeBases.map(kb => (
                  <Option key={kb.id} value={kb.id}>
                    <FolderOutlined /> {kb.name}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Search
                placeholder="搜索问题、答案或反馈"
                allowClear
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                onSearch={fetchRecords}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Quick Stats */}
      {records.length > 0 && (
        <Row gutter={[16, 16]} className="mb-6">
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="总答题数"
                value={records.length}
                prefix={<QuestionCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="平均分"
                value={records.reduce((sum, r) => sum + r.score, 0) / records.length}
                precision={1}
                prefix={<TrophyOutlined />}
                suffix="/ 10"
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="最高分"
                value={Math.max(...records.map(r => r.score))}
                precision={1}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="优秀率"
                value={records.filter(r => r.score >= 9).length / records.length * 100}
                precision={1}
                suffix="%"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Records List */}
      {records.length === 0 && !loading ? (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无答题记录"
          >
            <Text type="secondary">
              开始答题后，您的记录将显示在这里
            </Text>
          </Empty>
        </Card>
      ) : (
        <Spin spinning={loading}>
          <List
            grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 3, xxl: 3 }}
            dataSource={records}
            renderItem={(record) => (
              <List.Item>
                <Card
                  hoverable
                  actions={[
                    <Tooltip key="view" title="查看详情">
                      <Button
                        type="link"
                        icon={<EyeOutlined />}
                        onClick={() => onViewRecord?.(record)}
                      >
                        查看
                      </Button>
                    </Tooltip>,
                    <Popconfirm
                      key="delete"
                      title="确定要删除这条记录吗？"
                      description="删除后将无法恢复。"
                      onConfirm={() => handleDeleteRecord(record.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Tooltip title="删除记录">
                        <Button
                          type="link"
                          danger
                          icon={<DeleteOutlined />}
                        >
                          删除
                        </Button>
                      </Tooltip>
                    </Popconfirm>
                  ]}
                >
                  <div className="space-y-3">
                    {/* Score */}
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-2">
                        <Progress
                          type="circle"
                          percent={record.score * 10}
                          format={() => record.score.toFixed(1)}
                          strokeColor={getScoreColor(record.score)}
                          size={50}
                        />
                        <div>
                          <div className="font-medium">{record.score.toFixed(1)} / 10</div>
                          <Tag color={getScoreColor(record.score)} size="small">
                            {getScoreLevel(record.score)}
                          </Tag>
                        </div>
                      </div>
                      <div className="text-right text-xs text-gray-500">
                        <div className="flex items-center">
                          <CalendarOutlined className="mr-1" />
                          {formatDate(record.answered_at)}
                        </div>
                      </div>
                    </div>

                    {/* Question */}
                    <div>
                      <Text strong className="text-sm line-clamp-2">
                        {record.question_text}
                      </Text>
                    </div>

                    {/* Answer Preview */}
                    <div>
                      <Text type="secondary" className="text-xs">我的答案：</Text>
                      <div className="bg-gray-50 p-2 rounded text-xs mt-1">
                        <Text className="line-clamp-2">
                          {record.user_answer}
                        </Text>
                      </div>
                    </div>

                    {/* Feedback Preview */}
                    <div>
                      <Text type="secondary" className="text-xs">评估反馈：</Text>
                      <div className="text-xs mt-1">
                        <Text className="line-clamp-2">
                          {record.feedback}
                        </Text>
                      </div>
                    </div>

                    {/* Meta */}
                    <div className="flex flex-wrap gap-1">
                      <Tag icon={<FileTextOutlined />} size="small">
                        {record.document_name}
                      </Tag>
                    </div>
                  </div>
                </Card>
              </List.Item>
            )}
          />
        </Spin>
      )}

      {/* Statistics Modal */}
      <Modal
        title="统计分析"
        open={statsModalVisible}
        onCancel={() => setStatsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setStatsModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        <Spin spinning={statsLoading}>
          {statistics && (
            <div className="space-y-6">
              {/* Overall Stats */}
              <Row gutter={[16, 16]}>
                <Col span={6}>
                  <Statistic
                    title="总答题数"
                    value={statistics.total_answers}
                    prefix={<QuestionCircleOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="平均分"
                    value={statistics.average_score}
                    precision={1}
                    prefix={<TrophyOutlined />}
                    suffix="/ 10"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="优秀率"
                    value={statistics.score_distribution['8-10'] / statistics.total_answers * 100}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="及格率"
                    value={(statistics.total_answers - statistics.score_distribution['0-2'] - statistics.score_distribution['2-4']) / statistics.total_answers * 100}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
              </Row>

              {/* Score Distribution */}
              <div>
                <Title level={5}>分数分布</Title>
                {Object.entries(statistics.score_distribution).map(([range, count]) => {
                  const percentage = statistics.total_answers > 0 
                    ? (count / statistics.total_answers) * 100 
                    : 0;
                  
                  return (
                    <div key={range} className="mb-2">
                      <div className="flex justify-between items-center mb-1">
                        <span>{range} 分</span>
                        <span>{count} 次 ({percentage.toFixed(1)}%)</span>
                      </div>
                      <Progress
                        percent={percentage}
                        strokeColor={getScoreColor(parseFloat(range.split('-')[1]) || 0)}
                        size="small"
                      />
                    </div>
                  );
                })}
              </div>

              {/* Recent Performance */}
              {statistics.recent_performance.length > 0 && (
                <div>
                  <Title level={5}>最近表现</Title>
                  <List
                    size="small"
                    dataSource={statistics.recent_performance.slice(0, 5)}
                    renderItem={(perf) => (
                      <List.Item>
                        <div className="flex justify-between items-center w-full">
                          <div className="flex-1">
                            <Text className="text-sm line-clamp-1">
                              {perf.question_text}
                            </Text>
                            <div className="text-xs text-gray-500">
                              {formatDate(perf.date)}
                            </div>
                          </div>
                          <div className="ml-4">
                            <Tag color={getScoreColor(perf.score)}>
                              {perf.score.toFixed(1)}
                            </Tag>
                          </div>
                        </div>
                      </List.Item>
                    )}
                  />
                </div>
              )}

              {/* Performance Trends */}
              {trends.length > 0 && (
                <div>
                  <Title level={5}>30天趋势</Title>
                  <div className="text-sm text-gray-600">
                    显示最近30天的答题表现趋势
                  </div>
                  {/* 这里可以添加图表组件来显示趋势 */}
                  <div className="mt-2 space-y-1">
                    {trends.slice(-7).map((trend, index) => (
                      <div key={index} className="flex justify-between items-center text-sm">
                        <span>{new Date(trend.date).toLocaleDateString()}</span>
                        <div className="flex items-center space-x-2">
                          <span>{trend.answer_count} 题</span>
                          <Tag color={getScoreColor(trend.average_score)} size="small">
                            {trend.average_score.toFixed(1)}
                          </Tag>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Spin>
      </Modal>
    </div>
  );
}