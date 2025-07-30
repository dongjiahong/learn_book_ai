/**
 * Loading spinner component with responsive design
 */
'use client';

import React from 'react';
import { Spin, Typography, Grid } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { useBreakpoint } = Grid;

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large';
  text?: string;
  fullScreen?: boolean;
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'default',
  text,
  fullScreen = false,
  className = '',
}) => {
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  const getSpinSize = () => {
    if (isMobile) {
      return size === 'large' ? 'default' : size;
    }
    return size;
  };

  const getIconSize = () => {
    switch (getSpinSize()) {
      case 'small':
        return 16;
      case 'large':
        return 32;
      default:
        return 24;
    }
  };

  const customIcon = (
    <LoadingOutlined 
      style={{ fontSize: getIconSize() }} 
      spin 
      className="text-blue-500"
    />
  );

  const content = (
    <div className="flex flex-col items-center justify-center space-y-3">
      <Spin 
        indicator={customIcon} 
        size={getSpinSize()}
      />
      {text && (
        <Text 
          type="secondary" 
          className={`text-center ${isMobile ? 'text-sm' : 'text-base'}`}
        >
          {text}
        </Text>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className={`fixed inset-0 bg-white dark:bg-gray-900 bg-opacity-80 dark:bg-opacity-80 backdrop-blur-sm z-50 flex items-center justify-center ${className}`}>
        {content}
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center p-8 ${className}`}>
      {content}
    </div>
  );
};

// Page loading component
export const PageLoading: React.FC<{ text?: string }> = ({ text = '加载中...' }) => {
  return (
    <LoadingSpinner 
      size="large" 
      text={text} 
      className="min-h-[400px]"
    />
  );
};

// Inline loading component
export const InlineLoading: React.FC<{ text?: string }> = ({ text }) => {
  return (
    <div className="flex items-center justify-center space-x-2 py-4">
      <Spin size="small" />
      {text && (
        <Text type="secondary" className="text-sm">
          {text}
        </Text>
      )}
    </div>
  );
};