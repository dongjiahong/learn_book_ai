'use client';

import React, { useState } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  FolderOutlined,
  FileTextOutlined,
  BookOutlined,
  DashboardOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: <Link href="/dashboard">仪表板</Link>,
    },
    {
      key: '/knowledge-bases',
      icon: <FolderOutlined />,
      label: <Link href="/knowledge-bases">知识库管理</Link>,
    },
    {
      key: '/questions',
      icon: <FileTextOutlined />,
      label: <Link href="/questions">智能学习</Link>,
    },
    {
      key: '/review',
      icon: <BookOutlined />,
      label: <Link href="/review">复习系统</Link>,
    },
  ];

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <Layout className="min-h-screen">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="bg-white shadow-md"
        width={240}
      >
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <BookOutlined className="text-white text-lg" />
            </div>
            {!collapsed && (
              <div>
                <div className="font-semibold text-gray-800">RAG学习平台</div>
                <div className="text-xs text-gray-500">智能学习助手</div>
              </div>
            )}
          </div>
        </div>
        
        <Menu
          mode="inline"
          selectedKeys={[pathname]}
          items={menuItems}
          className="border-none"
          style={{ height: 'calc(100vh - 80px)', borderRight: 0 }}
        />
      </Sider>
      
      <Layout>
        <Header className="bg-white shadow-sm px-4 flex justify-between items-center">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            className="text-lg"
          />
          
          <Dropdown
            menu={{ items: userMenuItems }}
            placement="bottomRight"
            arrow
          >
            <Space className="cursor-pointer hover:bg-gray-50 px-3 py-2 rounded-lg">
              <Avatar size="small" icon={<UserOutlined />} />
              <div className="hidden sm:block">
                <Text strong>{user?.username}</Text>
                <br />
                <Text type="secondary" className="text-xs">
                  {user?.email}
                </Text>
              </div>
            </Space>
          </Dropdown>
        </Header>
        
        <Content className="bg-gray-50 overflow-auto">
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}