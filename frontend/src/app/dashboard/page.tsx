/**
 * Dashboard page (protected route) - Enhanced with responsive components
 */
'use client';

import { Card, Typography, Space, Statistic, Button, Spin, App } from 'antd';
import { 
  FolderOutlined, 
  FileTextOutlined, 
  BookOutlined, 
  TrophyOutlined, 
  ClockCircleOutlined,
  PlusOutlined,
  UploadOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';
import { 
  Container, 
  ResponsiveGrid, 
  ResponsiveCol, 
  ResponsiveColPresets,
  PageHeader,
  EmptyState
} from '@/components/layout';
import { useNotification } from '@/components/feedback';
import { apiClient, DashboardStats } from '@/lib/api';

const { Title, Text } = Typography;

function DashboardContent() {
  const { message } = App.useApp();
  const { user, tokens } = useAuth();
  const router = useRouter();
  const notification = useNotification();
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardStats = useCallback(async () => {
    if (!tokens?.access_token) return;

    try {
      setLoading(true);
      const stats = await apiClient.getDashboardStats(tokens.access_token);
      setDashboardStats(stats);
    } catch (error) {
      console.error('获取仪表板统计数据失败:', error);
      message.error('获取统计数据失败');
    } finally {
      setLoading(false);
    }
  }, [tokens?.access_token, message]);

  useEffect(() => {
    fetchDashboardStats();
  }, [fetchDashboardStats]);

  const handleQuickAction = (action: string, path: string) => {
    notification.info(`正在前往${action}...`);
    router.push(path);
  };

  const statsData = [
    {
      title: '知识库',
      value: dashboardStats?.knowledge_bases || 0,
      icon: <FolderOutlined className="text-blue-500" />,
      suffix: '个',
      color: 'blue',
    },
    {
      title: '文档',
      value: dashboardStats?.documents || 0,
      icon: <FileTextOutlined className="text-green-500" />,
      suffix: '份',
      color: 'green',
    },
    {
      title: '学习记录',
      value: dashboardStats?.learning_records || 0,
      icon: <BookOutlined className="text-orange-500" />,
      suffix: '次',
      color: 'orange',
    },
    {
      title: '学习积分',
      value: dashboardStats?.learning_points || 0,
      icon: <TrophyOutlined className="text-purple-500" />,
      suffix: '分',
      color: 'purple',
    },
  ];

  const quickActions = [
    {
      title: '创建知识库',
      description: '创建您的第一个知识库来组织学习材料',
      icon: <FolderOutlined className="text-blue-500" />,
      action: () => handleQuickAction('知识库管理', '/knowledge-bases'),
      buttonText: '创建知识库',
      buttonIcon: <PlusOutlined />,
    },
    {
      title: '上传文档',
      description: '上传PDF、EPUB、TXT或MD格式的文档',
      icon: <UploadOutlined className="text-green-500" />,
      action: () => handleQuickAction('知识库管理', '/knowledge-bases'),
      buttonText: '上传文档',
      buttonIcon: <UploadOutlined />,
    },
    {
      title: '开始学习',
      description: '通过学习集进行基于记忆曲线的学习',
      icon: <PlayCircleOutlined className="text-orange-500" />,
      action: () => handleQuickAction('学习集管理', '/learning-sets'),
      buttonText: '开始学习',
      buttonIcon: <PlayCircleOutlined />,
    },
  ];

  return (
    <MainLayout>
      <Container>
        {/* 统计卡片 */}
        <ResponsiveGrid className="mb-6">
          {statsData.map((stat, index) => (
            <ResponsiveCol key={index} {...ResponsiveColPresets.quarterOnLarge}>
              <Card 
                className="hover:shadow-lg transition-shadow duration-200 fade-in"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <Spin spinning={loading}>
                  <Statistic
                    title={stat.title}
                    value={stat.value}
                    prefix={stat.icon}
                    suffix={stat.suffix}
                    valueStyle={{ 
                      color: `var(--color-${stat.color}-6, #1890ff)`,
                      fontSize: '24px',
                      fontWeight: 'bold'
                    }}
                  />
                </Spin>
              </Card>
            </ResponsiveCol>
          ))}
        </ResponsiveGrid>

        <ResponsiveGrid>
          {/* 快速开始 */}
          <ResponsiveCol {...ResponsiveColPresets.main}>
            <Card 
              title="快速开始" 
              className="h-full slide-in-right"
              extra={
                <Button 
                  type="link" 
                  onClick={() => router.push('/knowledge-bases')}
                >
                  查看全部
                </Button>
              }
            >
              <div className="space-y-6">
                {quickActions.map((action, index) => (
                  <div 
                    key={index}
                    className="flex items-start space-x-4 p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors duration-200"
                  >
                    <div className="flex-shrink-0 mt-1">
                      <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-sm">
                        {action.icon}
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <Title level={5} className="!mb-1">
                        {action.title}
                      </Title>
                      <Text type="secondary" className="block mb-3">
                        {action.description}
                      </Text>
                      <Button
                        type="primary"
                        size="small"
                        icon={action.buttonIcon}
                        onClick={action.action}
                      >
                        {action.buttonText}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </ResponsiveCol>

          {/* 最近活动 */}
          <ResponsiveCol {...ResponsiveColPresets.sidebar}>
            <Card 
              title="最近活动" 
              className="h-full slide-in-right"
              style={{ animationDelay: '200ms' }}
            >
              {loading ? (
                <div className="flex justify-center items-center h-32">
                  <Spin />
                </div>
              ) : dashboardStats?.recent_activity && dashboardStats.recent_activity.length > 0 ? (
                <div className="space-y-3">
                  {dashboardStats.recent_activity.map((activity, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="flex-shrink-0">
                        <BookOutlined className="text-blue-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <Text className="text-sm font-medium block truncate">
                          {activity.question_text}
                        </Text>
                        <div className="flex items-center space-x-2 mt-1">
                          <Text type="secondary" className="text-xs">
                            得分: {activity.score}
                          </Text>
                          <Text type="secondary" className="text-xs">
                            {new Date(activity.date).toLocaleDateString()}
                          </Text>
                        </div>
                      </div>
                    </div>
                  ))}
                  <Button 
                    type="link" 
                    size="small" 
                    onClick={() => router.push('/learning-records')}
                    className="w-full"
                  >
                    查看全部记录
                  </Button>
                </div>
              ) : (
                <EmptyState
                  title="暂无学习记录"
                  description="开始学习后，这里会显示您的学习活动"
                  image={<ClockCircleOutlined className="text-4xl text-gray-300" />}
                  action={{
                    text: '开始学习',
                    onClick: () => handleQuickAction('学习集管理', '/learning-sets'),
                    icon: <PlayCircleOutlined />,
                  }}
                />
              )}
            </Card>
          </ResponsiveCol>
        </ResponsiveGrid>

        {/* 学习进度 */}
        <ResponsiveGrid className="mt-6">
          <ResponsiveCol span={24}>
            <Card 
              title="本周学习进度"
              className="slide-in-right"
              style={{ animationDelay: '300ms' }}
              extra={
                <Button 
                  type="link" 
                  onClick={() => router.push('/learning-records')}
                >
                  查看详情
                </Button>
              }
            >
              <EmptyState
                title="还没有学习数据"
                description="完成一些学习任务后，这里会显示您的学习进度图表"
                image={<BookOutlined className="text-4xl text-gray-300" />}
                action={{
                  text: '查看学习记录',
                  onClick: () => handleQuickAction('学习记录', '/learning-records'),
                  icon: <BookOutlined />,
                  type: 'default',
                }}
              />
            </Card>
          </ResponsiveCol>
        </ResponsiveGrid>
      </Container>
    </MainLayout>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}