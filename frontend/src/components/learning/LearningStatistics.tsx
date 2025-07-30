'use client';

import React from 'react';
import { Card, Row, Col, Statistic, Progress, Button, Empty, Spin } from 'antd';
import { 
  TrophyOutlined, 
  BookOutlined, 
  ClockCircleOutlined, 
  BarChartOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { LearningStatistics as LearningStatsType } from '@/lib/api';
import { Line } from '@ant-design/plots';

interface LearningStatisticsProps {
  statistics?: LearningStatsType;
  loading?: boolean;
  onRefresh?: () => void;
}

export default function LearningStatistics({ 
  statistics, 
  loading = false, 
  onRefresh 
}: LearningStatisticsProps) {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Spin size="large" />
      </div>
    );
  }

  if (!statistics) {
    return (
      <Card>
        <Empty 
          description="No learning statistics available"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  // Prepare chart data
  const chartData = statistics.scores_by_date.map(item => ({
    date: item.date,
    score: item.avg_score,
    count: item.count
  }));

  const lineConfig = {
    data: chartData,
    xField: 'date',
    yField: 'score',
    point: {
      size: 5,
      shape: 'diamond',
    },
    tooltip: {
      formatter: (datum: { score: number; count: number }) => {
        return {
          name: 'Average Score',
          value: `${datum.score.toFixed(1)} (${datum.count} answers)`,
        };
      },
    },
    yAxis: {
      min: 0,
      max: 10,
    },
  };

  return (
    <div className="space-y-6">
      {/* Header with refresh button */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Learning Statistics</h2>
        {onRefresh && (
          <Button 
            icon={<ReloadOutlined />} 
            onClick={onRefresh}
            loading={loading}
          >
            Refresh
          </Button>
        )}
      </div>

      {/* Key Statistics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Questions Answered"
              value={statistics.total_questions_answered}
              prefix={<BookOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Average Score"
              value={statistics.average_score}
              precision={1}
              suffix="/ 10"
              prefix={<TrophyOutlined />}
              valueStyle={{ 
                color: statistics.average_score >= 7 ? '#52c41a' : 
                       statistics.average_score >= 5 ? '#faad14' : '#ff4d4f' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Study Time"
              value={statistics.total_study_time}
              suffix="min"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Knowledge Bases"
              value={statistics.knowledge_base_progress.length}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Performance Chart */}
      {chartData.length > 0 && (
        <Card title="Performance Trend (Last 30 Days)">
          <Line {...lineConfig} height={300} />
        </Card>
      )}

      {/* Knowledge Base Progress */}
      <Card title="Progress by Knowledge Base">
        {statistics.knowledge_base_progress.length > 0 ? (
          <div className="space-y-4">
            {statistics.knowledge_base_progress.map((kb, index) => (
              <div key={index} className="border-b pb-4 last:border-b-0">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">{kb.knowledge_base_name}</h4>
                  <span className="text-sm text-gray-500">
                    {kb.total_answered} questions answered
                  </span>
                </div>
                <div className="flex items-center space-x-4">
                  <Progress
                    percent={(kb.avg_score / 10) * 100}
                    strokeColor={{
                      '0%': kb.avg_score >= 7 ? '#52c41a' : 
                            kb.avg_score >= 5 ? '#faad14' : '#ff4d4f',
                      '100%': kb.avg_score >= 7 ? '#52c41a' : 
                              kb.avg_score >= 5 ? '#faad14' : '#ff4d4f',
                    }}
                    className="flex-1"
                  />
                  <span className="text-sm font-medium min-w-[60px]">
                    {kb.avg_score.toFixed(1)}/10
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Empty 
            description="No knowledge base progress data"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>

      {/* Difficulty Distribution */}
      {Object.keys(statistics.questions_by_difficulty).length > 0 && (
        <Card title="Questions by Difficulty Level">
          <Row gutter={[16, 16]}>
            {Object.entries(statistics.questions_by_difficulty).map(([level, count]) => (
              <Col xs={24} sm={8} key={level}>
                <Card size="small">
                  <Statistic
                    title={`Level ${level}`}
                    value={count}
                    suffix="questions"
                    valueStyle={{ 
                      color: level === '1' ? '#52c41a' : 
                             level === '2' ? '#faad14' : '#ff4d4f' 
                    }}
                  />
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}
    </div>
  );
}