/**
 * App providers for React Query and other global providers
 */
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, App } from 'antd';
import { useState } from 'react';
import zhCN from 'antd/locale/zh_CN';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';
import { NotificationProvider } from '@/components/feedback/NotificationProvider';
import { KeyboardShortcutProvider } from '@/components/providers/KeyboardShortcutProvider';
import { ErrorBoundary } from '@/components/feedback/ErrorBoundary';
import { AuthErrorHandler } from '@/components/auth/AuthErrorHandler';

interface ProvidersProps {
  children: React.ReactNode;
}

// Inner component that uses theme context
const ThemedConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { antdTheme } = useTheme();

  return (
    <ConfigProvider
      locale={zhCN}
      theme={antdTheme}
      wave={{ disabled: true }}
    >
      <App>
        {children}
      </App>
    </ConfigProvider>
  );
};

export const Providers: React.FC<ProvidersProps> = ({ children }) => {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            retry: (failureCount, error: unknown) => {
              // Don't retry on 4xx errors
              const errorWithStatus = error as { status?: number };
              if (errorWithStatus?.status && errorWithStatus.status >= 400 && errorWithStatus.status < 500) {
                return false;
              }
              return failureCount < 3;
            },
          },
        },
      })
  );

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <ThemedConfigProvider>
            <AuthErrorHandler>
              <NotificationProvider>
                <KeyboardShortcutProvider>
                  {children}
                </KeyboardShortcutProvider>
              </NotificationProvider>
            </AuthErrorHandler>
          </ThemedConfigProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};