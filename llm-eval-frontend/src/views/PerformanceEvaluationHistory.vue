<template>
  <div>
    <!-- 页面头部 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <div>
        <h1 style="margin: 0; font-size: 24px; font-weight: 600;">性能测试历史</h1>
        <p style="margin: 8px 0 0 0; color: #909399;">
          查看和管理您的性能测试记录
        </p>
      </div>
      <n-space>
        <n-button @click="refreshTasks" :loading="loading">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
        <n-button type="primary" @click="$router.push('/perf-eval/create')">
          <template #icon>
            <n-icon><Add /></n-icon>
          </template>
          创建新测试
        </n-button>
      </n-space>
    </n-space>

    <!-- 筛选和搜索 -->
    <n-card style="margin-bottom: 24px;">
      <n-space>
        <n-input
          v-model:value="searchQuery"
          placeholder="搜索模型名称或数据集..."
          style="width: 300px;"
          clearable
        >
          <template #prefix>
            <n-icon><Search /></n-icon>
          </template>
        </n-input>
        
        <n-select
          v-model:value="statusFilter"
          placeholder="筛选状态"
          style="width: 150px;"
          clearable
          :options="statusOptions"
        />
        
        <n-button @click="handleSearch">搜索</n-button>
        <n-button @click="resetFilters">重置</n-button>
      </n-space>
    </n-card>

    <!-- 统计信息 -->
    <n-card style="margin-bottom: 24px;">
      <div class="stats-grid">
        <n-statistic label="总任务数" :value="pagination.itemCount">
          <template #prefix>
            <n-icon color="#18a058"><List /></n-icon>
          </template>
        </n-statistic>

        <n-statistic label="已完成" :value="taskStats.completed">
          <template #prefix>
            <n-icon color="#18a058"><CheckmarkCircle /></n-icon>
          </template>
        </n-statistic>

        <n-statistic label="运行中" :value="taskStats.running">
          <template #prefix>
            <n-icon color="#2080f0"><Time /></n-icon>
          </template>
        </n-statistic>

        <n-statistic label="失败" :value="taskStats.failed">
          <template #prefix>
            <n-icon color="#d03050"><CloseCircle /></n-icon>
          </template>
        </n-statistic>
      </div>
    </n-card>

    <!-- 任务列表 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="tasks"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: any) => row.id"
        striped
      />
    </n-card>

    <!-- 删除确认对话框 -->
    <n-modal v-model:show="showDeleteModal" preset="dialog" type="warning">
      <template #header>
        <span>确认删除</span>
      </template>
      <span>确定要删除这个性能测试任务吗？此操作无法撤销。</span>
      <template #action>
        <n-space>
          <n-button @click="showDeleteModal = false">取消</n-button>
          <n-button type="error" :loading="deleting" @click="confirmDelete">
            删除
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, useDialog, type DataTableColumns } from 'naive-ui'
import {
  Refresh,
  Add,
  Search,
  Eye,
  Trash,
  Time,
  List,
  CheckmarkCircle,
  CloseCircle
} from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()

// 数据
const tasks = ref<any[]>([])
const loading = ref(false)
const deleting = ref(false)

// 搜索和筛选
const searchQuery = ref('')
const statusFilter = ref<string | null>(null)

// 任务统计
const taskStats = ref({
  completed: 0,
  running: 0,
  failed: 0,
  pending: 0
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => {
    pagination.page = page
    fetchTasks()
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.pageSize = pageSize
    pagination.page = 1
    fetchTasks()
  }
})

// 删除相关
const showDeleteModal = ref(false)
const taskToDelete = ref<any>(null)

// 状态选项
const statusOptions = [
  { label: '等待中', value: 'pending' },
  { label: '运行中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
]

// 表格列定义
const columns: DataTableColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '模型名称',
    key: 'model_name',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '数据集',
    key: 'dataset_name',
    width: 120
  },
  {
    title: '并发数',
    key: 'concurrency',
    width: 100,
    align: 'center'
  },
  {
    title: '请求数',
    key: 'num_requests',
    width: 100,
    align: 'center'
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
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row: any) {
      return formatDate(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    align: 'center',
    render(row: any) {
      return h('div', { style: 'display: flex; gap: 8px; justify-content: center;' }, [
        // 查看结果按钮
        h('button', {
          style: 'padding: 4px 12px; background: #2080f0; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 4px;',
          onClick: () => viewResults(row)
        }, [
          h('span', '👁️'),
          h('span', '查看')
        ]),

        // 删除按钮
        h('button', {
          style: 'padding: 4px 12px; background: #d03050; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 4px;',
          onClick: () => deleteTask(row)
        }, [
          h('span', '🗑️'),
          h('span', '删除')
        ])
      ])
    }
  }
]

// 获取任务列表
const fetchTasks = async () => {
  try {
    loading.value = true

    const { getPerformanceTasks } = await import('@/api/performance')
    const response = await getPerformanceTasks({
      search: searchQuery.value,
      status: statusFilter.value || undefined,
      page: pagination.page,
      per_page: pagination.pageSize
    })

    if (response.success) {
      tasks.value = response.data?.tasks || []
      pagination.itemCount = response.data?.pagination.total || 0

      // 计算当前页面的任务统计
      const currentPageStats = {
        completed: 0,
        running: 0,
        failed: 0,
        pending: 0
      }

      tasks.value.forEach(task => {
        if (task.status in currentPageStats) {
          currentPageStats[task.status as keyof typeof currentPageStats]++
        }
      })

      taskStats.value = currentPageStats
    } else {
      message.error(response.error || '获取任务列表失败')
    }

  } catch (error: any) {
    console.error('获取任务列表错误:', error)
    message.error(error.message || '获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新任务列表
const refreshTasks = () => {
  fetchTasks()
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchTasks()
}

// 重置筛选
const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = null
  pagination.page = 1
  fetchTasks()
}

// 查看结果
const viewResults = (task: any) => {
  router.push(`/perf-eval/results/${task.id}`)
}

// 删除任务
const deleteTask = (task: any) => {
  taskToDelete.value = task
  showDeleteModal.value = true
}

// 确认删除
const confirmDelete = async () => {
  if (!taskToDelete.value) return

  try {
    deleting.value = true

    const { deletePerformanceTask } = await import('@/api/performance')
    const response = await deletePerformanceTask(taskToDelete.value.id)

    if (response.success) {
      message.success('任务删除成功')
      showDeleteModal.value = false
      taskToDelete.value = null

      // 刷新列表
      fetchTasks()
    } else {
      message.error(response.error || '删除任务失败')
    }

  } catch (error: any) {
    console.error('删除任务错误:', error)
    message.error(error.message || '删除任务失败')
  } finally {
    deleting.value = false
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'running': return 'info'
    case 'failed': return 'error'
    case 'pending': return 'warning'
    default: return 'default'
  }
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'running': return '运行中'
    case 'failed': return '失败'
    case 'pending': return '等待中'
    default: return status
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

// 组件挂载时获取数据
onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.n-card {
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}
</style>
