/**
 * Dashboard page (protected route) - Enhanced with responsive components
 */
'use client';

import { Card, Typography, Space, Statistic, Button } from 'antd';
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

const { Title, Text } = Typography;

function DashboardContent() {
  const { user } = useAuth();
  const router = useRouter();
  const notification = useNotification();

  const handleQuickAction = (action: string, path: string) => {
    notification.info(`正在前往${action}...`);
    router.push(path);
  };

  const statsData = [
    {
      title: '知识库',
      value: 0,
      icon: <FolderOutlined className="text-blue-500" />,
      suffix: '个',
      color: 'blue',
    },
    {
      title: '文档',
      value: 0,
      icon: <FileTextOutlined className="text-green-500" />,
      suffix: '份',
      color: 'green',
    },
    {
      title: '学习记录',
      value: 0,
      icon: <BookOutlined className="text-orange-500" />,
      suffix: '次',
      color: 'orange',
    },
    {
      title: '学习积分',
      value: 0,
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
      description: '系统将自动生成问题帮助您学习文档内容',
      icon: <PlayCircleOutlined className="text-orange-500" />,
      action: () => handleQuickAction('答题练习', '/practice'),
      buttonText: '开始练习',
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
                    className="flex items-start space-x-4 p-4 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
                  >
                    <div className="flex-shrink-0 mt-1">
                      <div className="w-10 h-10 bg-white dark:bg-gray-900 rounded-full flex items-center justify-center shadow-sm">
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
              <EmptyState
                title="暂无学习记录"
                description="开始学习后，这里会显示您的学习活动"
                image={<ClockCircleOutlined className="text-4xl text-gray-300" />}
                action={{
                  text: '开始学习',
                  onClick: () => handleQuickAction('答题练习', '/practice'),
                  icon: <PlayCircleOutlined />,
                }}
              />
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