<!-- src/components/business/ModelForm.vue -->
<template>
  <el-dialog
    :model-value="visible"
    :title="isEditMode ? '编辑模型' : '添加自定义模型'"
    width="600px"
    @update:model-value="$emit('update:visible', $event)"
    @closed="handleClose"
  >
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px" class="space-y-4">
      <el-form-item label="显示名称" prop="display_name">
        <el-input v-model="formData.display_name" placeholder="例如：我的 GPT-4o 模型" />
      </el-form-item>
      <el-form-item label="模型标识" prop="model_identifier">
        <el-input v-model="formData.model_identifier" placeholder="例如：gpt-4o" />
      </el-form-item>
      <el-form-item label="API Base URL" prop="api_base_url">
        <el-input v-model="formData.api_base_url" placeholder="例如：https://api.openai.com/v1" />
      </el-form-item>
      <el-form-item label="API Key" prop="api_key">
        <el-input
          v-model="formData.api_key"
          :placeholder="isEditMode ? '留空则不更改现有密钥' : '请填写API Key'"
          show-password
        />
      </el-form-item>
      <el-form-item label="提供商" prop="provider_name">
        <el-input v-model="formData.provider_name" placeholder="例如：OpenAI, Anthropic" />
      </el-form-item>
      <el-form-item label="默认Temperature" prop="default_temperature">
        <el-slider v-model="formData.default_temperature" :min="0" :max="1" :step="0.1" show-input />
      </el-form-item>
      <el-form-item label="系统提示词" prop="system_prompt">
        <el-input
          type="textarea"
          v-model="formData.system_prompt"
          :rows="3"
          placeholder="定义模型的默认行为和角色，例如：You are a helpful assistant."
        />
      </el-form-item>
      <el-form-item label="备注" prop="notes">
        <el-input type="textarea" v-model="formData.notes" :rows="2" placeholder="关于此模型的其他备注信息。" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="$emit('update:visible', false)">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="isSubmitting">
          {{ isEditMode ? '保存' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import type { AIModel } from '@/types/model';

interface Props {
  visible: boolean;
  model: AIModel | null;
}

const props = defineProps<Props>();
const emit = defineEmits(['update:visible', 'submit']);

const formRef = ref<FormInstance>();
const isSubmitting = ref(false);

const isEditMode = computed(() => !!props.model);

const getInitialFormData = (): Omit<AIModel, 'id' | 'is_system_model' | 'is_validated' | 'created_at'> & { api_key?: string } => ({
  display_name: '',
  model_identifier: '',
  api_base_url: '',
  api_key: '',
  provider_name: '',
  default_temperature: 0.7,
  system_prompt: '',
  notes: '',
  model_type: 'openai_compatible', // Default value
});

const formData = ref(getInitialFormData());

watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      if (props.model) {
        // Edit mode: copy model data, but don't include the key
        formData.value = { ...props.model, api_key: '' };
      } else {
        // Create mode: reset to initial data
        formData.value = getInitialFormData();
      }
    }
  }
);

const formRules: FormRules = {
  display_name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  model_identifier: [{ required: true, message: '请输入模型标识', trigger: 'blur' }],
  api_base_url: [{ required: true, message: '请输入API Base URL', trigger: 'blur' }],
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      isSubmitting.value = true;
      try {
        emit('submit', formData.value, props.model?.id);
      } finally {
        isSubmitting.value = false;
      }
    }
  });
};

const handleClose = () => {
  formRef.value?.resetFields();
};
</script> 