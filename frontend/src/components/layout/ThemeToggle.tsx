/**
 * Theme toggle component for switching between light, dark, and auto modes
 */
'use client';

import React from 'react';
import { Button, Dropdown, Space, Typography } from 'antd';
import { 
  SunOutlined, 
  MoonOutlined, 
  DesktopOutlined,
  CheckOutlined 
} from '@ant-design/icons';
import { useTheme } from '@/contexts/ThemeContext';

const { Text } = Typography;

interface ThemeToggleProps {
  size?: 'small' | 'middle' | 'large';
  showText?: boolean;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  size = 'middle', 
  showText = false 
}) => {
  const { mode, setMode, isDark } = useTheme();

  const themeOptions = [
    {
      key: 'light',
      icon: <SunOutlined />,
      label: '浅色主题',
      description: '始终使用浅色主题',
    },
    {
      key: 'dark',
      icon: <MoonOutlined />,
      label: '深色主题',
      description: '始终使用深色主题',
    },
    {
      key: 'auto',
      icon: <DesktopOutlined />,
      label: '跟随系统',
      description: '根据系统设置自动切换',
    },
  ];

  const menuItems = themeOptions.map(option => ({
    key: option.key,
    icon: (
      <Space>
        {option.icon}
        {mode === option.key && <CheckOutlined className="text-blue-500" />}
      </Space>
    ),
    label: (
      <div>
        <div className="font-medium">{option.label}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          {option.description}
        </div>
      </div>
    ),
    onClick: () => setMode(option.key as 'light' | 'dark' | 'auto'),
  }));

  const getCurrentIcon = () => {
    switch (mode) {
      case 'light':
        return <SunOutlined />;
      case 'dark':
        return <MoonOutlined />;
      case 'auto':
        return <DesktopOutlined />;
      default:
        return isDark ? <MoonOutlined /> : <SunOutlined />;
    }
  };

  const getCurrentLabel = () => {
    switch (mode) {
      case 'light':
        return '浅色';
      case 'dark':
        return '深色';
      case 'auto':
        return '自动';
      default:
        return isDark ? '深色' : '浅色';
    }
  };

  return (
    <Dropdown
      menu={{ items: menuItems }}
      placement="bottomRight"
      arrow
      trigger={['click']}
    >
      <Button
        type="text"
        size={size}
        icon={getCurrentIcon()}
        className="hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      >
        {showText && (
          <Text className="ml-1 text-gray-600 dark:text-gray-300">
            {getCurrentLabel()}
          </Text>
        )}
      </Button>
    </Dropdown>
  );
};