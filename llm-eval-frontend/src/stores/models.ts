// src/stores/models.ts
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getModels, deleteModel as apiDeleteModel, createModel, updateModel } from '@/api/models'
import type { AIModel } from '@/types/model'
import { ElMessage, ElMessageBox } from 'element-plus'

export const useModelsStore = defineStore('models', () => {
  const models = ref<AIModel[]>([])
  const loading = ref(false)
  const total = ref(0)

  const fetchModels = async (params?: Record<string, any>) => {
    loading.value = true
    try {
      const response = await getModels(params)
      models.value = response.models
      total.value = response.total
    } catch (error) {
      console.error('Failed to fetch models:', error)
      ElMessage.error('获取模型列表失败')
    } finally {
      loading.value = false
    }
  }

  const saveModel = async (data: Partial<AIModel>, id?: number) => {
    try {
      if (id) {
        await updateModel(id, data);
        ElMessage.success('模型更新成功');
      } else {
        await createModel(data);
        ElMessage.success('模型创建成功');
      }
      // Refresh the list
      await fetchModels();
    } catch (error) {
      console.error('Failed to save model:', error);
      ElMessage.error(id ? '更新模型失败' : '创建模型失败');
      // Re-throw the error to be caught in the component
      throw error;
    }
  }

  const removeModel = async (model: AIModel) => {
    try {
      await ElMessageBox.confirm(
        `您确定要删除模型 <strong>${model.display_name}</strong> 吗？此操作无法撤销。`,
        '确认删除模型',
        {
          confirmButtonText: '确认删除',
          cancelButtonText: '取消',
          type: 'warning',
          dangerouslyUseHTMLString: true,
        }
      )

      await apiDeleteModel(model.id)
      ElMessage.success('模型删除成功')
      
      await fetchModels()
      
    } catch (error) {
      if (error !== 'cancel') {
        console.error(`Failed to delete model ${model.id}:`, error)
        ElMessage.error('删除模型失败')
      }
    }
  }

  return {
    models,
    loading,
    total,
    fetchModels,
    saveModel,
    removeModel,
  }
}) 