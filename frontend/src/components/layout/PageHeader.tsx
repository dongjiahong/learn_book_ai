/**
 * Responsive page header component
 */
'use client';

import React from 'react';
import { Typography, Breadcrumb, Space, Button, Grid } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { Container } from './Container';

const { Title, Text } = Typography;
const { useBreakpoint } = Grid;

interface BreadcrumbItem {
  title: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  extra?: React.ReactNode;
  showBack?: boolean;
  onBack?: () => void;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  breadcrumbs,
  extra,
  showBack = false,
  onBack,
  className = '',
}) => {
  const router = useRouter();
  const screens = useBreakpoint();

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      router.back();
    }
  };

  const isMobile = !screens.md;

  return (
    <div className={`bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 ${className}`}>
      <Container>
        <div className="py-4 md:py-6">
          {/* Breadcrumbs */}
          {breadcrumbs && breadcrumbs.length > 0 && (
            <div className="mb-2">
              <Breadcrumb
                items={breadcrumbs.map(item => ({
                  title: item.href ? (
                    <a 
                      href={item.href}
                      className="text-gray-500 hover:text-blue-500 dark:text-gray-400 dark:hover:text-blue-400"
                    >
                      {item.title}
                    </a>
                  ) : (
                    <span className="text-gray-800 dark:text-gray-200">
                      {item.title}
                    </span>
                  ),
                }))}
                className="text-sm"
              />
            </div>
          )}

          {/* Header content */}
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 min-w-0 flex-1">
              {/* Back button */}
              {showBack && (
                <Button
                  type="text"
                  icon={<ArrowLeftOutlined />}
                  onClick={handleBack}
                  className="mt-1 hover:bg-gray-100 dark:hover:bg-gray-800"
                  size={isMobile ? 'small' : 'middle'}
                />
              )}

              {/* Title and subtitle */}
              <div className="min-w-0 flex-1">
                <Title 
                  level={isMobile ? 3 : 2} 
                  className="!mb-0 text-gray-900 dark:text-gray-100 truncate"
                  style={{ fontSize: isMobile ? '20px' : '28px' }}
                >
                  {title}
                </Title>
                {subtitle && (
                  <Text 
                    type="secondary" 
                    className="block mt-1 text-sm md:text-base"
                  >
                    {subtitle}
                  </Text>
                )}
              </div>
            </div>

            {/* Extra content */}
            {extra && (
              <div className="ml-4 flex-shrink-0">
                {isMobile ? (
                  <Space direction="vertical" size="small">
                    {extra}
                  </Space>
                ) : (
                  <Space size="middle">
                    {extra}
                  </Space>
                )}
              </div>
            )}
          </div>
        </div>
      </Container>
    </div>
  );
};