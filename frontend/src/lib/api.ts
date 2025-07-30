/**
 * API client for authentication and other backend services
 */
import { AuthTokens, User } from '@/stores/authStore';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://172.18.3.1:8800';

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

// Knowledge Base interfaces
export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  user_id: number;
  created_at: string;
  updated_at: string;
  document_count?: number;
}

export interface KnowledgeBaseCreate {
  name: string;
  description?: string;
}

export interface KnowledgeBaseUpdate {
  name?: string;
  description?: string;
}

export interface KnowledgeBaseListResponse {
  knowledge_bases: KnowledgeBase[];
  total: number;
  page: number;
  page_size: number;
}

export interface KnowledgeBaseDetailResponse extends KnowledgeBase {
  documents: Document[];
}

// Document interfaces
export interface Document {
  id: number;
  knowledge_base_id: number;
  filename: string;
  file_path: string;
  file_type: string;
  file_size: number;
  processed: boolean;
  created_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  document?: Document;
}

// Question interfaces
export interface Question {
  id: number;
  question_text: string;
  context?: string;
  difficulty_level: number;
  document_id: number;
  document_name?: string;
  knowledge_base_id?: number;
  knowledge_base_name?: string;
  created_at: string;
}

export interface QuestionListResponse {
  success: boolean;
  questions: Question[];
  count: number;
  document_id?: number;
  document_name?: string;
  knowledge_base_id?: number;
  knowledge_base_name?: string;
}

export interface QuestionGenerateRequest {
  num_questions?: number;
  min_quality_score?: number;
}

export interface QuestionGenerateResponse {
  success: boolean;
  message?: string;
  questions_generated?: number;
  error?: string;
}

export interface QuestionUpdateRequest {
  question_text?: string;
  context?: string;
  difficulty_level?: number;
}

export interface DifficultyDistribution {
  success: boolean;
  knowledge_base_id?: number;
  total_questions: number;
  distribution: Record<string, number>;
  difficulty_labels: Record<string, string>;
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

  // Knowledge Base endpoints
  async getKnowledgeBases(
    token: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<KnowledgeBaseListResponse> {
    return this.authenticatedRequest<KnowledgeBaseListResponse>(
      `/api/knowledge-bases?skip=${skip}&limit=${limit}`,
      token
    );
  }

  async getKnowledgeBase(token: string, id: number): Promise<KnowledgeBaseDetailResponse> {
    return this.authenticatedRequest<KnowledgeBaseDetailResponse>(
      `/api/knowledge-bases/${id}`,
      token
    );
  }

  async createKnowledgeBase(
    token: string,
    data: KnowledgeBaseCreate
  ): Promise<KnowledgeBase> {
    return this.authenticatedRequest<KnowledgeBase>('/api/knowledge-bases', token, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateKnowledgeBase(
    token: string,
    id: number,
    data: KnowledgeBaseUpdate
  ): Promise<KnowledgeBase> {
    return this.authenticatedRequest<KnowledgeBase>(`/api/knowledge-bases/${id}`, token, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteKnowledgeBase(token: string, id: number): Promise<{ message: string }> {
    return this.authenticatedRequest<{ message: string }>(`/api/knowledge-bases/${id}`, token, {
      method: 'DELETE',
    });
  }

  // Document endpoints
  async getDocuments(
    token: string,
    knowledgeBaseId?: number,
    skip: number = 0,
    limit: number = 100
  ): Promise<DocumentListResponse> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    
    if (knowledgeBaseId) {
      params.append('knowledge_base_id', knowledgeBaseId.toString());
    }

    return this.authenticatedRequest<DocumentListResponse>(
      `/api/documents?${params.toString()}`,
      token
    );
  }

  async getDocument(token: string, id: number): Promise<Document> {
    return this.authenticatedRequest<Document>(`/api/documents/${id}`, token);
  }

  async uploadDocument(
    token: string,
    knowledgeBaseId: number,
    file: File
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.authenticatedRequest<DocumentUploadResponse>(
      `/api/documents/upload?knowledge_base_id=${knowledgeBaseId}`,
      token,
      {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type for FormData, let browser set it with boundary
        },
      }
    );
  }

  async deleteDocument(token: string, id: number): Promise<{ message: string }> {
    return this.authenticatedRequest<{ message: string }>(`/api/documents/${id}`, token, {
      method: 'DELETE',
    });
  }

  async getDocumentContent(token: string, id: number): Promise<{
    document_id: number;
    filename: string;
    file_type: string;
    content: string;
    truncated: boolean;
  }> {
    return this.authenticatedRequest(`/api/documents/${id}/content`, token);
  }

  async getDocumentProcessingStatus(token: string, id: number): Promise<{
    document_id: number;
    processed: boolean;
    processing_progress?: number;
    error_message?: string;
  }> {
    return this.authenticatedRequest(`/api/documents/${id}/processing-status`, token);
  }

  async processDocument(token: string, id: number): Promise<{ message: string }> {
    return this.authenticatedRequest(`/api/documents/${id}/process`, token, {
      method: 'POST',
    });
  }

  async getProcessingQueueStatus(token: string): Promise<{
    is_running: boolean;
    queue_size: number;
    total_tasks: number;
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  }> {
    return this.authenticatedRequest('/api/processing/queue-status', token);
  }

  // Question endpoints
  async generateQuestionsForDocument(
    token: string,
    documentId: number,
    options: QuestionGenerateRequest = {}
  ): Promise<QuestionGenerateResponse> {
    const params = new URLSearchParams();
    if (options.num_questions) params.append('num_questions', options.num_questions.toString());
    if (options.min_quality_score) params.append('min_quality_score', options.min_quality_score.toString());

    return this.authenticatedRequest(
      `/api/questions/generate/document/${documentId}?${params.toString()}`,
      token,
      { method: 'POST' }
    );
  }

  async generateQuestionsForKnowledgeBase(
    token: string,
    knowledgeBaseId: number,
    options: { num_questions_per_document?: number; min_quality_score?: number } = {}
  ): Promise<QuestionGenerateResponse> {
    const params = new URLSearchParams();
    if (options.num_questions_per_document) {
      params.append('num_questions_per_document', options.num_questions_per_document.toString());
    }
    if (options.min_quality_score) {
      params.append('min_quality_score', options.min_quality_score.toString());
    }

    return this.authenticatedRequest(
      `/api/questions/generate/knowledge-base/${knowledgeBaseId}?${params.toString()}`,
      token,
      { method: 'POST' }
    );
  }

  async getQuestionsByDocument(
    token: string,
    documentId: number,
    skip: number = 0,
    limit: number = 100
  ): Promise<QuestionListResponse> {
    return this.authenticatedRequest(
      `/api/questions/document/${documentId}?skip=${skip}&limit=${limit}`,
      token
    );
  }

  async getQuestionsByKnowledgeBase(
    token: string,
    knowledgeBaseId: number,
    skip: number = 0,
    limit: number = 100
  ): Promise<QuestionListResponse> {
    return this.authenticatedRequest(
      `/api/questions/knowledge-base/${knowledgeBaseId}?skip=${skip}&limit=${limit}`,
      token
    );
  }

  async getQuestion(token: string, questionId: number): Promise<{ success: boolean; question: Question }> {
    return this.authenticatedRequest(`/api/questions/${questionId}`, token);
  }

  async updateQuestion(
    token: string,
    questionId: number,
    updates: QuestionUpdateRequest
  ): Promise<{ success: boolean; question: Question }> {
    return this.authenticatedRequest(`/api/questions/${questionId}`, token, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteQuestion(token: string, questionId: number): Promise<{ success: boolean; message: string }> {
    return this.authenticatedRequest(`/api/questions/${questionId}`, token, {
      method: 'DELETE',
    });
  }

  async getDifficultyDistribution(
    token: string,
    knowledgeBaseId?: number
  ): Promise<DifficultyDistribution> {
    const params = knowledgeBaseId ? `?knowledge_base_id=${knowledgeBaseId}` : '';
    return this.authenticatedRequest(`/api/questions/stats/difficulty-distribution${params}`, token);
  }
}

export const apiClient = new ApiClient();