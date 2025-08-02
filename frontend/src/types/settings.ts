/**
 * Settings related type definitions
 */

export interface ModelSettings {
  provider: 'openai' | 'ollama';
  fallback_provider?: 'openai' | 'ollama';
  
  // OpenAI settings
  openai_api_key_set: boolean;
  openai_base_url: string;
  openai_model: string;
  openai_embedding_model: string;
  
  // Ollama settings
  ollama_base_url: string;
  ollama_model: string;
  
  // Embedding settings
  embedding_provider: string;
  embedding_model: string;
  embedding_dimension: number;
  
  // OpenAI embedding settings
  openai_embedding_model: string;
  openai_embedding_dimension: number;
  
  // General settings
  temperature: number;
  max_tokens: number;
  timeout: number;
}

export interface ModelStatus {
  active_provider: string;
  fallback_provider?: string;
  openai_configured: boolean;
  ollama_configured: boolean;
  embedding_provider: string;
  health_check_interval: number;
}

export interface ModelSettingsUpdateRequest {
  provider?: 'openai' | 'ollama';
  fallback_provider?: 'openai' | 'ollama';
  
  // OpenAI settings
  openai_api_key?: string;
  openai_base_url?: string;
  openai_model?: string;
  openai_embedding_model?: string;
  
  // Ollama settings
  ollama_base_url?: string;
  ollama_model?: string;
  
  // Embedding settings
  embedding_provider?: string;
  embedding_model?: string;
  embedding_dimension?: number;
  
  // OpenAI embedding settings
  openai_embedding_model_name?: string;
  openai_embedding_dimension?: number;
  
  // General settings
  temperature?: number;
  max_tokens?: number;
}

export interface ConnectionTestResult {
  success: boolean;
  message?: string;
  error?: string;
  response_time_ms?: number;
}

export interface SettingsExport {
  config: Record<string, any>;
  exported_at: string;
}