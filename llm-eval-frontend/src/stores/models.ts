// src/stores/models.ts
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getModels, deleteModel as apiDeleteModel, createModel as apiCreateModel, updateModel as apiUpdateModel, validateModel as apiValidateModel } from '@/api/models'
import type { AIModel } from '@/types/model'

export const useModelsStore = defineStore('models', () => {
  const models = ref<AIModel[]>([])
  const loading = ref(false)
  const total = ref(0)

  const fetchModels = async (params?: Record<string, any>) => {
    loading.value = true
    try {
      // 设置大的分页参数以获取所有模型
      const queryParams = {
        per_page: 100, // 获取更多数据，足够显示所有模型
        page: 1,
        ...params
      }

      const response = await getModels(queryParams)

      if (response.success && response.data) {
        models.value = response.data.models || []
        total.value = response.data.pagination?.total || models.value.length
        console.log('📊 获取模型成功:', {
          获取数量: models.value.length,
          总数: total.value,
          分页信息: response.data.pagination
        })
      } else {
        throw new Error(response.error || '获取模型列表失败')
      }
    } catch (error: any) {
      console.error('Failed to fetch models:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const createModel = async (data: Partial<AIModel>) => {
    try {
      const response = await apiCreateModel(data)

      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || '创建模型失败')
      }
    } catch (error) {
      console.error('Failed to create model:', error)
      throw error
    }
  }

  const updateModel = async (id: number, data: Partial<AIModel>) => {
    try {
      const response = await apiUpdateModel(id, data)

      if (response.success) {
        return response.data
      } else {
        throw new Error(response.error || '更新模型失败')
      }
    } catch (error) {
      console.error('Failed to update model:', error)
      throw error
    }
  }

  const deleteModel = async (id: number) => {
    try {
      const response = await apiDeleteModel(id)

      if (response.success) {
        return response
      } else {
        throw new Error(response.error || '删除模型失败')
      }
    } catch (error) {
      console.error('Failed to delete model:', error)
      throw error
    }
  }

  const validateModel = async (id: number) => {
    try {
      const response = await apiValidateModel(id)

      if (response.success) {
        return response.data
      } else {
        throw new Error(response.error || '验证模型失败')
      }
    } catch (error) {
      console.error('Failed to validate model:', error)
      throw error
    }
  }

  // 兼容旧的方法名
  const saveModel = async (data: Partial<AIModel>, id?: number) => {
    if (id) {
      return await updateModel(id, data)
    } else {
      return await createModel(data)
    }
  }

  const removeModel = async (model: AIModel) => {
    return await deleteModel(model.id)
  }

  return {
    models,
    loading,
    total,
    fetchModels,
    createModel,
    updateModel,
    deleteModel,
    validateModel,
    saveModel,
    removeModel,
  }
})