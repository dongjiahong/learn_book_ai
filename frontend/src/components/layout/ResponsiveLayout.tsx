/**
 * Responsive layout component with mobile-first design
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography, Drawer, Grid } from 'antd';
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
  EditOutlined,
  HistoryOutlined,
  SyncOutlined,
  BulbOutlined,
  ExportOutlined,
  MoonOutlined,
  SunOutlined,
  DesktopOutlined,
} from '@ant-design/icons';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/contexts/ThemeContext';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;
const { useBreakpoint } = Grid;

interface ResponsiveLayoutProps {
  children: React.ReactNode;
}

export function ResponsiveLayout({ children }: ResponsiveLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const { user, logout } = useAuth();
  const { setMode, isDark } = useTheme();
  const router = useRouter();
  const pathname = usePathname();
  const screens = useBreakpoint();

  // Determine if we're on mobile
  const isMobile = !screens.md;

  // Auto-collapse sidebar on mobile
  useEffect(() => {
    if (isMobile) {
      setCollapsed(true);
    }
  }, [isMobile]);

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };

  const handleThemeChange = (newMode: 'light' | 'dark' | 'auto') => {
    setMode(newMode);
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
      key: '/knowledge-points',
      icon: <BulbOutlined />,
      label: <Link href="/knowledge-points">知识点管理</Link>,
    },
    {
      key: '/questions',
      icon: <FileTextOutlined />,
      label: <Link href="/questions">问题管理</Link>,
    },
    {
      key: '/practice',
      icon: <EditOutlined />,
      label: <Link href="/practice">答题练习</Link>,
    },
    {
      key: '/learning-records',
      icon: <HistoryOutlined />,
      label: <Link href="/learning-records">学习记录</Link>,
    },
    {
      key: '/review',
      icon: <SyncOutlined />,
      label: <Link href="/review">复习系统</Link>,
    },
    {
      key: '/anki-export',
      icon: <ExportOutlined />,
      label: <Link href="/anki-export">Anki导出</Link>,
    },
  ];

  // 主题切换菜单
  const themeMenuItems = [
    {
      key: 'light',
      icon: <SunOutlined />,
      label: '浅色主题',
      onClick: () => handleThemeChange('light'),
    },
    {
      key: 'dark',
      icon: <MoonOutlined />,
      label: '深色主题',
      onClick: () => handleThemeChange('dark'),
    },
    {
      key: 'auto',
      icon: <DesktopOutlined />,
      label: '跟随系统',
      onClick: () => handleThemeChange('auto'),
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
      key: 'theme',
      icon: isDark ? <MoonOutlined /> : <SunOutlined />,
      label: '主题设置',
      children: themeMenuItems,
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

  // 侧边栏内容
  const sidebarContent = (
    <>
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <BookOutlined className="text-white text-lg" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="font-semibold text-gray-800 dark:text-gray-200 truncate">
                RAG学习平台
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                智能学习助手
              </div>
            </div>
          )}
        </div>
      </div>

      <Menu
        mode="inline"
        selectedKeys={[pathname]}
        items={menuItems}
        className="border-none flex-1"
        style={{ 
          height: isMobile ? 'auto' : 'calc(100vh - 80px)', 
          borderRight: 0,
          overflow: 'auto'
        }}
        onClick={() => {
          if (isMobile) {
            setMobileDrawerOpen(false);
          }
        }}
      />
    </>
  );

  return (
    <Layout className="min-h-screen">
      {/* Desktop Sidebar */}
      {!isMobile && (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          className="bg-white dark:bg-gray-900 shadow-md"
          width={240}
          collapsedWidth={64}
        >
          {sidebarContent}
        </Sider>
      )}

      {/* Mobile Drawer */}
      {isMobile && (
        <Drawer
          title={null}
          placement="left"
          closable={false}
          onClose={() => setMobileDrawerOpen(false)}
          open={mobileDrawerOpen}
          styles={{ body: { padding: 0 } }}
          width={240}
          className="mobile-drawer"
        >
          {sidebarContent}
        </Drawer>
      )}

      <Layout>
        <Header className="bg-white dark:bg-gray-900 shadow-sm px-4 flex justify-between items-center sticky top-0 z-10">
          <div className="flex items-center space-x-2">
            <Button
              type="text"
              icon={
                isMobile ? (
                  <MenuUnfoldOutlined />
                ) : collapsed ? (
                  <MenuUnfoldOutlined />
                ) : (
                  <MenuFoldOutlined />
                )
              }
              onClick={() => {
                if (isMobile) {
                  setMobileDrawerOpen(true);
                } else {
                  setCollapsed(!collapsed);
                }
              }}
              className="text-lg hover:bg-gray-100 dark:hover:bg-gray-800"
            />
            
            {/* Mobile title */}
            {isMobile && (
              <div className="flex items-center space-x-2">
                <div className="w-6 h-6 bg-blue-500 rounded flex items-center justify-center">
                  <BookOutlined className="text-white text-sm" />
                </div>
                <Text strong className="text-gray-800 dark:text-gray-200">
                  RAG学习平台
                </Text>
              </div>
            )}
          </div>

          {user ? (
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              arrow
              trigger={['click']}
            >
              <div className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 px-3 py-2 rounded-lg transition-colors">
                <Space align="center">
                  <Avatar size="small" icon={<UserOutlined />} />
                  {!isMobile && (
                    <div className="flex flex-col items-start">
                      <Text strong className="text-gray-800 dark:text-gray-200 text-sm leading-tight">
                        {user.username}
                      </Text>
                      <Text type="secondary" className="text-xs leading-tight">
                        {user.email}
                      </Text>
                    </div>
                  )}
                </Space>
              </div>
            </Dropdown>
          ) : (
            <Button 
              type="primary" 
              onClick={() => router.push('/auth/login')}
              size="small"
            >
              登录
            </Button>
          )}
        </Header>

        <Content className="bg-gray-50 dark:bg-gray-900 overflow-auto">
          <div className="p-4 md:p-6">
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}