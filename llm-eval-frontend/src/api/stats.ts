import request from '@/utils/request'

// 统计数据相关接口

export interface DashboardStats {
  overview: {
    total_models: number
    total_chats: number
    total_datasets: number
    total_evaluations: number
  }
  models: {
    total: number
    user_models: number
    system_models: number
    validated: number
    unvalidated: number
  }
  evaluations: {
    total: number
    model_evaluations: number
    rag_evaluations: number
    performance_evaluations: number
  }
  recent_activity: {
    recent_chats: Array<{
      id: number
      title: string
      updated_at: string
    }>
    recent_evaluations: Array<{
      id: number
      type: string
      name: string
      status: string
      created_at: string
    }>
  }
}

export interface ModelStats {
  by_type: Array<{
    type: string
    count: number
  }>
  by_provider: Array<{
    provider: string
    count: number
  }>
}

/**
 * 获取仪表盘统计数据
 */
export function getDashboardStats() {
  return request<DashboardStats>({
    url: '/stats/dashboard',
    method: 'get'
  })
}

/**
 * 获取模型统计数据
 */
export function getModelStats() {
  return request<ModelStats>({
    url: '/stats/models',
    method: 'get'
  })
}
