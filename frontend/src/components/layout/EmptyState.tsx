/**
 * Empty state component with responsive design
 */
'use client';

import React from 'react';
import { Empty, Button, Typography, Grid } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { useBreakpoint } = Grid;

interface EmptyStateProps {
  title?: string;
  description?: string;
  image?: React.ReactNode;
  action?: {
    text: string;
    onClick: () => void;
    icon?: React.ReactNode;
    type?: 'primary' | 'default';
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = '暂无数据',
  description,
  image,
  action,
  className = '',
}) => {
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  return (
    <div className={`flex items-center justify-center py-12 ${className}`}>
      <div className="text-center max-w-md mx-auto px-4">
        <Empty
          image={image || Empty.PRESENTED_IMAGE_SIMPLE}
          styles={{
            image: {
              height: isMobile ? 80 : 120,
              marginBottom: isMobile ? 16 : 24,
            }
          }}
          description={
            <div className="space-y-2">
              <Text
                className={`block font-medium text-gray-800 ${isMobile ? 'text-base' : 'text-lg'
                  }`}
              >
                {title}
              </Text>
              {description && (
                <Text
                  type="secondary"
                  className={`block ${isMobile ? 'text-sm' : 'text-base'}`}
                >
                  {description}
                </Text>
              )}
            </div>
          }
        >
          {action && (
            <Button
              type={action.type || 'primary'}
              icon={action.icon || <PlusOutlined />}
              onClick={action.onClick}
              size={isMobile ? 'middle' : 'large'}
              className="mt-4"
            >
              {action.text}
            </Button>
          )}
        </Empty>
      </div>
    </div>
  );
};