/**
 * Dashboard page (protected route)
 */
'use client';

import { Button, Card, Typography, Space } from 'antd';
import { LogoutOutlined, UserOutlined, FolderOutlined, FileTextOutlined, BookOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

const { Title, Text } = Typography;

function DashboardContent() {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <Title level={2}>学习平台仪表板</Title>
          <Button
            type="primary"
            danger
            icon={<LogoutOutlined />}
            onClick={handleLogout}
          >
            退出登录
          </Button>
        </div>

        <Card className="mb-6">
          <Space direction="vertical" size="middle">
            <div className="flex items-center space-x-3">
              <UserOutlined className="text-2xl text-blue-500" />
              <div>
                <Title level={4} className="mb-0">
                  欢迎回来，{user?.username}！
                </Title>
                <Text type="secondary">{user?.email}</Text>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <Card size="small" className="text-center">
                <Title level={4} className="text-blue-500">0</Title>
                <Text>知识库</Text>
              </Card>
              <Card size="small" className="text-center">
                <Title level={4} className="text-green-500">0</Title>
                <Text>文档</Text>
              </Card>
              <Card size="small" className="text-center">
                <Title level={4} className="text-orange-500">0</Title>
                <Text>学习记录</Text>
              </Card>
            </div>
          </Space>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Card
            hoverable
            className="text-center"
            actions={[
              <Link key="manage" href="/knowledge-bases">
                <Button type="primary" icon={<FolderOutlined />}>
                  管理知识库
                </Button>
              </Link>
            ]}
          >
            <Card.Meta
              avatar={<FolderOutlined className="text-3xl text-blue-500" />}
              title="知识库管理"
              description="创建和管理您的知识库，组织学习材料"
            />
          </Card>

          <Card
            hoverable
            className="text-center"
            actions={[
              <Link key="questions" href="/questions">
                <Button type="primary" icon={<FileTextOutlined />}>
                  问题管理
                </Button>
              </Link>
            ]}
          >
            <Card.Meta
              avatar={<FileTextOutlined className="text-3xl text-green-500" />}
              title="智能学习"
              description="基于文档内容自动生成学习问题"
            />
          </Card>

          <Card
            hoverable
            className="text-center"
            actions={[
              <Button key="review" disabled>
                即将推出
              </Button>
            ]}
          >
            <Card.Meta
              avatar={<BookOutlined className="text-3xl text-orange-500" />}
              title="复习系统"
              description="基于记忆曲线的智能复习安排"
            />
          </Card>
        </div>

        <Card title="快速开始">
          <Space direction="vertical" size="large" className="w-full">
            <div>
              <Title level={5}>1. 创建知识库</Title>
              <Text type="secondary">
                创建您的第一个知识库来组织学习材料
              </Text>
            </div>
            <div>
              <Title level={5}>2. 上传文档</Title>
              <Text type="secondary">
                上传PDF、EPUB、TXT或MD格式的文档
              </Text>
            </div>
            <div>
              <Title level={5}>3. 开始学习</Title>
              <Text type="secondary">
                系统将自动生成问题帮助您学习文档内容
              </Text>
            </div>
          </Space>
        </Card>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}