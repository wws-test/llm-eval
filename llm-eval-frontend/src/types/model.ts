// src/types/model.ts

/**
 * 模型类型
 * 'openai_compatible' - OpenAI或其兼容接口
 * 'ollama' - Ollama模型
 * 'gemini' - Google Gemini
 * ... 其他可能的类型
 */
export type ModelType = 'openai_compatible' | 'ollama' | 'gemini' | string;

/**
 * 模型对象接口
 */
export interface AIModel {
  id: number;
  display_name: string;
  model_identifier: string;
  provider_name: string | null;
  model_type: ModelType;
  is_system_model: boolean;
  is_validated: boolean;
  api_base_url: string;
  encrypted_api_key?: string;
  default_temperature?: number;
  system_prompt?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * 用于API响应的模型列表
 */
export interface ModelListResponse {
  models: AIModel[];
  total: number;
} 