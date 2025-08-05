<template>
  <div>
    <!-- 页面头部 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <div>
        <h1 style="margin: 0; font-size: 24px; font-weight: 600;">性能测试结果</h1>
        <p style="margin: 8px 0 0 0; color: #909399;">
          任务ID: {{ taskId }} - {{ taskData?.model_name || '加载中...' }}
        </p>
      </div>
      <n-space>
        <n-button @click="refreshResults" :loading="loading">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
        <n-button @click="$router.push('/perf-eval/history')">
          <template #icon>
            <n-icon><ArrowBack /></n-icon>
          </template>
          返回列表
        </n-button>
      </n-space>
    </n-space>

    <!-- 任务信息 -->
    <n-card title="任务信息" style="margin-bottom: 24px;">
      <n-spin :show="loading">
        <n-descriptions v-if="taskData" :column="3" bordered>
          <n-descriptions-item label="模型名称">
            {{ taskData.model_name }}
          </n-descriptions-item>
          <n-descriptions-item label="数据集">
            {{ taskData.dataset_name }}
          </n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="getStatusType(taskData.status)">
              {{ getStatusLabel(taskData.status) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="并发数">
            {{ taskData.concurrency }}
          </n-descriptions-item>
          <n-descriptions-item label="请求总数">
            {{ taskData.num_requests }}
          </n-descriptions-item>
          <n-descriptions-item label="创建时间">
            {{ formatDate(taskData.created_at) }}
          </n-descriptions-item>
        </n-descriptions>
        <n-empty v-else description="加载中..." />
      </n-spin>
    </n-card>

    <!-- 性能指标 -->
    <div v-if="taskData?.status === 'completed' && results">
      <!-- 汇总指标 -->
      <n-card title="性能汇总" style="margin-bottom: 24px;">
        <div class="metrics-grid">
          <n-statistic label="平均响应时间" :value="results.summary?.avg_response_time || 0" suffix="ms">
            <template #prefix>
              <n-icon color="#18a058"><Time /></n-icon>
            </template>
          </n-statistic>
          
          <n-statistic label="吞吐量" :value="results.summary?.throughput || 0" suffix="req/s">
            <template #prefix>
              <n-icon color="#2080f0"><TrendingUp /></n-icon>
            </template>
          </n-statistic>
          
          <n-statistic label="成功率" :value="results.summary?.success_rate || 0" suffix="%">
            <template #prefix>
              <n-icon color="#f0a020"><CheckmarkCircle /></n-icon>
            </template>
          </n-statistic>
          
          <n-statistic label="错误率" :value="results.summary?.error_rate || 0" suffix="%">
            <template #prefix>
              <n-icon color="#d03050"><CloseCircle /></n-icon>
            </template>
          </n-statistic>
        </div>
      </n-card>

      <!-- 详细指标 -->
      <n-grid :cols="2" :x-gap="24">
        <!-- 响应时间分布 -->
        <n-grid-item>
          <n-card title="响应时间分布">
            <n-descriptions :column="1" bordered size="small">
              <n-descriptions-item label="最小值">
                {{ results.details?.min_response_time || 0 }}ms
              </n-descriptions-item>
              <n-descriptions-item label="最大值">
                {{ results.details?.max_response_time || 0 }}ms
              </n-descriptions-item>
              <n-descriptions-item>
                <template #label>
                  <span
                    class="metric-label"
                    @click="showPercentileExplanation('P50')"
                    title="点击查看说明"
                  >
                    P50
                  </span>
                </template>
                {{ results.details?.p50_response_time || 0 }}ms
              </n-descriptions-item>
              <n-descriptions-item>
                <template #label>
                  <span
                    class="metric-label"
                    @click="showPercentileExplanation('P90')"
                    title="点击查看说明"
                  >
                    P90
                  </span>
                </template>
                {{ results.details?.p90_response_time || 0 }}ms
              </n-descriptions-item>
              <n-descriptions-item>
                <template #label>
                  <span
                    class="metric-label"
                    @click="showPercentileExplanation('P95')"
                    title="点击查看说明"
                  >
                    P95
                  </span>
                </template>
                {{ results.details?.p95_response_time || 0 }}ms
              </n-descriptions-item>
              <n-descriptions-item>
                <template #label>
                  <span
                    class="metric-label"
                    @click="showPercentileExplanation('P99')"
                    title="点击查看说明"
                  >
                    P99
                  </span>
                </template>
                {{ results.details?.p99_response_time || 0 }}ms
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-grid-item>

        <!-- 其他指标 -->
        <n-grid-item>
          <n-card title="其他指标">
            <n-descriptions :column="1" bordered size="small">
              <n-descriptions-item label="总耗时">
                {{ results.details?.total_duration || 0 }}s
              </n-descriptions-item>
              <n-descriptions-item label="成功请求数">
                {{ results.details?.successful_requests || 0 }}
              </n-descriptions-item>
              <n-descriptions-item label="失败请求数">
                {{ results.details?.failed_requests || 0 }}
              </n-descriptions-item>
              <n-descriptions-item label="平均Token数">
                {{ results.details?.avg_tokens || 0 }}
              </n-descriptions-item>
              <n-descriptions-item label="总Token数">
                {{ results.details?.total_tokens || 0 }}
              </n-descriptions-item>
              <n-descriptions-item label="Token/秒">
                {{ results.details?.tokens_per_second || 0 }}
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-grid-item>
      </n-grid>

      <!-- 错误信息 -->
      <n-card v-if="results.errors && results.errors.length > 0" title="错误信息" style="margin-top: 24px;">
        <n-list>
          <n-list-item v-for="(error, index) in results.errors" :key="index">
            <n-thing>
              <template #header>
                <n-text type="error">错误 {{ index + 1 }}</n-text>
              </template>
              <template #description>
                <n-text depth="3">{{ error.timestamp }}</n-text>
              </template>
              <n-text>{{ error.message }}</n-text>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-card>
    </div>

    <!-- 运行中状态 -->
    <n-card v-else-if="taskData?.status === 'running'" title="任务运行中">
      <n-space vertical align="center" style="padding: 40px 0;">
        <n-spin size="large" />
        <n-text>性能测试正在进行中，请稍候...</n-text>
        <n-text depth="3">页面将自动刷新以获取最新状态</n-text>
      </n-space>
    </n-card>

    <!-- 失败状态 -->
    <n-card v-else-if="taskData?.status === 'failed'" title="任务失败">
      <n-result status="error" title="性能测试失败" description="任务执行过程中发生错误">
        <template #footer>
          <n-space>
            <n-button @click="refreshResults">重新加载</n-button>
            <n-button type="primary" @click="$router.push('/perf-eval/create')">
              创建新测试
            </n-button>
          </n-space>
        </template>
      </n-result>
    </n-card>

    <!-- 等待状态 -->
    <n-card v-else-if="taskData?.status === 'pending'" title="等待执行">
      <n-result status="info" title="任务等待中" description="性能测试任务正在队列中等待执行">
        <template #footer>
          <n-button @click="refreshResults">刷新状态</n-button>
        </template>
      </n-result>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, h } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage, useDialog } from 'naive-ui'
import {
  Refresh,
  ArrowBack,
  Time,
  TrendingUp,
  CheckmarkCircle,
  CloseCircle
} from '@vicons/ionicons5'

const route = useRoute()
const message = useMessage()
const dialog = useDialog()

// 路由参数
const taskId = ref(route.params.taskId as string)

// 数据
const taskData = ref<any>(null)
const results = ref<any>(null)
const loading = ref(false)

// 指标说明数据
const metricExplanations = ref<any>({})
const percentileExplanations = ref<any>({})

// 自动刷新定时器
let refreshTimer: NodeJS.Timeout | null = null

// 获取指标说明数据
const fetchMetricExplanations = async () => {
  try {
    const { getMetricExplanations } = await import('@/api/performance')
    const response = await getMetricExplanations()

    if (response.success) {
      metricExplanations.value = response.data?.metric_explanations || {}
      percentileExplanations.value = response.data?.percentile_explanations || {}
    }
  } catch (error) {
    console.warn('获取指标说明失败:', error)
  }
}

// 获取任务详情和结果
const fetchTaskDetails = async () => {
  try {
    loading.value = true

    const { getPerformanceTask } = await import('@/api/performance')
    const response = await getPerformanceTask(parseInt(taskId.value))

    if (response.success) {
      taskData.value = response.data

      // 如果任务已完成且有结果数据，设置结果
      if (taskData.value?.status === 'completed' && taskData.value.results) {
        results.value = taskData.value.results
      } else if (taskData.value?.status === 'completed') {
        // 如果任务完成但没有结果数据，可能需要单独获取结果
        try {
          const { getPerformanceResults } = await import('@/api/performance')
          const resultsResponse = await getPerformanceResults(parseInt(taskId.value))
          if (resultsResponse.success) {
            results.value = resultsResponse.data
          }
        } catch (resultsError) {
          console.warn('获取结果数据失败:', resultsError)
        }
      }
    } else {
      message.error(response.error || '获取任务详情失败')
    }

  } catch (error: any) {
    console.error('获取任务详情错误:', error)
    message.error(error.message || '获取任务详情失败')
  } finally {
    loading.value = false
  }
}

// 刷新结果
const refreshResults = () => {
  fetchTaskDetails()
}

// 设置自动刷新
const setupAutoRefresh = () => {
  if (taskData.value?.status === 'running' || taskData.value?.status === 'pending') {
    refreshTimer = setInterval(() => {
      fetchTaskDetails()
    }, 5000) // 每5秒刷新一次
  }
}

// 清除自动刷新
const clearAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
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

// 显示性能指标说明
const showMetricExplanation = (metricName: string) => {
  const explanation = metricExplanations.value[metricName]
  if (explanation) {
    dialog.info({
      title: explanation.title,
      content: () => [
        h('div', { style: 'margin-bottom: 12px;' }, [
          h('strong', '说明：'),
          h('span', explanation.description)
        ]),
        h('div', [
          h('strong', '计算公式：'),
          h('span', explanation.formula)
        ])
      ],
      positiveText: '确定'
    })
  } else {
    message.info(`暂无 "${metricName}" 的详细说明`)
  }
}

// 显示百分位指标说明
const showPercentileExplanation = (metricName: string) => {
  const explanation = percentileExplanations.value[metricName]
  if (explanation) {
    dialog.info({
      title: explanation.title,
      content: () => [
        h('div', { style: 'margin-bottom: 12px;' }, [
          h('strong', '说明：'),
          h('span', explanation.description)
        ]),
        h('div', { style: 'font-size: 12px; color: #666;' }, [
          h('strong', '注：'),
          h('span', '以单个请求为单位进行统计，数据被分为100个相等部分，第n百分位表示n%的数据点在此值之下。')
        ])
      ],
      positiveText: '确定'
    })
  } else {
    message.info(`暂无 "${metricName}" 的详细说明`)
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

// 组件挂载时获取数据
onMounted(() => {
  // 获取指标说明数据
  fetchMetricExplanations()

  // 获取任务详情
  fetchTaskDetails().then(() => {
    setupAutoRefresh()
  })
})

// 组件卸载时清除定时器
onUnmounted(() => {
  clearAutoRefresh()
})
</script>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.n-card {
  margin-bottom: 16px;
}

.metric-label {
  cursor: pointer;
  border-bottom: 1px dashed #666;
  transition: all 0.2s ease;
}

.metric-label:hover {
  border-bottom-color: #2080f0;
  color: #2080f0;
}
</style>
