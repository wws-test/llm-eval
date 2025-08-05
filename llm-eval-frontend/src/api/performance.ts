import request from '@/utils/request'

// 性能评估相关接口

export interface PerformanceTask {
  id: number
  model_name: string
  dataset_name: string
  concurrency: number
  num_requests: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
  results?: PerformanceResults
}

export interface PerformanceResults {
  summary: {
    avg_response_time: number
    throughput: number
    success_rate: number
    error_rate: number
  }
  details: {
    min_response_time: number
    max_response_time: number
    p50_response_time: number
    p90_response_time: number
    p95_response_time: number
    p99_response_time: number
    total_duration: number
    successful_requests: number
    failed_requests: number
    avg_tokens: number
    total_tokens: number
    tokens_per_second: number
  }
  errors?: Array<{
    timestamp: string
    message: string
  }>
}

export interface CreatePerformanceTaskRequest {
  model_id: number
  dataset_id: number
  concurrency: number
  num_requests: number
  min_prompt_length?: number
  max_prompt_length?: number
  max_tokens?: number
  extra_args?: string
}

export interface BatchTestConfiguration {
  concurrency: number
  num_requests: number
  min_prompt_length?: number
  max_prompt_length?: number
  min_tokens?: number
  max_tokens?: number
  description?: string
}

export interface CreateBatchPerformanceTaskRequest {
  model_id: number
  dataset_id: number
  test_configurations: BatchTestConfiguration[]
  name?: string
  description?: string
}

export interface CreateBatchTaskFromScriptRequest {
  model_id: number
  dataset_id: number
  num_prompts_list: number[]
  max_concurrency_list: number[]
  input_output_pairs: [number, number][]
  name?: string
  description?: string
}

interface APIResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  timestamp?: string
}

interface TasksResponse {
  tasks: PerformanceTask[]
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
 * 获取性能评估任务列表
 */
export const getPerformanceTasks = (params?: {
  search?: string
  status?: string
  page?: number
  per_page?: number
}): Promise<APIResponse<TasksResponse>> => {
  return request.get('/performance-eval/tasks', { params })
}

/**
 * 获取性能评估任务详情
 */
export const getPerformanceTask = (taskId: number): Promise<APIResponse<PerformanceTask>> => {
  return request.get(`/performance-eval/tasks/${taskId}`)
}

/**
 * 创建性能评估任务
 */
export const createPerformanceTask = (data: CreatePerformanceTaskRequest): Promise<APIResponse<PerformanceTask>> => {
  return request.post('/performance-eval/tasks', data)
}

/**
 * 删除性能评估任务
 */
export const deletePerformanceTask = (taskId: number): Promise<APIResponse> => {
  return request.delete(`/performance-eval/tasks/${taskId}`)
}

/**
 * 获取性能评估任务结果
 */
export const getPerformanceResults = (taskId: number): Promise<APIResponse<PerformanceResults>> => {
  return request.get(`/performance-eval/tasks/${taskId}/results`)
}

/**
 * 获取最近的性能评估任务
 */
export const getRecentPerformanceTasks = (limit: number = 5): Promise<APIResponse<PerformanceTask[]>> => {
  return request.get('/performance-eval/tasks/recent', { params: { limit } })
}

/**
 * 获取可用的模型列表（用于性能评估）
 */
export const getAvailableModels = (): Promise<APIResponse<Array<{ id: number; name: string; display_name: string }>>> => {
  return request.get('/performance-eval/models')
}

/**
 * 获取可用的数据集列表（用于性能评估）
 */
export const getAvailableDatasets = (): Promise<APIResponse<Array<{ id: number; name: string; description?: string }>>> => {
  return request.get('/performance-eval/datasets')
}

/**
 * 获取性能指标说明
 */
export const getMetricExplanations = (): Promise<APIResponse<{
  metric_explanations: Record<string, { title: string; description: string; formula: string }>
  percentile_explanations: Record<string, { title: string; description: string }>
}>> => {
  return request.get('/performance-eval/metric-explanations')
}

/**
 * 创建批量性能评估任务
 */
export const createBatchPerformanceTask = (data: CreateBatchPerformanceTaskRequest): Promise<APIResponse<PerformanceTask>> => {
  return request.post('/performance-eval/batch-tasks', data)
}

/**
 * 从脚本样式参数创建批量性能评估任务
 */
export const createBatchTaskFromScript = (data: CreateBatchTaskFromScriptRequest): Promise<APIResponse<PerformanceTask>> => {
  return request.post('/performance-eval/batch-tasks/from-script', data)
}
