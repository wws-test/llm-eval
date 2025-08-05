<template>
  <div class="chat-container">
    <!-- 左侧会话列表 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <h3>对话历史</h3>
        <n-button type="primary" size="small" @click="createNewSession">
          <template #icon>
            <n-icon><Add /></n-icon>
          </template>
          新建对话
        </n-button>
      </div>

      <div class="session-list">
        <n-spin :show="sessionsLoading">
          <div v-if="sessions.length === 0" class="empty-sessions">
            <n-empty description="暂无对话记录" size="small" />
          </div>
          <div
            v-for="session in sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: currentSession?.id === session.id }"
            @click="selectSession(session)"
          >
            <div class="session-title">{{ session.title }}</div>
            <div class="session-info">
              <span class="model-name">{{ session.model_name }}</span>
              <span class="message-count">{{ session.message_count }}条消息</span>
            </div>
            <div class="session-time">
              {{ formatTime(session.updated_at) }}
            </div>
          </div>
        </n-spin>
      </div>
    </div>

    <!-- 右侧对话区域 -->
    <div class="chat-main">
      <div v-if="!currentSession" class="chat-welcome">
        <n-empty description="选择一个对话开始聊天，或创建新的对话" size="large">
          <template #icon>
            <n-icon size="64" color="#d9d9d9">
              <ChatbubbleEllipses />
            </n-icon>
          </template>
          <template #extra>
            <n-button type="primary" @click="createNewSession">
              <template #icon>
                <n-icon><Add /></n-icon>
              </template>
              开始新对话
            </n-button>
          </template>
        </n-empty>
      </div>

      <div v-else class="chat-content">
        <!-- 对话头部 -->
        <div class="chat-header">
          <div class="chat-title">
            <h3>{{ currentSession.title }}</h3>
            <n-tag type="info" size="small">{{ currentSession.model_name }}</n-tag>
          </div>
          <n-space>
            <n-button size="small" @click="clearCurrentSession">
              <template #icon>
                <n-icon><Trash /></n-icon>
              </template>
              清空对话
            </n-button>
            <n-button size="small" @click="deleteCurrentSession">
              <template #icon>
                <n-icon><Trash /></n-icon>
              </template>
              删除对话
            </n-button>
          </n-space>
        </div>

        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <n-spin :show="messagesLoading">
            <div v-if="messages.length === 0" class="empty-messages">
              <n-empty description="开始你的第一条消息吧" size="small" />
            </div>
            <div
              v-for="message in messages"
              :key="message.id"
              class="message-item"
              :class="{ 'user-message': message.role === 'user', 'assistant-message': message.role === 'assistant' }"
            >
              <div class="message-avatar">
                <n-avatar v-if="message.role === 'user'" size="small">
                  <n-icon><Person /></n-icon>
                </n-avatar>
                <n-avatar v-else size="small" color="#2080f0">
                  <n-icon><ChatbubbleEllipses /></n-icon>
                </n-avatar>
              </div>
              <div class="message-content">
                <div class="message-text">{{ message.content }}</div>
                <div class="message-time">{{ formatTime(message.created_at) }}</div>
              </div>
            </div>

            <!-- 正在输入指示器 -->
            <div v-if="isTyping" class="message-item assistant-message typing">
              <div class="message-avatar">
                <n-avatar size="small" color="#2080f0">
                  <n-icon><ChatbubbleEllipses /></n-icon>
                </n-avatar>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </n-spin>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-controls">
            <n-select
              v-model:value="selectedModelId"
              placeholder="选择模型"
              style="width: 200px;"
              :options="modelOptions"
              :loading="modelsLoading"
            />
            <n-input-number
              v-model:value="temperature"
              :min="0"
              :max="2"
              :step="0.1"
              placeholder="温度"
              style="width: 100px;"
            />
          </div>
          <div class="input-box">
            <n-input
              v-model:value="inputMessage"
              type="textarea"
              placeholder="输入你的消息..."
              :rows="3"
              :disabled="isSending"
              @keydown.ctrl.enter="sendMessage"
            />
            <div class="input-actions">
              <n-space>
                <span class="input-tip">Ctrl+Enter 发送</span>
                <n-button
                  type="primary"
                  :loading="isSending"
                  :disabled="!inputMessage.trim() || !selectedModelId"
                  @click="sendMessage"
                >
                  <template #icon>
                    <n-icon><Send /></n-icon>
                  </template>
                  发送
                </n-button>
              </n-space>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建对话模态框 -->
    <n-modal v-model:show="showNewSessionModal" preset="dialog" title="新建对话">
      <n-form
        ref="newSessionFormRef"
        :model="newSessionForm"
        :rules="newSessionRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="对话标题" path="title">
          <n-input v-model:value="newSessionForm.title" placeholder="请输入对话标题" />
        </n-form-item>

        <n-form-item label="选择模型" path="model_id">
          <n-select
            v-model:value="newSessionForm.model_id"
            placeholder="请选择AI模型"
            :options="modelOptions"
            :loading="modelsLoading"
          />
        </n-form-item>
      </n-form>

      <template #action>
        <n-space>
          <n-button @click="showNewSessionModal = false">取消</n-button>
          <n-button type="primary" :loading="creatingSession" @click="handleCreateSession">
            创建
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useMessage, useDialog, type FormInst } from 'naive-ui'
import {
  Add,
  ChatbubbleEllipses,
  Person,
  Send,
  Trash
} from '@vicons/ionicons5'

const message = useMessage()
const dialog = useDialog()

// 响应式数据
const sessions = ref<any[]>([])
const currentSession = ref<any>(null)
const messages = ref<any[]>([])
const inputMessage = ref('')
const selectedModelId = ref<number | null>(null)
const temperature = ref(0.7)
const models = ref<any[]>([])

// 加载状态
const sessionsLoading = ref(false)
const messagesLoading = ref(false)
const modelsLoading = ref(false)
const isSending = ref(false)
const isTyping = ref(false)
const creatingSession = ref(false)

// 模态框状态
const showNewSessionModal = ref(false)

// 表单相关
const newSessionFormRef = ref<FormInst | null>(null)
const newSessionForm = ref({
  title: '',
  model_id: null as number | null
})

const newSessionRules = {
  title: [
    { required: true, message: '请输入对话标题', trigger: 'blur' }
  ],
  model_id: [
    { required: true, message: '请选择AI模型', trigger: 'change' }
  ]
}

// DOM引用
const messagesContainer = ref<HTMLElement>()

// 计算属性
const modelOptions = computed(() => {
  return models.value.map(model => ({
    label: model.display_name,
    value: model.id
  }))
})

// 获取会话列表
const fetchSessions = async () => {
  try {
    sessionsLoading.value = true

    let token = localStorage.getItem('token') || localStorage.getItem('auth_token')
    if (!token) {
      token = '1'  // 使用开发者后门
      localStorage.setItem('token', token)
    }

    const response = await fetch('/api/chat/sessions', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        sessions.value = data.data.sessions
      } else {
        message.error(data.error || '获取对话列表失败')
      }
    } else {
      message.error('获取对话列表失败')
    }
  } catch (error) {
    console.error('获取对话列表错误:', error)
    message.error('网络错误，请检查连接')
  } finally {
    sessionsLoading.value = false
  }
}

// 获取模型列表
const fetchModels = async () => {
  try {
    modelsLoading.value = true

    let token = localStorage.getItem('token') || localStorage.getItem('auth_token')
    if (!token) {
      token = '1'  // 使用开发者后门
      localStorage.setItem('token', token)
    }

    const response = await fetch('/api/models', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        models.value = data.data.models.filter((model: any) => model.is_validated)
        if (models.value.length > 0 && !selectedModelId.value) {
          selectedModelId.value = models.value[0].id
        }
      } else {
        message.error(data.error || '获取模型列表失败')
      }
    } else {
      message.error('获取模型列表失败')
    }
  } catch (error) {
    console.error('获取模型列表错误:', error)
    message.error('网络错误，请检查连接')
  } finally {
    modelsLoading.value = false
  }
}

// 获取消息列表
const fetchMessages = async (sessionId: number) => {
  try {
    messagesLoading.value = true

    let token = localStorage.getItem('token') || localStorage.getItem('auth_token')
    if (!token) {
      token = '1'  // 使用开发者后门
      localStorage.setItem('token', token)
    }

    const response = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        messages.value = data.data.messages
        await nextTick()
        scrollToBottom()
      } else {
        message.error(data.error || '获取消息列表失败')
      }
    } else {
      message.error('获取消息列表失败')
    }
  } catch (error) {
    console.error('获取消息列表错误:', error)
    message.error('网络错误，请检查连接')
  } finally {
    messagesLoading.value = false
  }
}

// 选择会话
const selectSession = (session: any) => {
  currentSession.value = session
  selectedModelId.value = session.model_id
  fetchMessages(session.id)
}

// 创建新会话
const createNewSession = () => {
  newSessionForm.value = {
    title: '',
    model_id: selectedModelId.value
  }
  showNewSessionModal.value = true
}

// 处理创建会话
const handleCreateSession = async () => {
  if (!newSessionFormRef.value) return

  try {
    await newSessionFormRef.value.validate()
    creatingSession.value = true

    let token = localStorage.getItem('token') || localStorage.getItem('auth_token')
    if (!token) {
      token = '1'  // 使用开发者后门
      localStorage.setItem('token', token)
    }

    const response = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newSessionForm.value)
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        message.success('对话创建成功')
        showNewSessionModal.value = false
        await fetchSessions()

        // 自动选择新创建的会话
        const newSession = data.data
        selectSession(newSession)
      } else {
        message.error(data.error || '创建对话失败')
      }
    } else {
      message.error('创建对话失败')
    }
  } catch (error: any) {
    if (error.errors) {
      return
    }
    console.error('创建对话错误:', error)
    message.error('创建对话失败，请重试')
  } finally {
    creatingSession.value = false
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || !currentSession.value || !selectedModelId.value) {
    return
  }

  const messageContent = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息到界面
  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: messageContent,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMessage)

  await nextTick()
  scrollToBottom()

  try {
    isSending.value = true
    isTyping.value = true

    let token = localStorage.getItem('token') || localStorage.getItem('auth_token')
    if (!token) {
      token = '1'  // 使用开发者后门
      localStorage.setItem('token', token)
    }

    const response = await fetch(`/api/chat/sessions/${currentSession.value.id}/send`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: messageContent,
        model_id: selectedModelId.value,
        temperature: temperature.value
      })
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        // 添加助手回复到界面
        const assistantMessage = {
          id: data.data.id,
          role: 'assistant',
          content: data.data.content,
          created_at: data.data.created_at
        }
        messages.value.push(assistantMessage)

        await nextTick()
        scrollToBottom()

        // 更新会话列表
        fetchSessions()
      } else {
        message.error(data.error || '发送消息失败')
      }
    } else {
      message.error('发送消息失败')
    }
  } catch (error) {
    console.error('发送消息错误:', error)
    message.error('网络错误，请检查连接')
  } finally {
    isSending.value = false
    isTyping.value = false
  }
}

// 清空当前会话
const clearCurrentSession = () => {
  if (!currentSession.value) return

  dialog.warning({
    title: '确认清空',
    content: `确定要清空对话 "${currentSession.value.title}" 的所有消息吗？此操作不可恢复。`,
    positiveText: '清空',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        let token = localStorage.getItem('token') || localStorage.getItem('auth_token')
        if (!token) {
          token = '1'  // 使用开发者后门
          localStorage.setItem('token', token)
        }

        const response = await fetch(`/api/chat/sessions/${currentSession.value.id}/clear`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            message.success('对话已清空')
            messages.value = []
            fetchSessions()
          } else {
            message.error(data.error || '清空对话失败')
          }
        } else {
          message.error('清空对话失败')
        }
      } catch (error) {
        console.error('清空对话错误:', error)
        message.error('网络错误，请检查连接')
      }
    }
  })
}

// 删除当前会话
const deleteCurrentSession = () => {
  if (!currentSession.value) return

  dialog.warning({
    title: '确认删除',
    content: `确定要删除对话 "${currentSession.value.title}" 吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        let token = localStorage.getItem('token') || localStorage.getItem('auth_token')
        if (!token) {
          token = '1'  // 使用开发者后门
          localStorage.setItem('token', token)
        }

        const response = await fetch(`/api/chat/sessions/${currentSession.value.id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            message.success('对话已删除')
            currentSession.value = null
            messages.value = []
            fetchSessions()
          } else {
            message.error(data.error || '删除对话失败')
          }
        } else {
          message.error('删除对话失败')
        }
      } catch (error) {
        console.error('删除对话错误:', error)
        message.error('网络错误，请检查连接')
      }
    }
  })
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) { // 1天内
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleDateString()
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchSessions()
  fetchModels()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 120px);
  gap: 16px;
}

.chat-sidebar {
  width: 300px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e0e0e6;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e0e0e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-sessions {
  padding: 20px;
}

.session-item {
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.session-item:hover {
  background-color: #f5f5f5;
}

.session-item.active {
  background-color: #e6f7ff;
  border-color: #1890ff;
}

.session-title {
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.session-time {
  font-size: 11px;
  color: #999;
}

.chat-main {
  flex: 1;
  background: white;
  border-radius: 8px;
  border: 1px solid #e0e0e6;
  display: flex;
  flex-direction: column;
}

.chat-welcome {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 16px;
  border-bottom: 1px solid #e0e0e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-messages {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message-item.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
}

.user-message .message-content {
  text-align: right;
}

.message-text {
  background: #f5f5f5;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
  word-wrap: break-word;
}

.user-message .message-text {
  background: #1890ff;
  color: white;
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}

.user-message .message-time {
  text-align: right;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 12px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.input-area {
  border-top: 1px solid #e0e0e6;
  padding: 16px;
}

.input-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.input-box {
  position: relative;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-tip {
  font-size: 12px;
  color: #999;
}

@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
    height: auto;
  }

  .chat-sidebar {
    width: 100%;
    height: 200px;
  }

  .message-content {
    max-width: 85%;
  }
}
</style>
