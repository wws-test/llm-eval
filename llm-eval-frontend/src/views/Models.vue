<template>
  <div class="models-container">
    <h2>模型管理</h2>
    <el-table :data="models" style="width: 100%">
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="provider" label="提供商" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="selectModel(row)">选择</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const models = ref([
  { id: "1", name: "GPT-4", provider: "OpenAI" },
  { id: "2", name: "Claude-3", provider: "Anthropic" },
  { id: "3", name: "Qwen-72B", provider: "Alibaba" }
]);

const selectModel = (model: any) => {
  console.log("选择模型:", model);
};
</script>

<style scoped>
.models-container { padding: 2rem; }
</style>
