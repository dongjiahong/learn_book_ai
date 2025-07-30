/**
 * Dashboard page (protected route)
 */
'use client';

import { Card, Typography, Space, Statistic, Row, Col } from 'antd';
import { UserOutlined, FolderOutlined, FileTextOutlined, BookOutlined, TrophyOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';

const { Title, Text } = Typography;

function DashboardContent() {
  const { user } = useAuth();

  return (
    <MainLayout>
      <div className="p-6">
        <div className="mb-6">
          <Title level={2} className="mb-2">
            欢迎回来，{user?.username}！
          </Title>
          <Text type="secondary">
            今天也要努力学习哦 📚
          </Text>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]} className="mb-6">
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="知识库"
                value={0}
                prefix={<FolderOutlined className="text-blue-500" />}
                suffix="个"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="文档"
                value={0}
                prefix={<FileTextOutlined className="text-green-500" />}
                suffix="份"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="学习记录"
                value={0}
                prefix={<BookOutlined className="text-orange-500" />}
                suffix="次"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="学习积分"
                value={0}
                prefix={<TrophyOutlined className="text-purple-500" />}
                suffix="分"
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          {/* 快速开始 */}
          <Col xs={24} lg={12}>
            <Card title="快速开始" className="h-full">
              <Space direction="vertical" size="large" className="w-full">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-blue-600 font-semibold text-sm">1</span>
                  </div>
                  <div>
                    <Title level={5} className="mb-1">创建知识库</Title>
                    <Text type="secondary">
                      创建您的第一个知识库来组织学习材料
                    </Text>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-green-600 font-semibold text-sm">2</span>
                  </div>
                  <div>
                    <Title level={5} className="mb-1">上传文档</Title>
                    <Text type="secondary">
                      上传PDF、EPUB、TXT或MD格式的文档
                    </Text>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-orange-600 font-semibold text-sm">3</span>
                  </div>
                  <div>
                    <Title level={5} className="mb-1">开始学习</Title>
                    <Text type="secondary">
                      系统将自动生成问题帮助您学习文档内容
                    </Text>
                  </div>
                </div>
              </Space>
            </Card>
          </Col>

          {/* 最近活动 */}
          <Col xs={24} lg={12}>
            <Card title="最近活动" className="h-full">
              <div className="text-center py-8">
                <ClockCircleOutlined className="text-4xl text-gray-300 mb-4" />
                <Text type="secondary">暂无学习记录</Text>
                <br />
                <Text type="secondary" className="text-sm">
                  开始学习后，这里会显示您的学习活动
                </Text>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 学习进度 */}
        <Row gutter={[16, 16]} className="mt-4">
          <Col span={24}>
            <Card title="本周学习进度">
              <div className="text-center py-8">
                <BookOutlined className="text-4xl text-gray-300 mb-4" />
                <Text type="secondary">还没有学习数据</Text>
                <br />
                <Text type="secondary" className="text-sm">
                  完成一些学习任务后，这里会显示您的学习进度图表
                </Text>
              </div>
            </Card>
          </Col>
        </Row>
      </div>
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