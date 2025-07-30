'use client';

import React, { useState } from 'react';
import {
  Card,
  Typography,
  Space,
  Tag,
  Button,
  Progress,
  Collapse,
  Alert,
  Divider,
  Row,
  Col,
  Statistic,
  List,
  message,
  Modal
} from 'antd';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  TrophyOutlined,
  BulbOutlined,
  FileTextOutlined,
  QuestionCircleOutlined,
  EditOutlined,
  HistoryOutlined,
  ShareAltOutlined
} from '@ant-design/icons';
import { AnswerEvaluationResponse, Question } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface EvaluationResultProps {
  question: Question;
  evaluationResult: AnswerEvaluationResponse;
  onRetry?: () => void;
  onViewHistory?: () => void;
  onBack?: () => void;
}

const getScoreColor = (score: number): string => {
  if (score >= 9) return '#52c41a'; // green
  if (score >= 7) return '#1890ff'; // blue
  if (score >= 5) return '#faad14'; // orange
  if (score >= 3) return '#fa8c16'; // dark orange
  return '#f5222d'; // red
};

const getScoreLevel = (score: number): { level: string; icon: React.ReactNode; color: string } => {
  if (score >= 9) return { level: '优秀', icon: <TrophyOutlined />, color: 'success' };
  if (score >= 7) return { level: '良好', icon: <CheckCircleOutlined />, color: 'processing' };
  if (score >= 5) return { level: '及格', icon: <InfoCircleOutlined />, color: 'warning' };
  return { level: '需改进', icon: <ExclamationCircleOutlined />, color: 'error' };
};

export function EvaluationResult({ 
  question, 
  evaluationResult, 
  onRetry, 
  onViewHistory, 
  onBack 
}: EvaluationResultProps) {
  const [shareModalVisible, setShareModalVisible] = useState(false);
  
  const { evaluation } = evaluationResult;
  const scoreInfo = getScoreLevel(evaluation.score);

  const handleShare = () => {
    setShareModalVisible(true);
  };

  const handleCopyResult = () => {
    const shareText = `
问题：${question.question_text}

我的答案：${evaluationResult.user_answer}

评分：${evaluation.score}/10 (${scoreInfo.level})

反馈：${evaluation.feedback}

参考答案：${evaluation.reference_answer}
    `.trim();

    navigator.clipboard.writeText(shareText).then(() => {
      message.success('结果已复制到剪贴板');
      setShareModalVisible(false);
    }).catch(() => {
      message.error('复制失败');
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={2} className="mb-2">评估结果</Title>
          <Text type="secondary">AI已完成对您答案的评估分析</Text>
        </div>
        <Space>
          {onBack && (
            <Button onClick={onBack}>
              返回
            </Button>
          )}
          <Button icon={<ShareAltOutlined />} onClick={handleShare}>
            分享结果
          </Button>
          {onViewHistory && (
            <Button icon={<HistoryOutlined />} onClick={onViewHistory}>
              查看历史
            </Button>
          )}
          {onRetry && (
            <Button type="primary" icon={<EditOutlined />} onClick={onRetry}>
              重新答题
            </Button>
          )}
        </Space>
      </div>

      {/* Score Overview */}
      <Card className="mb-6">
        <Row gutter={[24, 24]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <div className="text-center">
              <div className="mb-4">
                <Progress
                  type="circle"
                  percent={evaluation.score * 10}
                  format={() => (
                    <div>
                      <div className="text-3xl font-bold" style={{ color: getScoreColor(evaluation.score) }}>
                        {evaluation.score}
                      </div>
                      <div className="text-sm text-gray-500">/ 10</div>
                    </div>
                  )}
                  strokeColor={getScoreColor(evaluation.score)}
                  size={120}
                />
              </div>
              <Tag 
                color={scoreInfo.color} 
                icon={scoreInfo.icon}
                className="text-base px-3 py-1"
              >
                {scoreInfo.level}
              </Tag>
            </div>
          </Col>
          <Col xs={24} sm={12} md={16}>
            <div className="space-y-4">
              <div>
                <Title level={4} className="mb-2">总体评价</Title>
                <Paragraph className="text-base">
                  {evaluation.feedback}
                </Paragraph>
              </div>
              
              {evaluation.detailed_analysis?.strengths && evaluation.detailed_analysis.strengths.length > 0 && (
                <div>
                  <Text strong className="text-green-600">
                    <CheckCircleOutlined className="mr-1" />
                    答案亮点
                  </Text>
                  <ul className="mt-1 ml-4">
                    {evaluation.detailed_analysis.strengths.slice(0, 2).map((strength, index) => (
                      <li key={index} className="text-sm text-gray-700">{strength}</li>
                    ))}
                  </ul>
                </div>
              )}

              {evaluation.detailed_analysis?.improvement_suggestions && evaluation.detailed_analysis.improvement_suggestions.length > 0 && (
                <div>
                  <Text strong className="text-orange-600">
                    <BulbOutlined className="mr-1" />
                    改进建议
                  </Text>
                  <ul className="mt-1 ml-4">
                    {evaluation.detailed_analysis.improvement_suggestions.slice(0, 2).map((suggestion, index) => (
                      <li key={index} className="text-sm text-gray-700">{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Col>
        </Row>
      </Card>

      {/* Question Review */}
      <Card title={
        <Space>
          <QuestionCircleOutlined />
          <span>问题回顾</span>
        </Space>
      } className="mb-6">
        <Card size="small" className="bg-blue-50 border-blue-200">
          <Paragraph className="mb-0 font-medium">
            {question.question_text}
          </Paragraph>
        </Card>
        {question.context && (
          <div className="mt-3">
            <Text type="secondary" className="text-sm">参考上下文：</Text>
            <Card size="small" className="bg-gray-50 mt-1">
              <Paragraph className="mb-0 text-sm">
                {question.context}
              </Paragraph>
            </Card>
          </div>
        )}
      </Card>

      {/* Answer Comparison */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <EditOutlined />
                <span>您的答案</span>
              </Space>
            }
            size="small"
          >
            <Card size="small" className="bg-yellow-50 border-yellow-200">
              <Paragraph className="mb-0 text-sm">
                {evaluationResult.user_answer}
              </Paragraph>
            </Card>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <FileTextOutlined />
                <span>参考答案</span>
              </Space>
            }
            size="small"
          >
            <Card size="small" className="bg-green-50 border-green-200">
              <Paragraph className="mb-0 text-sm">
                {evaluation.reference_answer}
              </Paragraph>
            </Card>
          </Card>
        </Col>
      </Row>

      {/* Detailed Analysis */}
      {evaluation.detailed_analysis && (
        <Card title="详细分析" className="mb-6">
          <Collapse ghost>
            <Panel header="完整分析报告" key="full-analysis">
              <div className="space-y-4">
                {evaluation.detailed_analysis.overall_analysis && (
                  <div>
                    <Title level={5}>综合分析</Title>
                    <Paragraph>
                      {evaluation.detailed_analysis.overall_analysis}
                    </Paragraph>
                  </div>
                )}

                {evaluation.detailed_analysis.structured_analysis && Object.keys(evaluation.detailed_analysis.structured_analysis).length > 0 && (
                  <div>
                    <Title level={5}>分项评估</Title>
                    {Object.entries(evaluation.detailed_analysis.structured_analysis).map(([category, points]) => (
                      <div key={category} className="mb-3">
                        <Text strong className="text-blue-600">{category}</Text>
                        <List
                          size="small"
                          dataSource={points}
                          renderItem={(point) => (
                            <List.Item className="py-1">
                              <Text className="text-sm">• {point}</Text>
                            </List.Item>
                          )}
                        />
                      </div>
                    ))}
                  </div>
                )}

                <Row gutter={[16, 16]}>
                  {evaluation.detailed_analysis.strengths && evaluation.detailed_analysis.strengths.length > 0 && (
                    <Col xs={24} md={12}>
                      <div>
                        <Title level={5} className="text-green-600">
                          <CheckCircleOutlined className="mr-2" />
                          优点总结
                        </Title>
                        <List
                          size="small"
                          dataSource={evaluation.detailed_analysis.strengths}
                          renderItem={(strength) => (
                            <List.Item className="py-1">
                              <Text className="text-sm text-green-700">✓ {strength}</Text>
                            </List.Item>
                          )}
                        />
                      </div>
                    </Col>
                  )}

                  {evaluation.detailed_analysis.improvement_suggestions && evaluation.detailed_analysis.improvement_suggestions.length > 0 && (
                    <Col xs={24} md={12}>
                      <div>
                        <Title level={5} className="text-orange-600">
                          <BulbOutlined className="mr-2" />
                          改进建议
                        </Title>
                        <List
                          size="small"
                          dataSource={evaluation.detailed_analysis.improvement_suggestions}
                          renderItem={(suggestion) => (
                            <List.Item className="py-1">
                              <Text className="text-sm text-orange-700">→ {suggestion}</Text>
                            </List.Item>
                          )}
                        />
                      </div>
                    </Col>
                  )}
                </Row>
              </div>
            </Panel>
          </Collapse>
        </Card>
      )}

      {/* Next Steps */}
      <Card title="下一步建议" size="small">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Alert
              message="继续练习"
              description="多做类似题目，巩固知识点"
              type="info"
              showIcon
              icon={<EditOutlined />}
              action={
                onRetry && (
                  <Button size="small" type="primary" onClick={onRetry}>
                    重新答题
                  </Button>
                )
              }
            />
          </Col>
          <Col xs={24} sm={8}>
            <Alert
              message="查看历史"
              description="回顾之前的答题记录"
              type="success"
              showIcon
              icon={<HistoryOutlined />}
              action={
                onViewHistory && (
                  <Button size="small" onClick={onViewHistory}>
                    查看记录
                  </Button>
                )
              }
            />
          </Col>
          <Col xs={24} sm={8}>
            <Alert
              message="分享成果"
              description="与他人分享学习成果"
              type="warning"
              showIcon
              icon={<ShareAltOutlined />}
              action={
                <Button size="small" onClick={handleShare}>
                  分享
                </Button>
              }
            />
          </Col>
        </Row>
      </Card>

      {/* Share Modal */}
      <Modal
        title="分享评估结果"
        open={shareModalVisible}
        onCancel={() => setShareModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setShareModalVisible(false)}>
            取消
          </Button>,
          <Button key="copy" type="primary" onClick={handleCopyResult}>
            复制到剪贴板
          </Button>
        ]}
      >
        <div className="space-y-4">
          <Alert
            message="您可以复制评估结果到剪贴板，然后分享给他人"
            type="info"
            showIcon
          />
          <div className="bg-gray-50 p-4 rounded border text-sm">
            <div><strong>问题：</strong>{question.question_text}</div>
            <Divider className="my-2" />
            <div><strong>评分：</strong>{evaluation.score}/10 ({scoreInfo.level})</div>
            <Divider className="my-2" />
            <div><strong>反馈：</strong>{evaluation.feedback}</div>
          </div>
        </div>
      </Modal>
    </div>
  );
}