<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <el-button type="primary" @click="createNewSession" :icon="Plus" plain>
        新对话
      </el-button>
    </div>
    <el-menu
      :default-active="chatStore.currentSessionId"
      class="sidebar-menu"
      @select="handleSelectSession"
    >
      <el-menu-item
        v-for="session in chatStore.sessions"
        :key="session.id"
        :index="session.id"
      >
        <template #title>
          <div class="session-item">
            <span class="session-title">{{ session.title }}</span>
            <el-button
              type="danger"
              :icon="Delete"
              size="small"
              circle
              plain
              @click.stop="deleteSession(session.id)"
            />
          </div>
        </template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '@/stores/chat'
import { useModelStore } from '@/stores/model'
import { Plus, Delete } from '@element-plus/icons-vue'

const chatStore = useChatStore()
const modelStore = useModelStore()

const createNewSession = () => {
  const defaultModelId = modelStore.models.length > 0 ? modelStore.models[0].id : 'default-model'
  chatStore.createSession(defaultModelId)
}

const handleSelectSession = (sessionId: string) => {
  chatStore.selectSession(sessionId)
}

const deleteSession = (sessionId: string) => {
  chatStore.deleteSession(sessionId)
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header .el-button {
  width: 100%;
}

.sidebar-menu {
  flex-grow: 1;
  border-right: none;
  overflow-y: auto;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.session-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 8px;
}
</style> 