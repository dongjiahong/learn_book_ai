/**
 * API client for authentication and other backend services
 */
import { AuthTokens, User } from '@/stores/authStore';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8800';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  private async authenticatedRequest<T>(
    endpoint: string,
    token: string,
    options: RequestInit = {}
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      },
    });
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<AuthTokens> {
    return this.request<AuthTokens>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async register(userData: RegisterRequest): Promise<User> {
    return this.request<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async refreshToken(refreshData: RefreshTokenRequest): Promise<AuthTokens> {
    return this.request<AuthTokens>('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify(refreshData),
    });
  }

  async getCurrentUser(token: string): Promise<User> {
    return this.authenticatedRequest<User>('/api/auth/me', token);
  }

  async logout(token: string): Promise<{ message: string }> {
    return this.authenticatedRequest<{ message: string }>('/api/auth/logout', token, {
      method: 'POST',
    });
  }
}

export const apiClient = new ApiClient();