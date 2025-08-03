/**
 * 全局认证错误处理 Hook
 */
import { useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { message } from 'antd';
import { useAuth } from './useAuth';

interface AuthErrorDetail {
  message: string;
  endpoint: string;
  status: number;
}

export const useAuthErrorHandler = () => {
  const router = useRouter();
  const { logout, tokens, isAuthenticated } = useAuth();

  // 处理认证失效
  const handleUnauthorized = useCallback(async (event: CustomEvent<AuthErrorDetail>) => {
    const { message: errorMessage, endpoint } = event.detail;
    
    console.warn('Authentication failed:', { errorMessage, endpoint });
    
    // 显示友好的错误提示
    message.error('登录已过期，请重新登录');
    
    // 清除认证状态
    logout();
    
    // 延迟跳转，让用户看到提示信息
    setTimeout(() => {
      // 保存当前页面路径，登录后可以跳转回来
      const currentPath = window.location.pathname;
      if (currentPath !== '/auth/login') {
        sessionStorage.setItem('redirectAfterLogin', currentPath);
      }
      
      router.push('/auth/login');
    }, 1500);
  }, [logout, router]);

  // 处理 token 刷新需求
  const handleTokenRefreshNeeded = useCallback(async () => {
    if (!tokens?.refresh_token || !isAuthenticated) {
      return;
    }

    try {
      // 这里可以调用 refresh token 的逻辑
      // 由于你的 useAuth hook 已经有自动刷新机制，这里主要是触发刷新
      console.log('Token refresh triggered by API error');
    } catch (error) {
      console.error('Token refresh failed:', error);
      // 如果刷新失败，触发登出
      handleUnauthorized(new CustomEvent('auth:unauthorized', {
        detail: {
          message: 'Token refresh failed',
          endpoint: 'token-refresh',
          status: 401
        }
      }));
    }
  }, [tokens, isAuthenticated, handleUnauthorized]);

  useEffect(() => {
    // 监听全局认证错误事件
    window.addEventListener('auth:unauthorized', handleUnauthorized as EventListener);
    window.addEventListener('auth:token-refresh-needed', handleTokenRefreshNeeded);

    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized as EventListener);
      window.removeEventListener('auth:token-refresh-needed', handleTokenRefreshNeeded);
    };
  }, [handleUnauthorized, handleTokenRefreshNeeded]);

  return {
    handleUnauthorized,
    handleTokenRefreshNeeded,
  };
};