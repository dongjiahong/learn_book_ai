/**
 * Notification provider for global notifications
 */
'use client';

import React, { createContext, useContext } from 'react';
import { notification } from 'antd';
import type { NotificationInstance } from 'antd/es/notification/interface';

interface NotificationContextType {
  success: (message: string, description?: string) => void;
  error: (message: string, description?: string) => void;
  warning: (message: string, description?: string) => void;
  info: (message: string, description?: string) => void;
  loading: (message: string, description?: string, duration?: number) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
  children: React.ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [api, contextHolder] = notification.useNotification({
    placement: 'topRight',
    duration: 4.5,
    maxCount: 3,
    rtl: false,
  });

  const success = (message: string, description?: string) => {
    api.success({
      message,
      description,
      placement: 'topRight',
    });
  };

  const error = (message: string, description?: string) => {
    api.error({
      message,
      description,
      placement: 'topRight',
      duration: 6, // Longer duration for errors
    });
  };

  const warning = (message: string, description?: string) => {
    api.warning({
      message,
      description,
      placement: 'topRight',
    });
  };

  const info = (message: string, description?: string) => {
    api.info({
      message,
      description,
      placement: 'topRight',
    });
  };

  const loading = (message: string, description?: string, duration = 0) => {
    api.info({
      message,
      description,
      placement: 'topRight',
      duration,
      icon: <div className="animate-spin">⏳</div>,
    });
  };

  const value: NotificationContextType = {
    success,
    error,
    warning,
    info,
    loading,
  };

  return (
    <NotificationContext.Provider value={value}>
      {contextHolder}
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};