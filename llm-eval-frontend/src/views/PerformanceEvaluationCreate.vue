<template>
  <div>
    <!-- 页面头部 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <div>
        <h1 style="margin: 0; font-size: 24px; font-weight: 600;">创建性能测试</h1>
        <p style="margin: 8px 0 0 0; color: #909399;">
          配置性能测试参数，评估模型的响应速度和吞吐量
        </p>
      </div>
      <n-button @click="$router.back()">
        <template #icon>
          <n-icon><ArrowBack /></n-icon>
        </template>
        返回
      </n-button>
    </n-space>

    <!-- 创建表单 -->
    <n-card>
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="120px"
        require-mark-placement="right-hanging"
      >
        <n-grid :cols="2" :x-gap="24">
          <!-- 基础配置 -->
          <n-grid-item>
            <n-card title="基础配置" size="small">
              <n-form-item label="选择模型" path="modelId">
                <n-select
                  v-model:value="formData.modelId"
                  placeholder="请选择要测试的模型"
                  :options="modelOptions"
                  :loading="modelsLoading"
                  clearable
                />
              </n-form-item>

              <n-form-item label="测试数据集" path="datasetId">
                <n-select
                  v-model:value="formData.datasetId"
                  placeholder="请选择测试数据集"
                  :options="datasetOptions"
                  :loading="datasetsLoading"
                  clearable
                />
              </n-form-item>

              <n-form-item label="并发数" path="concurrency">
                <n-input-number
                  v-model:value="formData.concurrency"
                  placeholder="并发请求数量"
                  :min="1"
                  :max="100"
                  style="width: 100%"
                />
                <template #feedback>
                  同时发送的请求数量，建议从小开始测试
                </template>
              </n-form-item>

              <n-form-item label="请求总数" path="numRequests">
                <n-input-number
                  v-model:value="formData.numRequests"
                  placeholder="总请求数量"
                  :min="1"
                  :max="10000"
                  style="width: 100%"
                />
                <template #feedback>
                  总共发送的请求数量
                </template>
              </n-form-item>
            </n-card>
          </n-grid-item>

          <!-- 高级配置 -->
          <n-grid-item>
            <n-card title="高级配置" size="small">
              <n-form-item label="最小Prompt长度">
                <n-input-number
                  v-model:value="formData.minPromptLength"
                  placeholder="最小输入长度"
                  :min="1"
                  style="width: 100%"
                />
              </n-form-item>

              <n-form-item label="最大Prompt长度">
                <n-input-number
                  v-model:value="formData.maxPromptLength"
                  placeholder="最大输入长度"
                  :min="1"
                  style="width: 100%"
                />
              </n-form-item>

              <n-form-item label="最大生成Token数">
                <n-input-number
                  v-model:value="formData.maxTokens"
                  placeholder="最大生成Token数"
                  :min="1"
                  :max="4096"
                  style="width: 100%"
                />
              </n-form-item>

              <n-form-item label="额外参数">
                <n-input
                  v-model:value="formData.extraArgs"
                  type="textarea"
                  placeholder='JSON格式的额外参数，如: {"temperature": 0.7}'
                  :rows="3"
                />
                <template #feedback>
                  JSON格式的额外请求参数（可选）
                </template>
              </n-form-item>
            </n-card>
          </n-grid-item>
        </n-grid>

        <!-- 提示信息 -->
        <n-alert type="info" style="margin-top: 24px;">
          <template #header>
            <n-icon><InformationCircle /></n-icon>
            性能评估说明
          </template>
          <ul style="margin: 8px 0; padding-left: 20px;">
            <li>性能评估将测试模型的响应速度、吞吐量和延迟等指标</li>
            <li>评估过程可能需要几分钟到几十分钟，具体取决于请求数量和并发数</li>
            <li>建议先使用较小的参数进行测试，确认配置正确后再进行大规模评估</li>
            <li>可以配置输入输出的限制参数，如最小/最大输入长度、最大生成token数等</li>
          </ul>
        </n-alert>

        <!-- 操作按钮 -->
        <n-space justify="end" style="margin-top: 24px;">
          <n-button @click="resetForm">重置</n-button>
          <n-button type="primary" :loading="submitting" @click="submitForm">
            创建并开始测试
          </n-button>
        </n-space>
      </n-form>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, type FormInst, type FormRules } from 'naive-ui'
import { ArrowBack, InformationCircle } from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()

// 表单引用
const formRef = ref<FormInst | null>(null)

// 表单数据
const formData = reactive({
  modelId: null as number | null,
  datasetId: null as number | null,
  concurrency: 5,  // 与后端默认值一致
  numRequests: 20, // 与后端默认值一致
  minPromptLength: 0 as number | null,
  maxPromptLength: 131072 as number | null,
  maxTokens: null as number | null,
  extraArgs: ''
})

// 表单验证规则
const formRules: FormRules = {
  modelId: [
    { required: true, message: '请选择模型', type: 'number', trigger: 'change' }
  ],
  datasetId: [
    { required: true, message: '请选择数据集', type: 'number', trigger: 'change' }
  ],
  concurrency: [
    { required: true, message: '请输入并发数', type: 'number', trigger: 'blur' },
    { type: 'number', min: 1, max: 100, message: '并发数应在1-100之间', trigger: 'blur' }
  ],
  numRequests: [
    { required: true, message: '请输入请求总数', type: 'number', trigger: 'blur' },
    { type: 'number', min: 1, max: 10000, message: '请求总数应在1-10000之间', trigger: 'blur' }
  ]
}

// 选项数据
const modelOptions = ref<Array<{ label: string; value: number }>>([])
const datasetOptions = ref<Array<{ label: string; value: number }>>([])

// 加载状态
const modelsLoading = ref(false)
const datasetsLoading = ref(false)
const submitting = ref(false)

// 获取模型列表
const fetchModels = async () => {
  try {
    modelsLoading.value = true

    const { getAvailableModels } = await import('@/api/performance')
    const response = await getAvailableModels()

    if (response.success) {
      modelOptions.value = (response.data || []).map(model => ({
        label: model.display_name,
        value: model.id
      }))
    } else {
      message.error(response.error || '获取模型列表失败')
    }
  } catch (error: any) {
    console.error('获取模型列表错误:', error)
    message.error(error.message || '获取模型列表失败')
  } finally {
    modelsLoading.value = false
  }
}

// 获取数据集列表
const fetchDatasets = async () => {
  try {
    datasetsLoading.value = true

    const { getAvailableDatasets } = await import('@/api/performance')
    const response = await getAvailableDatasets()

    if (response.success) {
      datasetOptions.value = (response.data || []).map(dataset => ({
        label: dataset.id === -1 ? `${dataset.name} (内置)` : dataset.name,
        value: dataset.id
      }))
    } else {
      message.error(response.error || '获取数据集列表失败')
    }
  } catch (error: any) {
    console.error('获取数据集列表错误:', error)
    message.error(error.message || '获取数据集列表失败')
  } finally {
    datasetsLoading.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.restoreValidation()
  Object.assign(formData, {
    modelId: null,
    datasetId: null,
    concurrency: 5,
    numRequests: 20,
    minPromptLength: 0,
    maxPromptLength: 131072,
    maxTokens: null,
    extraArgs: ''
  })
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  try {
    submitting.value = true

    // 验证额外参数JSON格式
    if (formData.extraArgs) {
      try {
        JSON.parse(formData.extraArgs)
      } catch {
        message.error('额外参数必须是有效的JSON格式')
        return
      }
    }

    const { createPerformanceTask } = await import('@/api/performance')
    const response = await createPerformanceTask({
      model_id: formData.modelId!,
      dataset_id: formData.datasetId!,
      concurrency: formData.concurrency,
      num_requests: formData.numRequests,
      min_prompt_length: formData.minPromptLength || undefined,
      max_prompt_length: formData.maxPromptLength || undefined,
      max_tokens: formData.maxTokens || undefined,
      extra_args: formData.extraArgs || undefined
    })

    if (response.success) {
      message.success('性能测试任务创建成功！')
      // 跳转到结果页面
      router.push(`/perf-eval/results/${response.data?.id}`)
    } else {
      message.error(response.error || '创建任务失败')
    }

  } catch (error: any) {
    console.error('创建性能测试任务错误:', error)
    message.error(error.message || '创建任务失败')
  } finally {
    submitting.value = false
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchModels()
  fetchDatasets()
})
</script>

<style scoped>
.n-card {
  margin-bottom: 16px;
}
</style>
