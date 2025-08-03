<template>
  <el-container class="layout-container">
    <el-header class="header">
      <div class="header-content">
        <h1>LLM-Eval 平台</h1>
        <el-menu :default-active="$route.path" class="nav-menu" mode="horizontal" router>
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/chat">对话</el-menu-item>
          <el-menu-item index="/models">模型</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.layout-container { min-height: 100vh; background-color: #f0f2f5; }
.header { background-color: #fff; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); padding: 0 40px; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; height: 100%; }
.header h1 { margin: 0; color: #409eff; font-size: 24px; }
.nav-menu { border-bottom: none; background-color: transparent; }
.main-content { max-width: 1200px; margin: 20px auto; padding: 24px; background-color: #fff; border-radius: 4px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1); }
</style>
