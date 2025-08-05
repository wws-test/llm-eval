// src/api/models.ts
import request from '@/utils/request'
import type { AIModel } from '@/types/model'

interface APIResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  timestamp?: string
}

interface ModelsResponse {
  models: AIModel[]
  pagination: {
    total: number
    page: number
    per_page: number
    pages: number
    has_next: boolean
    has_prev: boolean
  }
}

/**
 * 获取模型列表
 * @param params - 查询参数，例如分页、筛选等
 */
export const getModels = (params?: Record<string, any>): Promise<APIResponse<ModelsResponse>> => {
  return request.get('/models', { params })
}

/**
 * 删除一个模型
 * @param id - 模型的ID
 */
export const deleteModel = (id: number): Promise<APIResponse> => {
  return request.delete(`/models/${id}`)
}

/**
 * 验证一个模型
 * @param id - 模型的ID
 */
export const validateModel = (id: number): Promise<APIResponse> => {
  return request.post(`/models/${id}/validate`)
}

/**
 * 创建一个新模型
 * @param data - 模型数据
 */
export const createModel = (data: Partial<AIModel>): Promise<APIResponse<AIModel>> => {
  return request.post('/models', data)
}

/**
 * 更新一个模型
 * @param id - 模型的ID
 * @param data - 需要更新的模型数据
 */
export const updateModel = (id: number, data: Partial<AIModel>): Promise<APIResponse<AIModel>> => {
  return request.put(`/models/${id}`, data)
}