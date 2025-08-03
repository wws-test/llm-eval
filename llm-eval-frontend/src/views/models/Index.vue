<!-- src/views/models/Index.vue -->
<template>
  <div>
    <div class="prose max-w-none mb-6">
      <h1>模型管理</h1>
      <p>管理您的AI模型。系统内置模型无法修改，您可以添加、编辑或删除自定义模型。</p>
    </div>

    <div class="mb-6 text-right">
      <el-button type="primary" @click="handleAddModel">
        <el-icon class="mr-2"><Plus /></el-icon>
        添加自定义模型
      </el-button>
    </div>

    <model-table
      :models="modelsStore.models"
      :loading="modelsStore.loading"
      @validate="handleValidate"
      @edit="handleEdit"
      @delete="handleDelete"
    />
    
    <model-form
      v-model:visible="isFormVisible"
      :model="currentModel"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useModelsStore } from '@/stores/models';
import ModelTable from '@/components/business/ModelTable.vue';
import ModelForm from '@/components/business/ModelForm.vue';
import { Plus } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { AIModel } from '@/types/model';
import { validateModel as apiValidateModel } from '@/api/models';

const modelsStore = useModelsStore();
const isFormVisible = ref(false);
const currentModel = ref<AIModel | null>(null);

onMounted(() => {
  modelsStore.fetchModels();
});

const handleAddModel = () => {
  currentModel.value = null;
  isFormVisible.value = true;
};

const handleEdit = (model: AIModel) => {
  currentModel.value = model;
  isFormVisible.value = true;
};

const handleSubmit = async (formData: Partial<AIModel>, id?: number) => {
  try {
    await modelsStore.saveModel(formData, id);
    isFormVisible.value = false;
  } catch (error) {
    // Error is already handled in the store, but we catch it here
    // to prevent the dialog from closing on failure.
    console.error("Submit failed, dialog will not close.");
  }
};

const handleDelete = (model: AIModel) => {
  modelsStore.removeModel(model);
};

const handleValidate = async (model: AIModel) => {
  try {
    ElMessage.info(`正在验证模型 ${model.display_name}...`);
    await apiValidateModel(model.id);
    ElMessage.success(`模型 ${model.display_name} 验证成功！`);
    await modelsStore.fetchModels();
  } catch (error) {
    console.error(`Failed to validate model ${model.id}:`, error);
    ElMessage.error(`模型 ${model.display_name} 验证失败，请检查配置。`);
  }
};
</script>

<style scoped>
.prose h1 {
  margin-bottom: 0.5em;
}
.prose p {
  margin-top: 0;
}
</style> 