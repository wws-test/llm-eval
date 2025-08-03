<!-- src/views/Chat.vue -->
<template>
  <div class="chat-container">
    <SideBar />
    <div class="chat-main">
      <div v-if="currentSession">
        <vue-advanced-chat
          :current-user-id="currentUserId"
          :rooms="JSON.stringify(rooms)"
          :messages="JSON.stringify(formattedMessages)"
          :message-actions="JSON.stringify(messageActions)"
          @send-message="handleSendMessage($event.detail[0])"
          :loading-messages="isLoading"
        />
      </div>
      <div v-else class="no-session">
        <el-empty description="请选择或创建一个新的对话">
          <el-button type="primary" @click="createNewSession"
            >创建新对话</el-button
          >
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { register } from 'vue-advanced-chat'
import 'vue-advanced-chat/dist/vue-advanced-chat.css'
import { useChatStore } from '@/stores/chat'
import { useModelStore } from '@/stores/model' // Assuming you have a model store
import SideBar from '@/components/business/chat/SideBar.vue'

// Register vue-advanced-chat component
register()

const chatStore = useChatStore()
const modelStore = useModelStore()

const currentUserId = ref('current-user') // Static user ID

const rooms = computed(() => {
  if (!chatStore.currentSession) return []
  return [
    {
      roomId: chatStore.currentSession.id,
      roomName: chatStore.currentSession.title,
      avatar: 'https://64.media.tumblr.com/avatar_563d31614f60_128.png', // Placeholder avatar
      users: [
        { _id: currentUserId.value, username: 'You' },
        { _id: 'assistant', username: 'Assistant' },
      ],
    },
  ]
})

const formattedMessages = computed(() => {
  if (!chatStore.currentSession) return []
  return chatStore.currentSession.messages.map((msg) => ({
    _id: msg.id,
    content: msg.content,
    senderId: msg.role === 'user' ? currentUserId.value : 'assistant',
    username: msg.role === 'user' ? 'You' : 'Assistant',
    timestamp: msg.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    date: msg.timestamp.toLocaleDateString(),
    disableActions: msg.streaming,
    disableReactions: msg.streaming,
  }))
})

const isLoading = computed(() => chatStore.isLoading)

const messageActions = ref([
    { name: 'replyMessage', title: 'Reply' },
    { name: 'editMessage', title: 'Edit Message', onlyMe: true },
    { name: 'deleteMessage', title: 'Delete Message', onlyMe: true },
])


const handleSendMessage = (message: any) => {
  chatStore.sendMessage(message.content)
}

const createNewSession = () => {
  // Use the first available model as default, or a fallback
  const defaultModelId = modelStore.models.length > 0 ? modelStore.models[0].id : 'default-model'
  chatStore.createSession(defaultModelId)
}

onMounted(() => {
  // If no session is selected, and there are existing sessions, select the first one.
  if (!chatStore.currentSession && chatStore.sessions.length > 0) {
    chatStore.selectSession(chatStore.sessions[0].id)
  }
})

// Watch for changes in the current session and potentially load history
watch(
  () => chatStore.currentSessionId,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      chatStore.loadChatHistory(newId)
    }
  },
  { immediate: true }
)
</script>

<style>
.chat-container {
  display: flex;
  height: calc(100vh - 60px); /* Adjust based on your header's height */
}

.chat-main {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.no-session {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
}

/* vue-advanced-chat style overrides */
.vac-room-header {
  background-color: #409eff !important;
  color: white !important;
}

.vac-card-info {
  border-radius: 8px !important;
}

.vac-message-box {
  border-radius: 8px !important;
}
</style>
