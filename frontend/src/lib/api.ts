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

// Evaluation interfaces
export interface AnswerSubmission {
  question_id: number;
  user_answer: string;
  save_record?: boolean;
}

export interface AnswerEvaluation {
  score: number;
  feedback: string;
  reference_answer: string;
  detailed_analysis?: {
    overall_analysis: string;
    structured_analysis: Record<string, string[]>;
    improvement_suggestions: string[];
    strengths: string[];
  };
}

export interface AnswerEvaluationResponse {
  success: boolean;
  question_id: number;
  user_answer: string;
  evaluation: AnswerEvaluation;
  record_id?: number;
}

export interface AnswerRecord {
  id: number;
  question_id: number;
  question_text: string;
  user_answer: string;
  reference_answer: string;
  score: number;
  feedback: string;
  answered_at: string;
  document_name: string;
  knowledge_base_id: number;
}

export interface AnswerRecordsResponse {
  success: boolean;
  records: AnswerRecord[];
  count: number;
  filters: {
    question_id?: number;
    knowledge_base_id?: number;
  };
}

export interface EvaluationStatistics {
  total_answers: number;
  average_score: number;
  score_distribution: Record<string, number>;
  recent_performance: Array<{
    date: string;
    score: number;
    question_text: string;
  }>;
}

export interface EvaluationStatisticsResponse {
  success: boolean;
  statistics: EvaluationStatistics;
  knowledge_base_id?: number;
}

export interface PerformanceTrend {
  date: string;
  average_score: number;
  answer_count: number;
}

export interface PerformanceTrendsResponse {
  success: boolean;
  trends: PerformanceTrend[];
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  knowledge_base_id?: number;
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
  content_title?: string;
  document_filename?: string;
  knowledge_base_name?: string;
}

export interface ReviewRecordCreate {
  content_id: number;
  content_type: 'question' | 'knowledge_point';
  review_count?: number;
  ease_factor?: number;
  interval_days?: number;
}

export interface ReviewRecordUpdate {
  review_count?: number;
  ease_factor?: number;
  interval_days?: number;
  last_reviewed?: string;
  next_review?: string;
}

export interface LearningRecordFilter {
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
  importance_level: number;
  created_at: string;
}

export interface KnowledgePointCreate {
  document_id: number;
  title: string;
  content: string;
  importance_level?: number;
}

export interface KnowledgePointUpdate {
  title?: string;
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
  by_importance_level: Record<string, number>;
  top_documents: Array<{
    filename: string;
    count: number;
  }>;
}

export interface KnowledgePointStatisticsResponse {
  success: boolean;
  statistics: KnowledgePointStatistics;
}

export interface BatchExtractionResponse {
  success: boolean;
  processed_documents: number;
  successful_extractions: number;
  total_knowledge_points: number;
  results: Array<{
    document_id: number;
    knowledge_points_count: number;
    success: boolean;
    error?: string;
  }>;
  errors: Array<{
    document_id: number;
    error: string;
  }>;
}

export interface BatchDeleteResponse {
  success: boolean;
  requested_deletions: number;
  successful_deletions: number;
  errors: string[];
}

// Review and Spaced Repetition interfaces
export interface ReviewSubmission {
  content_id: number;
  content_type: 'question' | 'knowledge_point';
  quality: number; // 0-5 rating
}

export interface ReviewResponse {
  success: boolean;
  message: string;
  next_review: string;
  interval_days: number;
  ease_factor: number;
}

export interface DueReviewItem {
  review_record_id: number;
  content_id: number;
  content_type: 'question' | 'knowledge_point';
  review_count: number;
  last_reviewed?: string;
  next_review: string;
  ease_factor: number;
  interval_days: number;
  // Content-specific fields
  question_text?: string;
  context?: string;
  difficulty_level?: number;
  title?: string;
  content?: string;
  importance_level?: number;
  document_id: number;
}

export interface ReviewStatistics {
  total_items: number;
  due_today: number;
  due_this_week: number;
  completed_today: number;
  average_ease_factor: number;
  learning_streak: number;
}

export interface UpcomingReviews {
  [date: string]: Array<{
    content_id: number;
    content_type: 'question' | 'knowledge_point';
    review_count: number;
    ease_factor: number;
    interval_days: number;
  }>;
}

export interface ReviewReminder {
  type: 'overdue' | 'due_soon';
  content_id: number;
  content_type: 'question' | 'knowledge_point';
  priority: 'high' | 'medium' | 'low';
  message: string;
  title?: string;
  hours_overdue?: number;
  hours_until_due?: number;
}

export interface DailySummary {
  date: string;
  completed_today: number;
  due_today: number;
  due_tomorrow: number;
  completion_rate: number;
}

export interface WeeklySummary {
  week_start: string;
  total_completed: number;
  daily_breakdown: Array<{
    date: string;
    count: number;
  }>;
  average_per_day: number;
}

// Anki Export interfaces
export interface AnkiExportRequest {
  deck_name: string;
  knowledge_base_ids?: number[];
  include_qa: boolean;
  include_kp: boolean;
}

export interface CustomAnkiExportRequest {
  deck_name: string;
  answer_record_ids?: number[];
  knowledge_point_ids?: number[];
}

export interface AnkiExportResponse {
  export_id: string;
  deck_name: string;
  file_path: string;
  created_at: string;
  card_count: number;
}

export interface AnkiExportListItem {
  export_id: string;
  deck_name: string;
  created_at: string;
  card_count: number;
}

export interface AnkiExportListResponse {
  exports: AnkiExportListItem[];
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

  // Evaluation endpoints
  async submitAnswer(
    token: string,
    submission: AnswerSubmission
  ): Promise<AnswerEvaluationResponse> {
    return this.authenticatedRequest('/api/evaluation/submit-answer', token, {
      method: 'POST',
      body: JSON.stringify(submission),
    });
  }

  async getAnswerRecords(
    token: string,
    questionId?: number,
    knowledgeBaseId?: number,
    skip: number = 0,
    limit: number = 100
  ): Promise<AnswerRecordsResponse> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (questionId) params.append('question_id', questionId.toString());
    if (knowledgeBaseId) params.append('knowledge_base_id', knowledgeBaseId.toString());

    return this.authenticatedRequest(`/api/evaluation/records?${params.toString()}`, token);
  }

  async getAnswerRecord(
    token: string,
    recordId: number
  ): Promise<{ success: boolean; record: AnswerRecord & { question_context?: string; question_difficulty?: number; document?: Record<string, string | number> } }> {
    return this.authenticatedRequest(`/api/evaluation/records/${recordId}`, token);
  }

  async deleteAnswerRecord(
    token: string,
    recordId: number
  ): Promise<{ success: boolean; message: string }> {
    return this.authenticatedRequest(`/api/evaluation/records/${recordId}`, token, {
      method: 'DELETE',
    });
  }

  async reEvaluateAnswer(
    token: string,
    recordId: number
  ): Promise<{ success: boolean; message: string; evaluation: AnswerEvaluation; record_id: number }> {
    return this.authenticatedRequest(`/api/evaluation/re-evaluate/${recordId}`, token, {
      method: 'POST',
    });
  }

  async getEvaluationStatistics(
    token: string,
    knowledgeBaseId?: number
  ): Promise<EvaluationStatisticsResponse> {
    const params = knowledgeBaseId ? `?knowledge_base_id=${knowledgeBaseId}` : '';
    return this.authenticatedRequest(`/api/evaluation/statistics${params}`, token);
  }

  async getPerformanceTrends(
    token: string,
    knowledgeBaseId?: number,
    days: number = 30
  ): Promise<PerformanceTrendsResponse> {
    const params = new URLSearchParams({ days: days.toString() });
    if (knowledgeBaseId) params.append('knowledge_base_id', knowledgeBaseId.toString());

    return this.authenticatedRequest(`/api/evaluation/performance-trends?${params.toString()}`, token);
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
    limit: number = 20,
    filters?: {
      knowledge_base_id?: number;
      document_id?: number;
      score_min?: number;
      score_max?: number;
      date_from?: string;
      date_to?: string;
    }
  ): Promise<LearningAnswerRecord[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (filters?.knowledge_base_id) {
      params.append('knowledge_base_id', filters.knowledge_base_id.toString());
    }
    if (filters?.document_id) {
      params.append('document_id', filters.document_id.toString());
    }
    if (filters?.score_min !== undefined) {
      params.append('score_min', filters.score_min.toString());
    }
    if (filters?.score_max !== undefined) {
      params.append('score_max', filters.score_max.toString());
    }
    if (filters?.date_from) {
      params.append('date_from', filters.date_from);
    }
    if (filters?.date_to) {
      params.append('date_to', filters.date_to);
    }

    return this.authenticatedRequest(`/api/learning/answer-records?${params.toString()}`, token);
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
    recordIds: number[]
  ): Promise<{ message: string; deleted_count: number }> {
    return this.authenticatedRequest('/api/learning/answer-records/bulk-delete', token, {
      method: 'POST',
      body: JSON.stringify({ record_ids: recordIds }),
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
    forceRegenerate: boolean = false
  ): Promise<KnowledgePointExtractionResponse> {
    return this.authenticatedRequest(
      `/api/knowledge-points/extract/document/${documentId}?force_regenerate=${forceRegenerate}`,
      token,
      { method: 'POST' }
    );
  }

  async extractKnowledgePointsFromKnowledgeBase(
    token: string,
    knowledgeBaseId: number,
    forceRegenerate: boolean = false
  ): Promise<{
    success: boolean;
    total_documents: number;
    processed_documents: number;
    total_knowledge_points: number;
    errors: string[];
  }> {
    return this.authenticatedRequest(
      `/api/knowledge-points/extract/knowledge-base/${knowledgeBaseId}?force_regenerate=${forceRegenerate}`,
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

  async createKnowledgePoint(
    token: string,
    data: KnowledgePointCreate
  ): Promise<{ success: boolean; knowledge_point: KnowledgePoint; message: string }> {
    return this.authenticatedRequest('/api/knowledge-points', token, {
      method: 'POST',
      body: JSON.stringify(data),
    });
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
      document_id?: number;
      importance_level?: number;
      n_results?: number;
    } = {}
  ): Promise<KnowledgePointSearchResponse> {
    const body = {
      query,
      ...options,
    };

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

  // Review and Spaced Repetition endpoints
  async getDueReviews(
    token: string,
    limit: number = 50
  ): Promise<DueReviewItem[]> {
    return this.authenticatedRequest(`/api/review/due?limit=${limit}`, token);
  }

  async completeReview(
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
    knowledgeBaseId: number,
    includeQa: boolean = true,
    includeKp: boolean = true
  ): Promise<AnkiExportResponse> {
    const params = new URLSearchParams({
      include_qa: includeQa.toString(),
      include_kp: includeKp.toString(),
    });

    return this.authenticatedRequest(
      `/api/anki/export/knowledge-base/${knowledgeBaseId}?${params.toString()}`,
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
}

export const apiClient = new ApiClient();