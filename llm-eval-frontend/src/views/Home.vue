<template>
  <div class="home">
    <h1>LLM-Eval 平台</h1>
    <p>欢迎使用大型语言模型评估平台</p>
    <el-button type="primary" @click="$router.push('/chat')">开始对话</el-button>
  </div>
</template>

<script setup lang="ts">
// 首页组件
</script>

<style scoped>
.home {
  text-align: center;
  padding: 60px 20px;
}

h1 {
  color: #409eff;
  margin-bottom: 20px;
}

p {
  color: #666;
  margin-bottom: 30px;
  font-size: 18px;
}
</style>
