// src/api/models.ts
import request from '@/utils/request'
import type { AIModel, ModelListResponse } from '@/types/model'

/**
 * 获取模型列表
 * @param params - 查询参数，例如分页、筛选等
 */
export const getModels = (params?: Record<string, any>): Promise<ModelListResponse> => {
  return request({
    url: '/models',
    method: 'get',
    params,
  })
}

/**
 * 删除一个模型
 * @param id - 模型的ID
 */
export const deleteModel = (id: number): Promise<void> => {
  return request({
    url: `/models/${id}`,
    method: 'delete',
  })
}

/**
 * 验证一个模型
 * @param id - 模型的ID
 */
export const validateModel = (id: number): Promise<void> => {
  return request({
    url: `/models/${id}/validate`,
    method: 'post',
  })
}

/**
 * 创建一个新模型
 * @param data - 模型数据
 */
export const createModel = (data: Partial<AIModel>): Promise<AIModel> => {
  return request({
    url: '/models',
    method: 'post',
    data,
  })
}

/**
 * 更新一个模型
 * @param id - 模型的ID
 * @param data - 需要更新的模型数据
 */
export const updateModel = (id: number, data: Partial<AIModel>): Promise<AIModel> => {
  return request({
    url: `/models/${id}`,
    method: 'put',
    data,
  })
} 