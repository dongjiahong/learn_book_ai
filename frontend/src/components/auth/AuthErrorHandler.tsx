/**
 * 全局认证错误处理组件
 * 在应用根部使用，监听和处理认证相关错误
 */
'use client';

import { useAuthErrorHandler } from '@/hooks/useAuthErrorHandler';

interface AuthErrorHandlerProps {
  children: React.ReactNode;
}

export const AuthErrorHandler: React.FC<AuthErrorHandlerProps> = ({ children }) => {
  // 初始化全局认证错误处理
  useAuthErrorHandler();

  return <>{children}</>;
};