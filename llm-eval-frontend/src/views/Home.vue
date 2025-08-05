<template>
  <div>
    <!-- 欢迎区域 -->
    <div class="hero-section">
      <n-space vertical align="center" size="large">
        <n-icon size="80" color="white">
          <Star />
        </n-icon>
        <div style="text-align: center;">
          <h1 style="font-size: 3rem; margin: 0; color: white; font-weight: 700;">
            大模型评估仪表盘
          </h1>
          <p style="font-size: 1.2rem; margin: 16px 0 0 0; color: rgba(255,255,255,0.9);">
            全面的大语言模型评估平台，提供模型管理、性能评估、效果评估、RAG评估等功能
          </p>
        </div>
      </n-space>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <n-card>
        <n-skeleton v-if="loading" text :repeat="2" />
        <n-statistic v-else label="已注册模型" :value="stats.totalModels">
          <template #prefix>
            <n-icon color="#18a058">
              <Settings />
            </n-icon>
          </template>
        </n-statistic>
      </n-card>

      <n-card>
        <n-skeleton v-if="loading" text :repeat="2" />
        <n-statistic v-else label="对话会话" :value="stats.totalChats">
          <template #prefix>
            <n-icon color="#2080f0">
              <ChatbubbleEllipses />
            </n-icon>
          </template>
        </n-statistic>
      </n-card>

      <n-card>
        <n-skeleton v-if="loading" text :repeat="2" />
        <n-statistic v-else label="评估任务" :value="stats.totalEvaluations">
          <template #prefix>
            <n-icon color="#f0a020">
              <BarChart />
            </n-icon>
          </template>
        </n-statistic>
      </n-card>

      <n-card>
        <n-skeleton v-if="loading" text :repeat="2" />
        <n-statistic v-else label="测试集" :value="stats.totalDatasets">
          <template #prefix>
            <n-icon color="#d03050">
              <Library />
            </n-icon>
          </template>
        </n-statistic>
      </n-card>
    </div>

    <!-- 功能卡片 -->
    <div class="card-grid">
      <!-- 模型管理 -->
      <n-card
        class="feature-card"
        hoverable
        @click="$router.push('/models')"
        style="cursor: pointer;"
      >
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#18a058">
              <Settings />
            </n-icon>
            <span>模型管理</span>
          </n-space>
        </template>
        <p>管理和配置AI模型，支持多种模型类型和提供商</p>
        <template #footer>
          <n-space justify="end">
            <n-button type="primary" size="small">
              前往管理
            </n-button>
          </n-space>
        </template>
      </n-card>

      <!-- 智能对话 -->
      <n-card
        class="feature-card"
        hoverable
        @click="$router.push('/chat')"
        style="cursor: pointer;"
      >
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#2080f0">
              <ChatbubbleEllipses />
            </n-icon>
            <span>智能对话</span>
          </n-space>
        </template>
        <p>与AI模型进行智能对话，体验先进的语言理解能力</p>
        <template #footer>
          <n-space justify="space-between">
            <n-button size="small" @click.stop="$router.push('/chat/history')">
              查看历史
            </n-button>
            <n-button type="primary" size="small">
              开始对话
            </n-button>
          </n-space>
        </template>
      </n-card>

      <!-- 测试集管理 -->
      <n-card
        class="feature-card"
        hoverable
        @click="$router.push('/datasets')"
        style="cursor: pointer;"
      >
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#d03050">
              <Library />
            </n-icon>
            <span>测试集管理</span>
          </n-space>
        </template>
        <p>管理评估数据集，支持多种格式的数据导入和预处理</p>
        <template #footer>
          <n-space justify="end">
            <n-button type="primary" size="small">
              管理测试集
            </n-button>
          </n-space>
        </template>
      </n-card>

      <!-- 效果评估 -->
      <n-card
        class="feature-card"
        hoverable
        @click="$router.push('/evaluations')"
        style="cursor: pointer;"
      >
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#f0a020">
              <BarChart />
            </n-icon>
            <span>效果评估</span>
          </n-space>
        </template>
        <p>评估模型在各种任务上的表现，生成详细的评估报告</p>
        <template #footer>
          <n-space justify="space-between">
            <n-button size="small" @click.stop="$router.push('/evaluations')">
              查看历史
            </n-button>
            <n-button type="primary" size="small">
              开始评估
            </n-button>
          </n-space>
        </template>
      </n-card>

      <!-- 性能评估 -->
      <n-card
        class="feature-card"
        hoverable
        @click="$router.push('/perf-eval')"
        style="cursor: pointer;"
      >
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#18a058">
              <Rocket />
            </n-icon>
            <span>性能评估</span>
          </n-space>
        </template>
        <p>测试模型的响应速度、吞吐量和资源消耗等性能指标</p>
        <template #footer>
          <n-space justify="space-between">
            <n-button size="small" @click.stop="$router.push('/perf-eval/history')">
              查看历史
            </n-button>
            <n-button type="primary" size="small">
              性能测试
            </n-button>
          </n-space>
        </template>
      </n-card>

      <!-- RAG评估 -->
      <n-card
        class="feature-card"
        hoverable
        @click="$router.push('/rag-eval')"
        style="cursor: pointer;"
      >
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#2080f0">
              <Search />
            </n-icon>
            <span>RAG评估</span>
          </n-space>
        </template>
        <p>评估检索增强生成系统的准确性和相关性</p>
        <template #footer>
          <n-space justify="space-between">
            <n-button size="small" @click.stop="$router.push('/rag-eval/history')">
              查看历史
            </n-button>
            <n-button type="primary" size="small">
              RAG评估
            </n-button>
          </n-space>
        </template>
      </n-card>

      <!-- 即将推出 -->
      <n-card class="feature-card" style="border: 2px dashed #d9d9d9;">
        <template #header>
          <n-space align="center">
            <n-icon size="24" color="#909399">
              <Time />
            </n-icon>
            <span style="color: #909399;">即将推出</span>
          </n-space>
        </template>
        <p style="color: #909399;">更多功能正在开发中...</p>
        <n-space vertical size="small">
          <n-tag type="warning" size="small">安全评估</n-tag>
          <n-tag type="info" size="small">多模态评估</n-tag>
        </n-space>
      </n-card>
    </div>

    <!-- 快速操作 -->
    <n-card title="快速操作" style="margin-top: 24px;">
      <n-space>
        <n-button type="primary" @click="$router.push('/models')">
          <template #icon>
            <n-icon><Add /></n-icon>
          </template>
          添加模型
        </n-button>
        <n-button @click="$router.push('/chat')">
          <template #icon>
            <n-icon><ChatbubbleEllipses /></n-icon>
          </template>
          开始对话
        </n-button>
        <n-button @click="$router.push('/evaluations/create')">
          <template #icon>
            <n-icon><Play /></n-icon>
          </template>
          创建评估
        </n-button>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  Star,
  Settings,
  ChatbubbleEllipses,
  BarChart,
  Library,
  Rocket,
  Search,
  Time,
  Add,
  Play
} from '@vicons/ionicons5'

const message = useMessage()

// 统计数据
const stats = ref({
  totalModels: 0,
  totalChats: 0,
  totalEvaluations: 0,
  totalDatasets: 0
})

// 加载状态
const loading = ref(true)

// 获取统计数据
const fetchStats = async () => {
  try {
    loading.value = true

    const { getDashboardStats } = await import('@/api/stats')
    const data = await getDashboardStats()

    const overview = data.data.overview
    stats.value = {
      totalModels: overview.total_models,
      totalChats: overview.total_chats,
      totalEvaluations: overview.total_evaluations,
      totalDatasets: overview.total_datasets
    }
  } catch (error: any) {
    console.error('获取统计数据错误:', error)
    message.error(error.message || '获取统计数据失败')
  } finally {
    loading.value = false
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchStats()
})
</script>
