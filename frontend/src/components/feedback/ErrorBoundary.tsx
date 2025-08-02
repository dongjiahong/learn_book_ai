/**
 * Error boundary component for catching and displaying errors
 */
'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography, Space } from 'antd';
import { BugOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons';

const { Paragraph, Text } = Typography;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ error, errorInfo });
    
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by boundary:', error, errorInfo);
    }

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <div className="max-w-md w-full">
            <Result
              status="error"
              icon={<BugOutlined className="text-red-500" />}
              title="出现了一些问题"
              subTitle="应用程序遇到了意外错误，请尝试刷新页面或返回首页。"
              extra={
                <Space direction="vertical" className="w-full">
                  <Space wrap className="justify-center">
                    <Button 
                      type="primary" 
                      icon={<ReloadOutlined />}
                      onClick={this.handleReload}
                    >
                      刷新页面
                    </Button>
                    <Button 
                      icon={<HomeOutlined />}
                      onClick={this.handleGoHome}
                    >
                      返回首页
                    </Button>
                    <Button 
                      type="dashed"
                      onClick={this.handleRetry}
                    >
                      重试
                    </Button>
                  </Space>
                  
                  {/* Error details in development */}
                  {process.env.NODE_ENV === 'development' && this.state.error && (
                    <div className="mt-6 p-4 bg-gray-100 rounded-lg text-left">
                      <Text strong className="block mb-2">错误详情（开发模式）：</Text>
                      <Paragraph className="text-xs font-mono text-red-600 mb-2">
                        {this.state.error.message}
                      </Paragraph>
                      {this.state.errorInfo && (
                        <details className="text-xs">
                          <summary className="cursor-pointer text-gray-600 mb-2">
                            查看堆栈跟踪
                          </summary>
                          <pre className="whitespace-pre-wrap text-gray-500 overflow-auto max-h-40">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </details>
                      )}
                    </div>
                  )}
                </Space>
              }
            />
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// HOC for wrapping components with error boundary
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: ErrorInfo) => void
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback} onError={onError}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};