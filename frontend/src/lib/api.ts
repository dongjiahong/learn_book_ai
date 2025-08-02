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
  knowledge_point_count?: number;
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
  knowledge_point_count?: number;
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

// Learning Record Management interfaces
export interface LearningAnswerRecord {
  id: number;
  user_id: number;
  question_id: number;
  user_answer: string;
  reference_answer?: string;
  score?: number;
  feedback?: string;
  answered_at: string;
  question_text?: string;
  document_filename?: string;
  knowledge_base_name?: string;
}

export interface LearningAnswerRecordCreate {
  question_id: number;
  user_answer: string;
  reference_answer?: string;
  score?: number;
  feedback?: string;
}

export interface LearningAnswerRecordUpdate {
  user_answer?: string;
  reference_answer?: string;
  score?: number;
  feedback?: string;
}

export interface ReviewRecord {
  id: number;
  user_id: number;
  content_id: number;
  content_type: 'question' | 'knowledge_point';
  review_count: number;
  last_reviewed?: string;
  next_review?: string;
  ease_factor: number;
  interval_days: number;
  created_at: string;
  updated_at: string;
  content_title?: string;
  content_text?: string;
}

export interface ReviewRecordCreate {
  content_id: number;
  content_type: 'question' | 'knowledge_point';
}

export interface ReviewRecordUpdate {
  ease_factor?: number;
  interval_days?: number;
  next_review?: string;
}

export interface LearningRecordFilter {
  question_id?: number;
  knowledge_base_id?: number;
  document_id?: number;
  score_min?: number;
  score_max?: number;
  date_from?: string;
  date_to?: string;
  content_type?: 'question' | 'knowledge_point';
}

export interface LearningStatistics {
  total_questions_answered: number;
  average_score: number;
  total_study_time: number;
  questions_by_difficulty: Record<number, number>;
  scores_by_date: Array<{
    date: string;
    avg_score: number;
    count: number;
  }>;
  knowledge_base_progress: Array<{
    knowledge_base_name: string;
    total_answered: number;
    avg_score: number;
  }>;
  recent_activity: Array<Record<string, string | number>>;
}

export interface LearningProgressResponse {
  user_id: number;
  statistics: LearningStatistics;
  due_reviews: ReviewRecord[];
  recent_records: LearningAnswerRecord[];
}

export interface LearningRecordSearchRequest {
  query?: string;
  filters?: LearningRecordFilter;
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface BulkDeleteRequest {
  record_ids: number[];
}

// Knowledge Point interfaces
export interface KnowledgePoint {
  id: number;
  document_id: number;
  title: string;
  content: string;
  question?: string;
  importance_level: number;
  created_at: string;
}

// Learning Set interfaces
export interface LearningSet {
  id: number;
  user_id: number;
  knowledge_base_id: number;
  name: string;
  description?: string;
  created_at: string;
  knowledge_base_name?: string;
  total_items?: number;
  mastered_items?: number;
  learning_items?: number;
  new_items?: number;
}

export interface LearningSetCreate {
  name: string;
  description?: string;
  knowledge_base_id: number;
  document_ids: number[];
}

export interface LearningSetUpdate {
  name?: string;
  description?: string;
}

export interface LearningSetItem {
  id: number;
  knowledge_point_id: number;
  added_at: string;
  
  // Knowledge point details
  knowledge_point_title: string;
  knowledge_point_content: string;
  knowledge_point_question?: string;
  knowledge_point_importance: number;
  
  // Learning progress
  mastery_level?: number; // 0: 不会, 1: 学习中, 2: 已学会
  review_count?: number;
  next_review?: string;
}

export type LearningSetListResponse = LearningSet[];

export interface LearningSetDetailResponse extends LearningSet {
  items: LearningSetItem[];
}

export interface LearningRecord {
  id: number;
  user_id: number;
  knowledge_point_id: number;
  learning_set_id: number;
  mastery_level: number;
  review_count: number;
  last_reviewed?: string;
  next_review?: string;
  ease_factor: number;
  interval_days: number;
  created_at: string;
  updated_at: string;
}

export interface LearningRecordCreate {
  knowledge_point_id: number;
  learning_set_id: number;
  mastery_level: number;
}

export interface LearningSessionAnswer {
  knowledge_point_id: number;
  learning_set_id: number;
  mastery_level: 0 | 1 | 2;
}

export interface LearningRecordResponse {
  id: number;
  user_id: number;
  knowledge_point_id: number;
  learning_set_id: number;
  mastery_level: number;
  review_count: number;
  last_reviewed?: string;
  next_review?: string;
  ease_factor: number;
  interval_days: number;
  created_at: string;
  updated_at: string;
  knowledge_point_title?: string;
  knowledge_point_question?: string;
  knowledge_point_content?: string;
  learning_set_name?: string;
}

export interface KnowledgePointUpdate {
  title?: string;
  question?: string;
  content?: string;
  importance_level?: number;
}

export interface KnowledgePointListResponse {
  success: boolean;
  knowledge_points: KnowledgePoint[];
  count: number;
  filters: {
    document_id?: number;
    knowledge_base_id?: number;
    importance_level?: number;
    search_query?: string;
  };
}

export interface KnowledgePointResponse {
  success: boolean;
  knowledge_point: KnowledgePoint;
}

export interface KnowledgePointExtractionResponse {
  success: boolean;
  document_id?: number;
  knowledge_points: KnowledgePoint[];
  count: number;
  message?: string;
  total_requested?: number;
  extraction_stages?: number;
}

export interface KnowledgePointSearchResponse {
  success: boolean;
  query: string;
  results: Array<{
    content: string;
    metadata: {
      knowledge_point_id: number;
      document_id: number;
      title: string;
      importance_level: number;
    };
    distance?: number;
    id: string;
  }>;
  count: number;
}

export interface KnowledgePointStatistics {
  total_knowledge_points: number;
  by_importance_level: Record<number, number>;
  by_document: Array<{
    document_id: number;
    document_name: string;
    count: number;
  }>;
  recent_extractions: Array<{
    date: string;
    count: number;
  }>;
}

export interface KnowledgePointStatisticsResponse {
  success: boolean;
  statistics: KnowledgePointStatistics;
  knowledge_base_id?: number;
}

export interface BatchExtractionResponse {
  success: boolean;
  total_documents: number;
  processed_documents: number;
  total_knowledge_points: number;
  errors: string[];
}

export interface BatchDeleteResponse {
  success: boolean;
  deleted_count: number;
  errors: string[];
}

// Spaced Repetition interfaces
export interface DueReviewItem {
  id: number;
  content_id: number;
  content_type: 'question' | 'knowledge_point';
  content_title: string;
  content_text: string;
  review_count: number;
  last_reviewed?: string;
  next_review: string;
  ease_factor: number;
  interval_days: number;
  is_overdue: boolean;
  days_overdue?: number;
}

export interface ReviewSubmission {
  review_record_id: number;
  quality: number; // 0-5 scale
}

export interface ReviewResponse {
  success: boolean;
  review_record: ReviewRecord;
  next_review: string;
  message: string;
}

export interface ReviewStatistics {
  total_reviews: number;
  reviews_today: number;
  reviews_this_week: number;
  average_quality: number;
  streak_days: number;
  due_today: number;
  overdue: number;
  upcoming_7_days: number;
}

export interface UpcomingReviews {
  reviews_by_date: Array<{
    date: string;
    count: number;
    items: DueReviewItem[];
  }>;
  total_upcoming: number;
}

export interface ReviewReminder {
  id: number;
  user_id: number;
  content_id: number;
  content_type: 'question' | 'knowledge_point';
  content_title: string;
  due_date: string;
  is_overdue: boolean;
  days_overdue?: number;
}

export interface DailySummary {
  date: string;
  reviews_completed: number;
  reviews_due: number;
  average_quality: number;
  time_spent_minutes: number;
  new_items_learned: number;
}

export interface WeeklySummary {
  week_start: string;
  week_end: string;
  total_reviews: number;
  average_daily_reviews: number;
  average_quality: number;
  total_time_minutes: number;
  days_active: number;
  streak_days: number;
}

// Anki Export interfaces
export interface AnkiExportRequest {
  deck_name: string;
  knowledge_base_ids?: number[];
}

export interface CustomAnkiExportRequest {
  deck_name: string;
  knowledge_point_ids: number[];
}

export interface AnkiExportResponse {
  success: boolean;
  export_id: string;
  deck_name: string;
  card_count: number;
  created_at: string;
}

export interface AnkiExportRecord {
  export_id: string;
  deck_name: string;
  card_count: number;
  created_at: string;
}

// Type alias for backward compatibility
export type AnkiExportListItem = AnkiExportRecord;

export interface AnkiExportListResponse {
  exports: AnkiExportRecord[];
  count: number;
}

// Dashboard interfaces
export interface DashboardStats {
  knowledge_bases: number;
  documents: number;
  learning_records: number;
  learning_points: number;
  recent_activity: Array<{
    question_text: string;
    score: number;
    date: string;
  }>;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
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

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<{ user: User; tokens: AuthTokens }> {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async register(userData: RegisterRequest): Promise<{ user: User; tokens: AuthTokens }> {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async refreshToken(refreshData: RefreshTokenRequest): Promise<AuthTokens> {
    return this.request('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify(refreshData),
    });
  }

  async getCurrentUser(token: string): Promise<User> {
    return this.authenticatedRequest('/api/auth/me', token);
  }

  // Knowledge Base endpoints
  async getKnowledgeBases(
    token: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<KnowledgeBaseListResponse> {
    return this.authenticatedRequest(
      `/api/knowledge-bases?page=${page}&page_size=${pageSize}`,
      token
    );
  }

  async getKnowledgeBase(token: string, id: number): Promise<KnowledgeBaseDetailResponse> {
    return this.authenticatedRequest(`/api/knowledge-bases/${id}`, token);
  }

  async createKnowledgeBase(
    token: string,
    data: KnowledgeBaseCreate
  ): Promise<KnowledgeBase> {
    return this.authenticatedRequest('/api/knowledge-bases', token, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateKnowledgeBase(
    token: string,
    id: number,
    data: KnowledgeBaseUpdate
  ): Promise<KnowledgeBase> {
    return this.authenticatedRequest(`/api/knowledge-bases/${id}`, token, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteKnowledgeBase(token: string, id: number): Promise<{ message: string }> {
    return this.authenticatedRequest(`/api/knowledge-bases/${id}`, token, {
      method: 'DELETE',
    });
  }

  // Document endpoints
  async getDocuments(
    token: string,
    knowledgeBaseId: number,
    page: number = 1,
    pageSize: number = 20
  ): Promise<DocumentListResponse> {
    return this.authenticatedRequest(
      `/api/documents?knowledge_base_id=${knowledgeBaseId}&page=${page}&page_size=${pageSize}`,
      token
    );
  }

  async uploadDocument(
    token: string,
    knowledgeBaseId: number,
    file: File
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('knowledge_base_id', knowledgeBaseId.toString());

    return this.authenticatedRequest(
      '/api/documents/upload',
      token,
      {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': null as unknown as string,
        },
      }
    );
  }

  async getDocument(token: string, id: number): Promise<{ success: boolean; document: Document }> {
    return this.authenticatedRequest(`/api/documents/${id}`, token);
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

  // Learning Record Management endpoints
  async createLearningAnswerRecord(
    token: string,
    data: LearningAnswerRecordCreate
  ): Promise<LearningAnswerRecord> {
    return this.authenticatedRequest('/api/learning/answer-records', token, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getLearningAnswerRecords(
    token: string,
    skip: number = 0,
    limit: number = 20
  ): Promise<LearningAnswerRecord[]> {
    return this.authenticatedRequest(`/api/learning/answer-records?skip=${skip}&limit=${limit}`, token);
  }

  async getLearningAnswerRecord(
    token: string,
    recordId: number
  ): Promise<LearningAnswerRecord> {
    return this.authenticatedRequest(`/api/learning/answer-records/${recordId}`, token);
  }

  async updateLearningAnswerRecord(
    token: string,
    recordId: number,
    data: LearningAnswerRecordUpdate
  ): Promise<LearningAnswerRecord> {
    return this.authenticatedRequest(`/api/learning/answer-records/${recordId}`, token, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteLearningAnswerRecord(
    token: string,
    recordId: number
  ): Promise<{ message: string }> {
    return this.authenticatedRequest(`/api/learning/answer-records/${recordId}`, token, {
      method: 'DELETE',
    });
  }

  async bulkDeleteLearningAnswerRecords(
    token: string,
    request: BulkDeleteRequest
  ): Promise<{ deleted_count: number; message: string }> {
    return this.authenticatedRequest('/api/learning/answer-records/bulk-delete', token, {
      method: 'DELETE',
      body: JSON.stringify(request),
    });
  }

  async searchLearningAnswerRecords(
    token: string,
    searchRequest: LearningRecordSearchRequest
  ): Promise<LearningAnswerRecord[]> {
    return this.authenticatedRequest('/api/learning/answer-records/search', token, {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    });
  }

  async getLearningStatistics(token: string): Promise<LearningStatistics> {
    return this.authenticatedRequest('/api/learning/statistics', token);
  }

  async getLearningProgress(token: string): Promise<LearningProgressResponse> {
    return this.authenticatedRequest('/api/learning/progress', token);
  }

  // Review Record endpoints
  async createReviewRecord(
    token: string,
    data: ReviewRecordCreate
  ): Promise<ReviewRecord> {
    return this.authenticatedRequest('/api/learning/review-records', token, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getReviewRecords(
    token: string,
    skip: number = 0,
    limit: number = 20,
    contentType?: 'question' | 'knowledge_point'
  ): Promise<ReviewRecord[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (contentType) {
      params.append('content_type', contentType);
    }

    return this.authenticatedRequest(`/api/learning/review-records?${params.toString()}`, token);
  }

  async getDueReviews(
    token: string,
    limit: number = 50
  ): Promise<ReviewRecord[]> {
    return this.authenticatedRequest(`/api/learning/review-records/due?limit=${limit}`, token);
  }

  async completeReview(
    token: string,
    recordId: number,
    quality: number
  ): Promise<ReviewRecord> {
    return this.authenticatedRequest(`/api/learning/review-records/${recordId}/complete?quality=${quality}`, token, {
      method: 'PUT',
    });
  }

  async updateReviewRecord(
    token: string,
    recordId: number,
    data: ReviewRecordUpdate
  ): Promise<ReviewRecord> {
    return this.authenticatedRequest(`/api/learning/review-records/${recordId}`, token, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteReviewRecord(
    token: string,
    recordId: number
  ): Promise<{ message: string }> {
    return this.authenticatedRequest(`/api/learning/review-records/${recordId}`, token, {
      method: 'DELETE',
    });
  }

  // Knowledge Point endpoints
  async extractKnowledgePointsFromDocument(
    token: string,
    documentId: number,
    targetCount?: number
  ): Promise<KnowledgePointExtractionResponse> {
    const params = new URLSearchParams();
    if (targetCount !== undefined) {
      params.append('target_count', targetCount.toString());
    }
    
    return this.authenticatedRequest(
      `/api/knowledge-points/extract/document/${documentId}?${params.toString()}`,
      token,
      { method: 'POST' }
    );
  }

  async extractKnowledgePointsFromKnowledgeBase(
    token: string,
    knowledgeBaseId: number,
    targetCountPerDocument?: number
  ): Promise<{
    success: boolean;
    total_documents: number;
    processed_documents: number;
    total_knowledge_points: number;
    errors: string[];
  }> {
    const params = new URLSearchParams();
    if (targetCountPerDocument !== undefined) {
      params.append('target_count_per_document', targetCountPerDocument.toString());
    }
    
    return this.authenticatedRequest(
      `/api/knowledge-points/extract/knowledge-base/${knowledgeBaseId}?${params.toString()}`,
      token,
      { method: 'POST' }
    );
  }

  async getKnowledgePoints(
    token: string,
    options: {
      document_id?: number;
      knowledge_base_id?: number;
      importance_level?: number;
      search_query?: string;
      skip?: number;
      limit?: number;
    } = {}
  ): Promise<KnowledgePointListResponse> {
    const params = new URLSearchParams();
    
    if (options.document_id) params.append('document_id', options.document_id.toString());
    if (options.knowledge_base_id) params.append('knowledge_base_id', options.knowledge_base_id.toString());
    if (options.importance_level) params.append('importance_level', options.importance_level.toString());
    if (options.search_query) params.append('search_query', options.search_query);
    if (options.skip !== undefined) params.append('skip', options.skip.toString());
    if (options.limit !== undefined) params.append('limit', options.limit.toString());

    return this.authenticatedRequest(`/api/knowledge-points?${params.toString()}`, token);
  }

  async getKnowledgePoint(
    token: string,
    kpId: number
  ): Promise<KnowledgePointResponse> {
    return this.authenticatedRequest(`/api/knowledge-points/${kpId}`, token);
  }

  async updateKnowledgePoint(
    token: string,
    kpId: number,
    data: KnowledgePointUpdate
  ): Promise<{ success: boolean; knowledge_point: KnowledgePoint; message: string }> {
    return this.authenticatedRequest(`/api/knowledge-points/${kpId}`, token, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteKnowledgePoint(
    token: string,
    kpId: number
  ): Promise<{ success: boolean; message: string }> {
    return this.authenticatedRequest(`/api/knowledge-points/${kpId}`, token, {
      method: 'DELETE',
    });
  }

  async searchKnowledgePoints(
    token: string,
    query: string,
    options: {
      knowledge_base_id?: number;
      document_id?: number;
      importance_level?: number;
      n_results?: number;
    } = {}
  ): Promise<KnowledgePointSearchResponse> {
    const body: Record<string, unknown> = {
      ...options,
    };

    // 只有当query不为空时才添加到body中
    if (query && query.trim()) {
      body.query = query.trim();
    }

    return this.authenticatedRequest('/api/knowledge-points/search', token, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async getKnowledgePointStatistics(
    token: string,
    knowledgeBaseId?: number
  ): Promise<KnowledgePointStatisticsResponse> {
    const params = knowledgeBaseId ? `?knowledge_base_id=${knowledgeBaseId}` : '';
    return this.authenticatedRequest(`/api/knowledge-points/statistics/overview${params}`, token);
  }

  async batchExtractKnowledgePoints(
    token: string,
    documentIds: number[],
    forceRegenerate: boolean = false
  ): Promise<BatchExtractionResponse> {
    return this.authenticatedRequest('/api/knowledge-points/batch/extract', token, {
      method: 'POST',
      body: JSON.stringify({
        document_ids: documentIds,
        force_regenerate: forceRegenerate,
      }),
    });
  }

  async batchDeleteKnowledgePoints(
    token: string,
    kpIds: number[]
  ): Promise<BatchDeleteResponse> {
    return this.authenticatedRequest('/api/knowledge-points/batch', token, {
      method: 'DELETE',
      body: JSON.stringify({
        kp_ids: kpIds,
      }),
    });
  }

  // Learning Set endpoints
  async getLearningSets(token: string): Promise<LearningSetListResponse> {
    return this.authenticatedRequest('/api/learning-sets', token);
  }

  async getLearningSet(token: string, id: number): Promise<LearningSetDetailResponse> {
    return this.authenticatedRequest(`/api/learning-sets/${id}`, token);
  }

  async createLearningSet(
    token: string,
    data: LearningSetCreate
  ): Promise<LearningSet> {
    return this.authenticatedRequest('/api/learning-sets', token, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateLearningSet(
    token: string,
    id: number,
    data: LearningSetUpdate
  ): Promise<LearningSet> {
    return this.authenticatedRequest(`/api/learning-sets/${id}`, token, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteLearningSet(token: string, id: number): Promise<{ message: string }> {
    return this.authenticatedRequest(`/api/learning-sets/${id}`, token, {
      method: 'DELETE',
    });
  }

  async getLearningSetItems(token: string, id: number): Promise<{ items: LearningSetItem[] }> {
    return this.authenticatedRequest(`/api/learning-sets/${id}/items`, token);
  }

  async createOrUpdateLearningRecord(
    token: string,
    data: LearningSessionAnswer
  ): Promise<LearningRecordResponse> {
    return this.authenticatedRequest('/api/learning-sets/learning-records', token, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async createLearningRecord(
    token: string,
    data: LearningRecordCreate
  ): Promise<LearningRecord> {
    return this.authenticatedRequest('/api/learning-records', token, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Review and Spaced Repetition endpoints
  async getSpacedRepetitionDueReviews(
    token: string,
    limit: number = 50
  ): Promise<DueReviewItem[]> {
    return this.authenticatedRequest(`/api/review/due?limit=${limit}`, token);
  }

  async completeSpacedRepetitionReview(
    token: string,
    reviewData: ReviewSubmission
  ): Promise<ReviewResponse> {
    return this.authenticatedRequest('/api/review/complete', token, {
      method: 'POST',
      body: JSON.stringify(reviewData),
    });
  }

  async getReviewStatistics(token: string): Promise<ReviewStatistics> {
    return this.authenticatedRequest('/api/review/statistics', token);
  }

  async getUpcomingReviews(
    token: string,
    days: number = 7
  ): Promise<UpcomingReviews> {
    return this.authenticatedRequest(`/api/review/upcoming?days=${days}`, token);
  }

  async scheduleItemForReview(
    token: string,
    contentId: number,
    contentType: 'question' | 'knowledge_point'
  ): Promise<{ success: boolean; message: string; review_record_id: number; next_review: string }> {
    return this.authenticatedRequest('/api/review/schedule', token, {
      method: 'POST',
      body: JSON.stringify({
        content_id: contentId,
        content_type: contentType,
      }),
    });
  }

  async getReviewReminders(token: string): Promise<ReviewReminder[]> {
    return this.authenticatedRequest('/api/review/reminders', token);
  }

  async getDailySummary(token: string): Promise<DailySummary> {
    return this.authenticatedRequest('/api/review/daily-summary', token);
  }

  async getWeeklySummary(token: string): Promise<WeeklySummary> {
    return this.authenticatedRequest('/api/review/weekly-summary', token);
  }

  // Anki Export endpoints
  async exportAnkiDeck(
    token: string,
    request: AnkiExportRequest
  ): Promise<AnkiExportResponse> {
    return this.authenticatedRequest('/api/anki/export', token, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async exportKnowledgeBaseAnkiDeck(
    token: string,
    knowledgeBaseId: number
  ): Promise<AnkiExportResponse> {
    return this.authenticatedRequest(
      `/api/anki/export/knowledge-base/${knowledgeBaseId}`,
      token,
      { method: 'POST' }
    );
  }

  async exportCustomAnkiDeck(
    token: string,
    request: CustomAnkiExportRequest
  ): Promise<AnkiExportResponse> {
    return this.authenticatedRequest('/api/anki/export/custom', token, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async downloadAnkiDeck(
    token: string,
    exportId: string
  ): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/anki/download/${exportId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.blob();
  }

  async getAnkiExports(token: string): Promise<AnkiExportListResponse> {
    return this.authenticatedRequest('/api/anki/exports', token);
  }

  async deleteAnkiExport(
    token: string,
    exportId: string
  ): Promise<{ message: string }> {
    return this.authenticatedRequest(`/api/anki/exports/${exportId}`, token, {
      method: 'DELETE',
    });
  }

  // Dashboard endpoints
  async getDashboardStats(token: string): Promise<DashboardStats> {
    return this.authenticatedRequest('/api/dashboard/stats', token);
  }

  // Settings endpoints
  async getModelSettings(token: string): Promise<any> {
    return this.authenticatedRequest('/api/settings/models', token);
  }

  async updateModelSettings(token: string, settings: any): Promise<any> {
    return this.authenticatedRequest('/api/settings/models', token, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async getModelStatus(token: string): Promise<any> {
    return this.authenticatedRequest('/api/settings/models/status', token);
  }

  async testModelConnection(token: string, provider: string): Promise<any> {
    return this.authenticatedRequest('/api/settings/models/test-connection', token, {
      method: 'POST',
      body: JSON.stringify({ provider }),
    });
  }

  async exportSettings(token: string): Promise<unknown> {
    return this.authenticatedRequest('/api/settings/export', token);
  }
}

export const apiClient = new ApiClient();