<template>
  <div>
    <!-- 页面头部 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <div>
        <h1 style="margin: 0; font-size: 24px; font-weight: 600;">效果评估</h1>
        <p style="margin: 8px 0 0 0; color: #909399;">
          评估模型在各种任务上的表现，生成详细的评估报告
        </p>
      </div>
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon>
          <n-icon><Play /></n-icon>
        </template>
        创建评估任务
      </n-button>
    </n-space>

    <!-- 筛选和搜索 -->
    <n-card style="margin-bottom: 16px;">
      <n-space>
        <n-input
          v-model:value="searchQuery"
          placeholder="搜索评估任务..."
          style="width: 300px;"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <n-icon><Search /></n-icon>
          </template>
        </n-input>

        <n-select
          v-model:value="selectedStatus"
          placeholder="状态筛选"
          style="width: 150px;"
          clearable
          @update:value="handleStatusFilter"
          :options="statusOptions"
        />

        <n-select
          v-model:value="selectedType"
          placeholder="类型筛选"
          style="width: 150px;"
          clearable
          @update:value="handleTypeFilter"
          :options="typeOptions"
        />

        <n-button @click="refreshEvaluations">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
      </n-space>
    </n-card>

    <!-- 评估任务列表 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="evaluations"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: any) => row.id"
        striped
      />
    </n-card>

    <!-- 创建评估任务模态框 -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="创建评估任务" style="width: 600px;">
      <n-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="任务名称" path="name">
          <n-input v-model:value="createForm.name" placeholder="请输入评估任务名称" />
        </n-form-item>

        <n-form-item label="评估类型" path="evaluation_type">
          <n-select
            v-model:value="createForm.evaluation_type"
            placeholder="请选择评估类型"
            :options="typeOptions"
          />
        </n-form-item>

        <n-form-item label="选择模型" path="model_ids">
          <n-select
            v-model:value="createForm.model_ids"
            placeholder="请选择要评估的模型"
            multiple
            :options="modelOptions"
            :loading="modelsLoading"
          />
        </n-form-item>

        <n-form-item label="选择数据集" path="dataset_id">
          <n-select
            v-model:value="createForm.dataset_id"
            placeholder="请选择评估数据集"
            :options="datasetOptions"
            :loading="datasetsLoading"
          />
        </n-form-item>

        <n-form-item label="评估配置">
          <n-space vertical style="width: 100%;">
            <n-form-item label="温度参数" path="temperature">
              <n-input-number
                v-model:value="createForm.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                placeholder="0.7"
                style="width: 100%;"
              />
            </n-form-item>

            <n-form-item label="最大Token数" path="max_tokens">
              <n-input-number
                v-model:value="createForm.max_tokens"
                :min="1"
                :max="4096"
                placeholder="1024"
                style="width: 100%;"
              />
            </n-form-item>

            <n-form-item label="批处理大小" path="batch_size">
              <n-input-number
                v-model:value="createForm.batch_size"
                :min="1"
                :max="50"
                placeholder="10"
                style="width: 100%;"
              />
            </n-form-item>
          </n-space>
        </n-form-item>

        <n-form-item label="任务描述" path="description">
          <n-input
            v-model:value="createForm.description"
            type="textarea"
            placeholder="请输入任务描述（可选）"
            :rows="3"
          />
        </n-form-item>
      </n-form>

      <template #action>
        <n-space>
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="handleCreate">
            创建并开始评估
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 评估结果详情模态框 -->
    <n-modal v-model:show="showResultModal" style="width: 90%; max-width: 1200px;">
      <n-card
        :title="`评估结果 - ${resultData?.name}`"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <template #header-extra>
          <n-button quaternary circle @click="showResultModal = false">
            <template #icon>
              <n-icon><Close /></n-icon>
            </template>
          </n-button>
        </template>

        <n-spin :show="resultLoading">
          <div v-if="resultData">
            <!-- 评估概览 -->
            <n-space style="margin-bottom: 24px;">
              <n-statistic label="总样本数" :value="resultData.total_samples || 0" />
              <n-statistic label="已完成" :value="resultData.completed_samples || 0" />
              <n-statistic label="成功率" :value="resultData.success_rate || 0" suffix="%" />
              <n-statistic label="平均分数" :value="resultData.average_score || 0" :precision="2" />
            </n-space>

            <!-- 详细结果 -->
            <n-tabs type="line" animated>
              <n-tab-pane name="summary" tab="评估摘要">
                <n-descriptions bordered :column="2">
                  <n-descriptions-item label="任务名称">{{ resultData.name }}</n-descriptions-item>
                  <n-descriptions-item label="评估类型">{{ getTypeLabel(resultData.evaluation_type) }}</n-descriptions-item>
                  <n-descriptions-item label="状态">
                    <n-tag :type="getStatusType(resultData.status)">
                      {{ getStatusLabel(resultData.status) }}
                    </n-tag>
                  </n-descriptions-item>
                  <n-descriptions-item label="创建时间">
                    {{ formatTime(resultData.created_at) }}
                  </n-descriptions-item>
                  <n-descriptions-item label="开始时间">
                    {{ formatTime(resultData.started_at) }}
                  </n-descriptions-item>
                  <n-descriptions-item label="完成时间">
                    {{ formatTime(resultData.completed_at) }}
                  </n-descriptions-item>
                </n-descriptions>

                <div v-if="resultData.description" style="margin-top: 16px;">
                  <h4>任务描述</h4>
                  <p>{{ resultData.description }}</p>
                </div>
              </n-tab-pane>

              <n-tab-pane name="results" tab="详细结果">
                <div v-if="resultData.results">
                  <n-data-table
                    :columns="resultColumns"
                    :data="resultData.results"
                    :max-height="400"
                    :scroll-x="800"
                  />
                </div>
                <n-empty v-else description="暂无详细结果" />
              </n-tab-pane>

              <n-tab-pane name="logs" tab="执行日志">
                <div v-if="resultData.logs" style="background: #f5f5f5; padding: 16px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; max-height: 400px; overflow-y: auto;">
                  {{ resultData.logs }}
                </div>
                <n-empty v-else description="暂无执行日志" />
              </n-tab-pane>
            </n-tabs>
          </div>
        </n-spin>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { useMessage, useDialog, type DataTableColumns, type FormInst } from 'naive-ui'
import {
  Play,
  Search,
  Refresh,
  Close,
  Eye,
  Trash,
  Pause,
  PlayCircle
} from '@vicons/ionicons5'

const message = useMessage()
const dialog = useDialog()

// 响应式数据
const evaluations = ref<any[]>([])
const models = ref<any[]>([])
const datasets = ref<any[]>([])
const loading = ref(false)
const modelsLoading = ref(false)
const datasetsLoading = ref(false)
const creating = ref(false)
const resultLoading = ref(false)

// 搜索和筛选
const searchQuery = ref('')
const selectedStatus = ref<string | null>(null)
const selectedType = ref<string | null>(null)

// 模态框状态
const showCreateModal = ref(false)
const showResultModal = ref(false)
const resultData = ref<any>(null)

// 表单相关
const createFormRef = ref<FormInst | null>(null)
const createForm = ref({
  name: '',
  evaluation_type: '',
  model_ids: [] as number[],
  dataset_id: null as number | null,
  temperature: 0.7,
  max_tokens: 1024,
  batch_size: 10,
  description: ''
})

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => {
    pagination.value.page = page
    fetchEvaluations()
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
    fetchEvaluations()
  }
})

// 选项配置
const statusOptions = [
  { label: '待开始', value: 'pending' },
  { label: '运行中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' }
]

const typeOptions = [
  { label: 'QA问答评估', value: 'qa' },
  { label: '多选题评估', value: 'mcq' },
  { label: 'RAG评估', value: 'rag' },
  { label: '自定义评估', value: 'custom' }
]

// 计算属性
const modelOptions = computed(() => {
  return models.value.map(model => ({
    label: model.display_name,
    value: model.id
  }))
})

const datasetOptions = computed(() => {
  return datasets.value.map(dataset => ({
    label: dataset.name,
    value: dataset.id
  }))
})

// 表单验证规则
const createRules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' }
  ],
  evaluation_type: [
    { required: true, message: '请选择评估类型', trigger: 'change' }
  ],
  model_ids: [
    { required: true, message: '请选择要评估的模型', trigger: 'change' }
  ],
  dataset_id: [
    { required: true, message: '请选择评估数据集', trigger: 'change' }
  ]
}

// 表格列定义
const columns: DataTableColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '任务名称',
    key: 'name',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '类型',
    key: 'evaluation_type',
    width: 120,
    render(row: any) {
      return getTypeLabel(row.evaluation_type)
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row: any) {
      return h('n-tag', {
        type: getStatusType(row.status)
      }, { default: () => getStatusLabel(row.status) })
    }
  },
  {
    title: '进度',
    key: 'progress',
    width: 120,
    render(row: any) {
      const progress = row.completed_samples && row.total_samples
        ? Math.round((row.completed_samples / row.total_samples) * 100)
        : 0
      return h('n-progress', {
        type: 'line',
        percentage: progress,
        showIndicator: false
      })
    }
  },
  {
    title: '模型数量',
    key: 'model_count',
    width: 100,
    render(row: any) {
      return row.model_ids ? row.model_ids.length : 0
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row: any) {
      return formatTime(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row: any) {
      const actions = []

      // 查看结果
      actions.push(h('n-button', {
        size: 'small',
        type: 'info',
        onClick: () => viewResult(row)
      }, { default: () => '查看结果', icon: () => h(Eye) }))

      // 根据状态显示不同操作
      if (row.status === 'running') {
        actions.push(h('n-button', {
          size: 'small',
          type: 'warning',
          onClick: () => pauseEvaluation(row)
        }, { default: () => '暂停', icon: () => h(Pause) }))
      } else if (row.status === 'pending' || row.status === 'failed') {
        actions.push(h('n-button', {
          size: 'small',
          type: 'success',
          onClick: () => startEvaluation(row)
        }, { default: () => '开始', icon: () => h(PlayCircle) }))
      }

      // 删除
      actions.push(h('n-button', {
        size: 'small',
        type: 'error',
        onClick: () => confirmDeleteEvaluation(row)
      }, { default: () => '删除', icon: () => h(Trash) }))

      return h('div', { style: 'display: flex; gap: 8px; flex-wrap: wrap;' }, actions)
    }
  }
]

// 结果表格列（动态生成）
const resultColumns = ref<DataTableColumns>([])

// 获取评估列表
const fetchEvaluations = async () => {
  try {
    loading.value = true

    const params = new URLSearchParams()
    params.append('page', pagination.value.page.toString())
    params.append('per_page', pagination.value.pageSize.toString())

    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    if (selectedStatus.value) {
      params.append('status', selectedStatus.value)
    }
    if (selectedType.value) {
      params.append('type', selectedType.value)
    }

    const token = localStorage.getItem('auth_token')
    if (!token) {
      message.error('请先登录')
      return
    }

    const response = await fetch(`/api/evaluations?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        evaluations.value = data.data.evaluations
        pagination.value.itemCount = data.data.total
      } else {
        message.error(data.error || '获取评估列表失败')
      }
    } else {
      message.error('获取评估列表失败')
    }
  } catch (error) {
    console.error('获取评估列表错误:', error)
    message.error('网络错误，请检查连接')
  } finally {
    loading.value = false
  }
}

// 获取模型列表
const fetchModels = async () => {
  try {
    modelsLoading.value = true

    const token = localStorage.getItem('auth_token')
    if (!token) return

    const response = await fetch('/api/models', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        models.value = data.data.models.filter((model: any) => model.is_validated)
      }
    }
  } catch (error) {
    console.error('获取模型列表错误:', error)
  } finally {
    modelsLoading.value = false
  }
}

// 获取数据集列表
const fetchDatasets = async () => {
  try {
    datasetsLoading.value = true

    const token = localStorage.getItem('auth_token')
    if (!token) return

    const response = await fetch('/api/datasets', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        datasets.value = data.data.datasets
      }
    }
  } catch (error) {
    console.error('获取数据集列表错误:', error)
  } finally {
    datasetsLoading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.value.page = 1
  fetchEvaluations()
}

// 状态筛选处理
const handleStatusFilter = () => {
  pagination.value.page = 1
  fetchEvaluations()
}

// 类型筛选处理
const handleTypeFilter = () => {
  pagination.value.page = 1
  fetchEvaluations()
}

// 刷新评估列表
const refreshEvaluations = () => {
  fetchEvaluations()
}

// 创建评估任务
const handleCreate = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()
    creating.value = true

    const token = localStorage.getItem('auth_token')
    if (!token) {
      message.error('请先登录')
      return
    }

    const response = await fetch('/api/evaluations', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(createForm.value)
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        message.success('评估任务创建成功')
        showCreateModal.value = false
        resetCreateForm()
        fetchEvaluations()
      } else {
        message.error(data.error || '创建评估任务失败')
      }
    } else {
      message.error('创建评估任务失败')
    }
  } catch (error: any) {
    if (error.errors) {
      return
    }
    console.error('创建评估任务错误:', error)
    message.error('创建评估任务失败，请重试')
  } finally {
    creating.value = false
  }
}

// 重置创建表单
const resetCreateForm = () => {
  createForm.value = {
    name: '',
    evaluation_type: '',
    model_ids: [],
    dataset_id: null,
    temperature: 0.7,
    max_tokens: 1024,
    batch_size: 10,
    description: ''
  }
}

// 查看评估结果
const viewResult = async (evaluation: any) => {
  try {
    resultLoading.value = true
    resultData.value = evaluation
    showResultModal.value = true

    const token = localStorage.getItem('auth_token')
    if (!token) {
      message.error('请先登录')
      return
    }

    const response = await fetch(`/api/evaluations/${evaluation.id}/results`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        resultData.value = { ...evaluation, ...data.data }

        // 动态生成结果表格列
        if (data.data.results && data.data.results.length > 0) {
          const firstResult = data.data.results[0]
          resultColumns.value = Object.keys(firstResult).map(key => ({
            title: key,
            key: key,
            ellipsis: {
              tooltip: true
            },
            width: 150
          }))
        }
      } else {
        message.error(data.error || '获取评估结果失败')
      }
    } else {
      message.error('获取评估结果失败')
    }
  } catch (error) {
    console.error('获取评估结果错误:', error)
    message.error('网络错误，请检查连接')
  } finally {
    resultLoading.value = false
  }
}

// 开始评估
const startEvaluation = async (evaluation: any) => {
  try {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      message.error('请先登录')
      return
    }

    const response = await fetch(`/api/evaluations/${evaluation.id}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        message.success('评估任务已开始')
        fetchEvaluations()
      } else {
        message.error(data.error || '开始评估失败')
      }
    } else {
      message.error('开始评估失败')
    }
  } catch (error) {
    console.error('开始评估错误:', error)
    message.error('网络错误，请检查连接')
  }
}

// 暂停评估
const pauseEvaluation = async (evaluation: any) => {
  try {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      message.error('请先登录')
      return
    }

    const response = await fetch(`/api/evaluations/${evaluation.id}/pause`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        message.success('评估任务已暂停')
        fetchEvaluations()
      } else {
        message.error(data.error || '暂停评估失败')
      }
    } else {
      message.error('暂停评估失败')
    }
  } catch (error) {
    console.error('暂停评估错误:', error)
    message.error('网络错误，请检查连接')
  }
}

// 确认删除评估
const confirmDeleteEvaluation = (evaluation: any) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除评估任务 "${evaluation.name}" 吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => deleteEvaluation(evaluation)
  })
}

// 删除评估
const deleteEvaluation = async (evaluation: any) => {
  try {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      message.error('请先登录')
      return
    }

    const response = await fetch(`/api/evaluations/${evaluation.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        message.success('评估任务删除成功')
        fetchEvaluations()
      } else {
        message.error(data.error || '删除失败')
      }
    } else {
      message.error('删除失败')
    }
  } catch (error) {
    console.error('删除评估错误:', error)
    message.error('网络错误，请检查连接')
  }
}

// 工具函数
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待开始',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'pending': 'default',
    'running': 'info',
    'completed': 'success',
    'failed': 'error',
    'cancelled': 'warning'
  }
  return typeMap[status] || 'default'
}

const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    'qa': 'QA问答评估',
    'mcq': '多选题评估',
    'rag': 'RAG评估',
    'custom': '自定义评估'
  }
  return typeMap[type] || type
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString()
}

// 组件挂载时获取数据
onMounted(() => {
  fetchEvaluations()
  fetchModels()
  fetchDatasets()
})
</script>
