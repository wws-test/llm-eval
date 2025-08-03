<!-- src/components/business/ModelTable.vue -->
<template>
  <div class="overflow-x-auto shadow-lg rounded-lg">
    <el-table :data="models" v-loading="loading" style="width: 100%" row-key="id">
      <el-table-column prop="display_name" label="显示名称" min-width="180">
        <template #default="{ row }">
          <div class="font-bold">{{ row.display_name }}</div>
          <el-tag :type="row.is_system_model ? 'info' : 'success'" size="small">
            {{ row.is_system_model ? '系统模型' : '自定义' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="model_identifier" label="模型标识" min-width="200" />

      <el-table-column prop="provider_name" label="提供商" width="120" />

      <el-table-column prop="model_type" label="类型" width="150">
        <template #default="{ row }">
          <el-tag v-if="row.model_type === 'openai_compatible'" type="primary" size="small">OpenAI兼容</el-tag>
          <el-tag v-else size="small">{{ row.model_type }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="已验证" width="100" align="center">
        <template #default="{ row }">
          <el-tooltip :content="row.is_validated ? '已验证' : '未验证或验证失败'" placement="top">
            <el-icon :size="20" :color="row.is_validated ? '#67C23A' : '#E6A23C'">
              <CircleCheck v-if="row.is_validated" />
              <Warning v-else />
            </el-icon>
          </el-tooltip>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="220" align="center" fixed="right">
        <template #default="{ row }">
          <el-tooltip content="验证模型连通性" placement="top">
            <el-button link type="primary" @click="$emit('validate', row)">验证</el-button>
          </el-tooltip>
          <el-button
            link
            type="warning"
            :disabled="row.is_system_model"
            @click="$emit('edit', row)"
          >
            编辑
          </el-button>
          <el-button
            link
            type="danger"
            :disabled="row.is_system_model"
            @click="$emit('delete', row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { CircleCheck, Warning } from '@element-plus/icons-vue';
import type { AIModel } from '@/types/model';

interface Props {
  models: AIModel[];
  loading: boolean;
}

defineProps<Props>();

defineEmits(['validate', 'edit', 'delete']);
</script> 