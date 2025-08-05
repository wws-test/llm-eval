<template>
  <div>
    <!-- 页面头部 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <div>
        <h1 style="margin: 0; font-size: 24px; font-weight: 600;">性能评估</h1>
        <p style="margin: 8px 0 0 0; color: #909399;">
          测试模型的响应速度、吞吐量和资源消耗等性能指标
        </p>
      </div>
      <n-space>
        <n-button @click="$router.push('/perf-eval/history')">
          <template #icon>
            <n-icon><Time /></n-icon>
          </template>
          查看历史
        </n-button>
        <n-button type="primary" @click="$router.push('/perf-eval/create')">
          <template #icon>
            <n-icon><Rocket /></n-icon>
          </template>
          创建性能测试
        </n-button>
      </n-space>
    </n-space>

    <!-- 功能介绍卡片 -->
    <div class="feature-grid">
      <!-- 创建测试 -->
      <n-card
        class="feature-card"
        hoverable
        @click="$router.push('/perf-eval/create')"
        style="cursor: pointer;"
      >
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#18a058">
              <Rocket />
            </n-icon>
            <span>创建性能测试</span>
          </n-space>
        </template>
        <p>配置并启动新的性能评估任务，测试模型的响应速度和吞吐量</p>
        <template #footer>
          <n-space justify="end">
            <n-button type="primary" size="small">
              立即创建
            </n-button>
          </n-space>
        </template>
      </n-card>

      <!-- 查看历史 -->
      <n-card
        class="feature-card"
        hoverable
        @click="$router.push('/perf-eval/history')"
        style="cursor: pointer;"
      >
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#2080f0">
              <Time />
            </n-icon>
            <span>测试历史</span>
          </n-space>
        </template>
        <p>查看历史性能测试记录，分析模型性能趋势和变化</p>
        <template #footer>
          <n-space justify="end">
            <n-button size="small">
              查看历史
            </n-button>
          </n-space>
        </template>
      </n-card>

      <!-- 性能指标说明 -->
      <n-card class="feature-card">
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#f0a020">
              <Analytics />
            </n-icon>
            <span>性能指标</span>
          </n-space>
        </template>
        <div style="font-size: 14px; line-height: 1.6;">
          <p><strong>响应时间</strong>：模型处理单个请求的时间</p>
          <p><strong>吞吐量</strong>：单位时间内处理的请求数量</p>
          <p><strong>并发性能</strong>：多个并发请求下的性能表现</p>
          <p><strong>资源消耗</strong>：CPU、内存等资源使用情况</p>
        </div>
      </n-card>

      <!-- 最近任务 -->
      <n-card class="feature-card">
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#d03050">
              <List />
            </n-icon>
            <span>最近任务</span>
          </n-space>
        </template>
        <n-spin :show="recentTasksLoading">
          <div v-if="recentTasks.length > 0">
            <div v-for="task in recentTasks" :key="task.id" class="recent-task-item">
              <div class="task-info">
                <div class="task-name">{{ task.model_name }}</div>
                <div class="task-meta">{{ task.dataset_name }} • {{ formatDate(task.created_at) }}</div>
              </div>
              <n-tag :type="getStatusType(task.status)" size="small">
                {{ getStatusLabel(task.status) }}
              </n-tag>
            </div>
          </div>
          <n-empty v-else description="暂无最近任务" size="small" />
        </n-spin>
        <template #footer>
          <n-space justify="end">
            <n-button size="small" @click="$router.push('/perf-eval/history')">
              查看全部
            </n-button>
          </n-space>
        </template>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  Rocket,
  Time,
  Analytics,
  List
} from '@vicons/ionicons5'

const message = useMessage()

// 最近任务数据
const recentTasks = ref<any[]>([])
const recentTasksLoading = ref(false)

// 获取最近任务
const fetchRecentTasks = async () => {
  try {
    recentTasksLoading.value = true

    const { getRecentPerformanceTasks } = await import('@/api/performance')
    const response = await getRecentPerformanceTasks(3)

    if (response.success) {
      recentTasks.value = response.data || []
    } else {
      message.error(response.error || '获取最近任务失败')
    }
  } catch (error: any) {
    console.error('获取最近任务错误:', error)
    message.error(error.message || '获取最近任务失败')
  } finally {
    recentTasksLoading.value = false
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
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

// 组件挂载时获取数据
onMounted(() => {
  fetchRecentTasks()
})
</script>

<style scoped>
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-top: 24px;
}

.feature-card {
  transition: transform 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
}

.recent-task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.recent-task-item:last-child {
  border-bottom: none;
}

.task-info {
  flex: 1;
}

.task-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.task-meta {
  font-size: 12px;
  color: #909399;
}
</style>
