/**
 * 认证重试机制
 * 处理 token 过期时的自动重试逻辑
 */

interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  shouldRetry: (error: Error) => boolean;
}

const defaultConfig: RetryConfig = {
  maxRetries: 1,
  retryDelay: 1000,
  shouldRetry: (error: Error) => error.message === 'UNAUTHORIZED',
};

export class AuthRetryManager {
  private static instance: AuthRetryManager;
  private refreshPromise: Promise<string | null> | null = null;

  static getInstance(): AuthRetryManager {
    if (!AuthRetryManager.instance) {
      AuthRetryManager.instance = new AuthRetryManager();
    }
    return AuthRetryManager.instance;
  }

  /**
   * 执行带有认证重试的请求
   */
  async executeWithRetry<T>(
    requestFn: (token: string) => Promise<T>,
    token: string,
    config: Partial<RetryConfig> = {}
  ): Promise<T> {
    const finalConfig = { ...defaultConfig, ...config };
    let lastError: Error;

    for (let attempt = 0; attempt <= finalConfig.maxRetries; attempt++) {
      try {
        return await requestFn(token);
      } catch (error) {
        lastError = error as Error;

        // 如果不是需要重试的错误，直接抛出
        if (!finalConfig.shouldRetry(lastError)) {
          throw lastError;
        }

        // 如果是最后一次尝试，抛出错误
        if (attempt === finalConfig.maxRetries) {
          throw lastError;
        }

        // 尝试刷新 token
        const newToken = await this.refreshTokenIfNeeded();
        if (newToken && newToken !== token) {
          token = newToken;
          // 等待一段时间后重试
          await new Promise(resolve => setTimeout(resolve, finalConfig.retryDelay));
        } else {
          // 无法获取新 token，抛出错误
          throw lastError;
        }
      }
    }

    throw lastError!;
  }

  /**
   * 刷新 token（防止并发刷新）
   */
  private async refreshTokenIfNeeded(): Promise<string | null> {
    // 如果已经有刷新请求在进行中，等待它完成
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performTokenRefresh();
    
    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      this.refreshPromise = null;
    }
  }

  /**
   * 执行实际的 token 刷新
   */
  private async performTokenRefresh(): Promise<string | null> {
    try {
      // 从存储中获取 refresh token
      const authData = localStorage.getItem('auth-storage');
      if (!authData) {
        return null;
      }

      const parsed = JSON.parse(authData);
      const refreshToken = parsed.state?.tokens?.refresh_token;
      
      if (!refreshToken) {
        return null;
      }

      // 这里需要调用你的 API 刷新 token
      // 由于 apiClient 可能会导致循环依赖，这里直接使用 fetch
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://172.18.3.1:8800'}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const newTokens = await response.json();
      
      // 更新存储中的 tokens
      const updatedAuthData = {
        ...parsed,
        state: {
          ...parsed.state,
          tokens: newTokens,
        },
      };
      
      localStorage.setItem('auth-storage', JSON.stringify(updatedAuthData));
      
      return newTokens.access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return null;
    }
  }
}

export const authRetryManager = AuthRetryManager.getInstance();