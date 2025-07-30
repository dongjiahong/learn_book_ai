'use client';

import React from 'react';
import { Card, Typography, Button, Space } from 'antd';
import { BookOutlined, ClockCircleOutlined, TrophyOutlined } from '@ant-design/icons';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';

const { Title, Text } = Typography;

function ReviewContent() {
    return (
        <MainLayout>
            <div className="p-6">
                <div className="mb-6">
                    <Title level={2} className="mb-2">
                        复习系统
                    </Title>
                    <Text type="secondary">
                        基于记忆曲线的智能复习安排
                    </Text>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* 今日复习 */}
                    <Card title="今日复习" className="h-fit">
                        <div className="text-center py-8">
                            <ClockCircleOutlined className="text-4xl text-blue-500 mb-4" />
                            <Title level={4}>暂无复习任务</Title>
                            <Text type="secondary">
                                完成一些学习后，系统会根据记忆曲线为您安排复习
                            </Text>
                        </div>
                    </Card>

                    {/* 复习统计 */}
                    <Card title="复习统计" className="h-fit">
                        <Space direction="vertical" size="large" className="w-full">
                            <div className="flex justify-between items-center">
                                <Text>本周复习次数</Text>
                                <Text strong>0 次</Text>
                            </div>
                            <div className="flex justify-between items-center">
                                <Text>复习正确率</Text>
                                <Text strong>-- %</Text>
                            </div>
                            <div className="flex justify-between items-center">
                                <Text>累计复习积分</Text>
                                <Text strong className="text-orange-500">0 分</Text>
                            </div>
                        </Space>
                    </Card>

                    {/* 复习计划 */}
                    <Card title="复习计划" className="h-fit">
                        <div className="text-center py-8">
                            <BookOutlined className="text-4xl text-green-500 mb-4" />
                            <Title level={4}>智能复习计划</Title>
                            <Text type="secondary" className="block mb-4">
                                系统会根据您的学习情况和记忆曲线，智能安排复习时间
                            </Text>
                            <Button type="primary" disabled>
                                即将推出
                            </Button>
                        </div>
                    </Card>

                    {/* 成就系统 */}
                    <Card title="学习成就" className="h-fit">
                        <div className="text-center py-8">
                            <TrophyOutlined className="text-4xl text-yellow-500 mb-4" />
                            <Title level={4}>学习徽章</Title>
                            <Text type="secondary" className="block mb-4">
                                完成学习目标，获得专属徽章和奖励
                            </Text>
                            <Button type="primary" disabled>
                                即将推出
                            </Button>
                        </div>
                    </Card>
                </div>

                {/* 功能介绍 */}
                <Card title="复习系统功能" className="mt-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <div className="text-center">
                            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                                <ClockCircleOutlined className="text-blue-600 text-xl" />
                            </div>
                            <Title level={5}>智能提醒</Title>
                            <Text type="secondary" className="text-sm">
                                根据记忆曲线，在最佳时机提醒您复习
                            </Text>
                        </div>
                        <div className="text-center">
                            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                                <BookOutlined className="text-green-600 text-xl" />
                            </div>
                            <Title level={5}>个性化复习</Title>
                            <Text type="secondary" className="text-sm">
                                根据您的掌握程度，调整复习频率和难度
                            </Text>
                        </div>
                        <div className="text-center">
                            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-3">
                                <TrophyOutlined className="text-orange-600 text-xl" />
                            </div>
                            <Title level={5}>成就激励</Title>
                            <Text type="secondary" className="text-sm">
                                完成复习目标，获得积分和成就徽章
                            </Text>
                        </div>
                    </div>
                </Card>
            </div>
        </MainLayout>
    );
}

export default function ReviewPage() {
    return (
        <ProtectedRoute>
            <ReviewContent />
        </ProtectedRoute>
    );
}