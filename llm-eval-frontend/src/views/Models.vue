<template>
  <div>
    <!-- 页面头部 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <div>
        <h1 style="margin: 0; font-size: 24px; font-weight: 600;">模型管理</h1>
        <p style="margin: 8px 0 0 0; color: #909399;">
          管理您的AI模型。系统内置模型无法修改，您可以添加、编辑或删除自定义模型。
        </p>
      </div>
      <n-space>
        <n-button @click="refreshModels" :loading="loading">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
        <n-button type="primary" @click="showModelForm()">
          <template #icon>
            <n-icon><AddIcon /></n-icon>
          </template>
          添加自定义模型
        </n-button>

      </n-space>
    </n-space>

    <!-- 模型列表 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="models"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: any) => row.id"
        striped
      />
    </n-card>

    <!-- 模型表单对话框 -->
    <n-modal
      v-model:show="showModal"
      preset="card"
      :title="formTitle"
      style="width: 600px;"
      :mask-closable="false"
    >
      <n-form
        ref="formRef"
        :model="modelForm"
        :rules="formRules"
        label-placement="top"
        require-mark-placement="right-hanging"
      >
        <n-grid :cols="2" :x-gap="16">
          <n-form-item-gi :span="2" path="display_name" label="显示名称">
            <n-input
              v-model:value="modelForm.display_name"
              placeholder="例如：我的 GPT-4o 模型"
              clearable
            />
          </n-form-item-gi>

          <n-form-item-gi :span="2" path="model_identifier" label="模型标识">
            <n-input
              v-model:value="modelForm.model_identifier"
              placeholder="例如：gpt-4o 或 claude-3-opus-20240229"
              clearable
            />
          </n-form-item-gi>

          <n-form-item-gi :span="2" path="api_base_url" label="API Base URL">
            <n-input
              v-model:value="modelForm.api_base_url"
              placeholder="例如：https://api.openai.com/v1"
              clearable
            />
          </n-form-item-gi>

          <n-form-item-gi :span="2" path="api_key" label="API Key">
            <n-input
              v-model:value="modelForm.api_key"
              type="password"
              placeholder="如需设置或更新API Key请在此填写"
              show-password-on="click"
              clearable
            />
            <template #feedback>
              <span style="color: #909399; font-size: 12px;">
                API密钥将被安全加密存储
                <span v-if="editingModel && editingModel.encrypted_api_key">(当前已设置，可修改)</span>
              </span>
            </template>
          </n-form-item-gi>

          <n-form-item-gi path="provider_name" label="提供商名称">
            <n-input
              v-model:value="modelForm.provider_name"
              placeholder="例如：OpenAI, Anthropic"
              clearable
            />
          </n-form-item-gi>

          <n-form-item-gi path="default_temperature" label="默认温度">
            <n-input-number
              v-model:value="modelForm.default_temperature"
              :min="0"
              :max="1"
              :step="0.1"
              placeholder="0.7"
              style="width: 100%;"
            />
          </n-form-item-gi>

          <n-form-item-gi :span="2" path="system_prompt" label="系统提示词">
            <n-input
              v-model:value="modelForm.system_prompt"
              type="textarea"
              placeholder="定义模型的默认行为和角色，例如：You are a helpful assistant."
              :rows="3"
            />
          </n-form-item-gi>

          <n-form-item-gi :span="2" path="notes" label="备注">
            <n-input
              v-model:value="modelForm.notes"
              type="textarea"
              placeholder="关于此模型的其他备注信息。"
              :rows="2"
            />
          </n-form-item-gi>
        </n-grid>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="closeModelForm">取消</n-button>
          <n-button type="primary" :loading="submittingForm" @click="submitModelForm">
            {{ submitButtonText }}
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>



<script setup lang="ts">
import { ref, reactive, onMounted, computed, h } from 'vue'
import { useModelsStore } from '@/stores/models'
import { useMessage, useDialog } from 'naive-ui'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import {
  Add as AddIcon,
  Checkmark as CheckIcon,
  Warning as WarningIcon,
  Create as EditIcon,
  Trash as DeleteIcon,
  Flash as ValidateIcon,
  Refresh
} from '@vicons/ionicons5'

const modelsStore = useModelsStore()
const message = useMessage()
const dialog = useDialog()

// 页面数据
const models = computed(() => modelsStore.models)
const loading = computed(() => modelsStore.loading)
const validatingModels = ref<number[]>([])

// 表单相关
const showModal = ref(false)
const formRef = ref<FormInst | null>(null)
const editingModel = ref<any>(null)
const submittingForm = ref(false)

const modelForm = reactive({
  display_name: '',
  model_identifier: '',
  api_base_url: '',
  api_key: '',
  provider_name: '',
  default_temperature: 0.7,
  system_prompt: '',
  notes: ''
})

const formRules: FormRules = {
  display_name: [
    { required: true, message: '请输入显示名称', trigger: ['input', 'blur'] }
  ],
  model_identifier: [
    { required: true, message: '请输入模型标识', trigger: ['input', 'blur'] }
  ],
  api_base_url: [
    { required: true, message: '请输入API Base URL', trigger: ['input', 'blur'] }
  ]
}

const formTitle = computed(() => {
  return editingModel.value ? '编辑模型' : '添加自定义模型'
})

const submitButtonText = computed(() => {
  return editingModel.value ? '更新模型' : '添加模型'
})

// 分页配置
const pagination = {
  pageSize: 10
}

// 表格列配置
const columns: DataTableColumns = [
  {
    title: '显示名称',
    key: 'display_name',
    render(row: any) {
      return h('div', [
        h('div', { style: 'font-weight: 600; margin-bottom: 4px;' }, row.display_name),
        h('div', [
          row.is_system_model
            ? h('n-tag', { type: 'default', size: 'small' }, '系统模型')
            : h('n-tag', { type: 'info', size: 'small' }, '自定义')
        ])
      ])
    }
  },
  {
    title: '模型标识',
    key: 'model_identifier'
  },
  {
    title: '提供商',
    key: 'provider_name',
    render(row: any) {
      return row.provider_name || 'N/A'
    }
  },
  {
    title: '类型',
    key: 'model_type',
    render(row: any) {
      if (row.model_type === 'openai_compatible') {
        return h('n-tag', { type: 'info', size: 'small' }, 'OpenAI兼容')
      }
      return h('n-tag', { size: 'small' }, row.model_type)
    }
  },
  {
    title: '验证状态',
    key: 'is_validated',
    align: 'center',
    render(row: any) {
      if (row.is_validated) {
        return h('n-icon', { size: 20, color: '#18a058' }, { default: () => h(CheckIcon) })
      } else {
        return h('n-icon', { size: 20, color: '#f0a020' }, { default: () => h(WarningIcon) })
      }
    }
  },
  {
    title: '操作',
    key: 'actions',
    align: 'center',
    render(row: any) {
      // 尝试使用原生HTML按钮
      return h('div', { style: 'display: flex; gap: 8px; align-items: center;' }, [
        // 验证按钮
        h('button', {
          style: 'padding: 4px 12px; background: #2080f0; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;',
          onClick: () => {
            console.log('🔘 点击验证按钮，模型ID:', row.id)
            validateModel(row.id)
          }
        }, '验证'),

        // 编辑按钮（仅非系统模型）
        !row.is_system_model ? h('button', {
          style: 'padding: 4px 12px; background: #f0a020; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;',
          onClick: () => {
            console.log('✏️ 点击编辑按钮，模型数据:', row)
            editModel(row)
          }
        }, '编辑') : h('button', {
          style: 'padding: 4px 12px; background: #ccc; color: #666; border: none; border-radius: 4px; cursor: not-allowed; font-size: 12px;',
          disabled: true
        }, '编辑'),

        // 删除按钮（仅非系统模型）
        !row.is_system_model ? h('button', {
          style: 'padding: 4px 12px; background: #d03050; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;',
          onClick: () => {
            console.log('🗑️ 点击删除按钮，模型数据:', row)
            confirmDeleteModel(row)
          }
        }, '删除') : h('button', {
          style: 'padding: 4px 12px; background: #ccc; color: #666; border: none; border-radius: 4px; cursor: not-allowed; font-size: 12px;',
          disabled: true
        }, '删除')
      ])
    }
  }
]

// 重置表单
const resetForm = () => {
  Object.assign(modelForm, {
    display_name: '',
    model_identifier: '',
    api_base_url: '',
    api_key: '',
    provider_name: '',
    default_temperature: 0.7,
    system_prompt: '',
    notes: ''
  })

  editingModel.value = null
}

// 显示模型表单
const showModelForm = (model?: any) => {
  resetForm()

  if (model) {
    editingModel.value = model
    Object.assign(modelForm, {
      display_name: model.display_name,
      model_identifier: model.model_identifier,
      api_base_url: model.api_base_url,
      api_key: '', // 不显示现有密钥
      provider_name: model.provider_name || '',
      default_temperature: model.default_temperature || 0.7,
      system_prompt: model.system_prompt || '',
      notes: model.notes || ''
    })
  }

  showModal.value = true
}

// 关闭模型表单
const closeModelForm = () => {
  showModal.value = false
  resetForm()
}

// 提交模型表单
const submitModelForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submittingForm.value = true

  try {
    if (editingModel.value) {
      await modelsStore.updateModel(editingModel.value.id, modelForm)
      message.success('模型更新成功！')
    } else {
      await modelsStore.createModel(modelForm)
      message.success('模型添加成功！')
    }

    closeModelForm()
    await modelsStore.fetchModels()
  } catch (error: any) {
    console.error('提交模型表单失败:', error)
    message.error(error.message || '操作失败，请重试')
  } finally {
    submittingForm.value = false
  }
}

// 编辑模型
const editModel = (model: any) => {
  showModelForm(model)
}

// 验证模型
const validateModel = async (modelId: number) => {
  validatingModels.value.push(modelId)

  try {
    await modelsStore.validateModel(modelId)
    message.success('模型验证成功！')
    await modelsStore.fetchModels() // 刷新列表以更新验证状态
  } catch (error: any) {
    console.error('验证模型失败:', error)
    message.error(error.message || '模型验证失败')
  } finally {
    validatingModels.value = validatingModels.value.filter(id => id !== modelId)
  }
}

// 确认删除模型
const confirmDeleteModel = (model: any) => {
  dialog.warning({
    title: '确认删除模型',
    content: `您确定要删除模型 "${model.display_name}" 吗？此操作无法撤销。`,
    positiveText: '确认删除',
    negativeText: '取消',
    onPositiveClick: () => deleteModel(model.id)
  })
}

// 删除模型
const deleteModel = async (modelId: number) => {
  try {
    await modelsStore.deleteModel(modelId)
    message.success('模型删除成功！')
    await modelsStore.fetchModels()
  } catch (error: any) {
    console.error('删除模型失败:', error)
    message.error(error.message || '删除模型失败')
  }
}

// 刷新模型列表
const refreshModels = async () => {
  try {
    console.log('🔄 开始刷新模型列表...')
    await modelsStore.fetchModels()
    console.log('✅ 刷新完成，当前模型数量:', models.value.length)
    console.log('📋 刷新后的模型列表:', models.value)
    message.success('模型列表刷新成功')
  } catch (error: any) {
    console.error('❌ 刷新失败:', error)
    message.error('刷新失败: ' + (error.message || '未知错误'))
  }
}

// 页面加载时获取模型列表
onMounted(async () => {
  try {
    console.log('🚀 组件挂载，开始获取模型列表...')
    await modelsStore.fetchModels()
    console.log('✅ 模型列表获取完成，当前模型数量:', models.value.length)
    console.log('📋 模型列表:', models.value)
  } catch (error: any) {
    console.error('❌ 获取模型列表失败:', error)
    message.error('获取模型列表失败: ' + (error.message || '未知错误'))
  }
})
</script>
