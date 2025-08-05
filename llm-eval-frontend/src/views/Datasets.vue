<template>
  <div>
    <!-- 页面头部 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <div>
        <h1 style="margin: 0; font-size: 24px; font-weight: 600;">测试集管理</h1>
        <p style="margin: 8px 0 0 0; color: #909399;">
          管理评估数据集，支持多种格式的数据导入和预处理
        </p>
      </div>
      <n-button type="primary" @click="showUploadModal = true">
        <template #icon>
          <n-icon><Add /></n-icon>
        </template>
        上传数据集
      </n-button>
    </n-space>

    <!-- 搜索和筛选 -->
    <n-card style="margin-bottom: 16px;">
      <n-space>
        <n-input
          v-model:value="searchQuery"
          placeholder="搜索数据集名称或描述..."
          style="width: 300px;"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <n-icon><Search /></n-icon>
          </template>
        </n-input>

        <n-select
          v-model:value="selectedType"
          placeholder="数据集类型"
          style="width: 150px;"
          clearable
          @update:value="handleTypeFilter"
          :options="datasetTypeOptions"
        />

        <n-button @click="refreshDatasets">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
      </n-space>
    </n-card>

    <!-- 数据集列表 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="datasets"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: any) => row.id"
        striped
      />
    </n-card>

    <!-- 上传数据集模态框 -->
    <n-modal v-model:show="showUploadModal" preset="dialog" title="上传数据集">
      <template #header>
        <div>上传数据集</div>
      </template>
      <n-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="数据集名称" path="name">
          <n-input v-model:value="uploadForm.name" placeholder="请输入数据集名称" />
        </n-form-item>

        <n-form-item label="数据集类型" path="dataset_type">
          <n-select
            v-model:value="uploadForm.dataset_type"
            placeholder="请选择数据集类型"
            :options="datasetTypeOptions"
          />
        </n-form-item>

        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="uploadForm.description"
            type="textarea"
            placeholder="请输入数据集描述（可选）"
            :rows="3"
          />
        </n-form-item>

        <n-form-item label="数据文件" path="file">
          <n-upload
            ref="uploadRef"
            :file-list="fileList"
            :max="1"
            accept=".json,.jsonl"
            @change="handleFileChange"
            @remove="handleFileRemove"
          >
            <n-upload-dragger>
              <div style="margin-bottom: 12px">
                <n-icon size="48" :depth="3">
                  <CloudUpload />
                </n-icon>
              </div>
              <n-text style="font-size: 16px">
                点击或者拖动文件到该区域来上传
              </n-text>
              <n-p depth="3" style="margin: 8px 0 0 0">
                支持 JSON 和 JSONL 格式文件，单个文件大小不超过 50MB
              </n-p>
            </n-upload-dragger>
          </n-upload>
        </n-form-item>
      </n-form>

      <template #action>
        <n-space>
          <n-button @click="showUploadModal = false">取消</n-button>
          <n-button type="primary" :loading="uploading" @click="handleUpload">
            上传
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 数据预览模态框 -->
    <n-modal v-model:show="showPreviewModal" style="width: 80%; max-width: 1200px;">
      <n-card
        :title="`数据预览 - ${currentPreviewDataset?.name}`"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <template #header-extra>
          <n-button quaternary circle @click="showPreviewModal = false">
            <template #icon>
              <n-icon><Close /></n-icon>
            </template>
          </n-button>
        </template>

        <n-spin :show="previewLoading">
          <div v-if="previewData && previewData.length > 0">
            <n-space style="margin-bottom: 16px;">
              <n-tag type="info">
                总记录数: {{ currentPreviewDataset?.record_count || 0 }}
              </n-tag>
              <n-tag type="success">
                预览: {{ previewData.length }} 条
              </n-tag>
            </n-space>

            <n-data-table
              :columns="previewColumns"
              :data="previewData"
              :max-height="400"
              :scroll-x="800"
            />
          </div>
          <n-empty v-else description="暂无数据" />
        </n-spin>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useMessage, useDialog, type DataTableColumns, type FormInst, type UploadFileInfo } from 'naive-ui'
import {
  Add,
  Search,
  Refresh,
  CloudUpload,
  Close,
  Eye,
  Trash
} from '@vicons/ionicons5'

const message = useMessage()
const dialog = useDialog()

// 响应式数据
const datasets = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const selectedType = ref<string | null>(null)
const showUploadModal = ref(false)
const showPreviewModal = ref(false)
const uploading = ref(false)
const previewLoading = ref(false)
const previewData = ref<any[]>([])
const currentPreviewDataset = ref<any>(null)

// 表单相关
const uploadFormRef = ref<FormInst | null>(null)
const uploadRef = ref()
const fileList = ref<UploadFileInfo[]>([])

// 上传表单数据
const uploadForm = ref({
  name: '',
  dataset_type: '',
  description: '',
  file: null as File | null
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
    fetchDatasets()
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
    fetchDatasets()
  }
})

// 数据集类型选项
const datasetTypeOptions = [
  { label: 'QA问答', value: 'qa' },
  { label: '多选题', value: 'mcq' },
  { label: 'RAG评估', value: 'rag' },
  { label: '自定义', value: 'custom' }
]

// 表单验证规则
const uploadRules = {
  name: [
    { required: true, message: '请输入数据集名称', trigger: 'blur' }
  ],
  dataset_type: [
    { required: true, message: '请选择数据集类型', trigger: 'change' }
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
    title: '名称',
    key: 'name',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '类型',
    key: 'dataset_type',
    width: 100,
    render(row: any) {
      const typeMap: Record<string, string> = {
        'qa': 'QA问答',
        'mcq': '多选题',
        'rag': 'RAG评估',
        'custom': '自定义'
      }
      return typeMap[row.dataset_type] || row.dataset_type
    }
  },
  {
    title: '记录数',
    key: 'record_count',
    width: 100
  },
  {
    title: '文件大小',
    key: 'file_size',
    width: 120,
    render(row: any) {
      if (!row.file_size) return '-'
      const size = row.file_size
      if (size < 1024) return `${size} B`
      if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
      return `${(size / (1024 * 1024)).toFixed(1)} MB`
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row: any) {
      return row.created_at ? new Date(row.created_at).toLocaleString() : '-'
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    align: 'center',
    render(row: any) {
      return h('div', { style: 'display: flex; gap: 8px; justify-content: center;' }, [
        // 预览按钮
        h('button', {
          style: 'padding: 4px 12px; background: #2080f0; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 4px;',
          onClick: () => {
            console.log('👁️ 点击预览按钮，数据集:', row)
            previewDataset(row)
          }
        }, [
          h('span', '👁️'),
          h('span', '预览')
        ]),

        // 删除按钮（只有自己创建的数据集才能删除）
        row.source === 'admin' || row.source === null ?
          h('button', {
            style: 'padding: 4px 12px; background: #d03050; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 4px;',
            onClick: () => {
              console.log('🗑️ 点击删除按钮，数据集:', row)
              confirmDeleteDataset(row)
            }
          }, [
            h('span', '🗑️'),
            h('span', '删除')
          ]) :
          h('button', {
            style: 'padding: 4px 12px; background: #ccc; color: #666; border: none; border-radius: 4px; cursor: not-allowed; font-size: 12px; display: flex; align-items: center; gap: 4px;',
            disabled: true,
            title: '只能删除自己创建的数据集'
          }, [
            h('span', '🗑️'),
            h('span', '删除')
          ])
      ])
    }
  }
]

// 预览表格列（动态生成）
const previewColumns = ref<DataTableColumns>([])

// 获取数据集列表
const fetchDatasets = async () => {
  try {
    loading.value = true

    const params = new URLSearchParams()
    params.append('page', pagination.value.page.toString())
    params.append('per_page', pagination.value.pageSize.toString())

    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    if (selectedType.value) {
      params.append('dataset_type', selectedType.value)
    }

    let token = localStorage.getItem('auth_token') || localStorage.getItem('token')

    // 如果没有token，为内部项目设置一个默认token（与request.ts保持一致）
    if (!token) {
      token = 'dev'  // 使用后端的开发者后门token
      localStorage.setItem('auth_token', token)
    }

    if (!token) {
      message.error('请先登录')
      return
    }

    const response = await fetch(`/api/datasets?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()

      if (data.success) {
        datasets.value = data.data.datasets
        pagination.value.itemCount = data.data.total
      } else {
        message.error(data.error || '获取数据集列表失败')
      }
    } else {
      message.error('获取数据集列表失败')
    }
  } catch (error) {
    console.error('获取数据集列表错误:', error)
    message.error('网络错误，请检查连接')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.value.page = 1
  fetchDatasets()
}

// 类型筛选处理
const handleTypeFilter = () => {
  pagination.value.page = 1
  fetchDatasets()
}

// 刷新数据集
const refreshDatasets = () => {
  fetchDatasets()
}

// 文件上传处理
const handleFileChange = (options: { fileList: UploadFileInfo[] }) => {
  fileList.value = options.fileList
  if (options.fileList.length > 0) {
    uploadForm.value.file = options.fileList[0].file as File
  } else {
    uploadForm.value.file = null
  }
}

// 文件移除处理
const handleFileRemove = () => {
  fileList.value = []
  uploadForm.value.file = null
}

// 上传数据集
const handleUpload = async () => {
  if (!uploadFormRef.value) return

  try {
    await uploadFormRef.value.validate()

    if (!uploadForm.value.file) {
      message.error('请选择要上传的文件')
      return
    }

    uploading.value = true

    const formData = new FormData()
    formData.append('name', uploadForm.value.name)
    formData.append('dataset_type', uploadForm.value.dataset_type)
    formData.append('description', uploadForm.value.description)
    formData.append('file', uploadForm.value.file)

    let token = localStorage.getItem('auth_token') || localStorage.getItem('token')
    if (!token) {
      token = 'dev'
      localStorage.setItem('auth_token', token)
    }

    const response = await fetch('/api/datasets/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        message.success('数据集上传成功')
        showUploadModal.value = false
        resetUploadForm()
        fetchDatasets()
      } else {
        message.error(data.error || '上传失败')
      }
    } else {
      message.error('上传失败')
    }
  } catch (error: any) {
    if (error.errors) {
      // 表单验证错误
      return
    }
    console.error('上传数据集错误:', error)
    message.error('上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

// 重置上传表单
const resetUploadForm = () => {
  uploadForm.value = {
    name: '',
    dataset_type: '',
    description: '',
    file: null
  }
  fileList.value = []
}

// 预览数据集
const previewDataset = async (dataset: any) => {
  try {
    previewLoading.value = true
    currentPreviewDataset.value = dataset
    showPreviewModal.value = true

    let token = localStorage.getItem('auth_token') || localStorage.getItem('token')
    if (!token) {
      token = 'dev'
      localStorage.setItem('auth_token', token)
    }

    const response = await fetch(`/api/datasets/${dataset.id}/preview`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        previewData.value = data.data.preview || []

        // 动态生成预览表格列
        if (previewData.value && previewData.value.length > 0) {
          const firstRow = previewData.value[0]
          previewColumns.value = Object.keys(firstRow).map(key => ({
            title: key,
            key: key,
            ellipsis: {
              tooltip: true
            },
            width: 200
          }))
        } else {
          previewColumns.value = []
        }
      } else {
        message.error(data.error || '获取预览数据失败')
      }
    } else {
      message.error('获取预览数据失败')
    }
  } catch (error) {
    console.error('预览数据集错误:', error)
    message.error('网络错误，请检查连接')
  } finally {
    previewLoading.value = false
  }
}

// 确认删除数据集
const confirmDeleteDataset = (dataset: any) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除数据集 "${dataset.name}" 吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => deleteDataset(dataset)
  })
}

// 删除数据集
const deleteDataset = async (dataset: any) => {
  try {
    let token = localStorage.getItem('auth_token') || localStorage.getItem('token')
    if (!token) {
      token = 'dev'
      localStorage.setItem('auth_token', token)
    }

    const response = await fetch(`/api/datasets/${dataset.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        message.success('数据集删除成功')
        fetchDatasets()
      } else {
        message.error(data.error || '删除失败')
      }
    } else {
      message.error('删除失败')
    }
  } catch (error) {
    console.error('删除数据集错误:', error)
    message.error('网络错误，请检查连接')
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchDatasets()
})
</script>
