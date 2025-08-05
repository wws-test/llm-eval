import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  streaming?: boolean
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  modelId: string
  createdAt: Date
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<any>(null)

  const currentSession = computed(() => {
    return sessions.value.find((s) => s.id === currentSessionId.value) || null
  })

  const createSession = (modelId: string) => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: '新的对话',
      messages: [],
      modelId: modelId,
      createdAt: new Date(),
    }
    sessions.value.unshift(newSession)
    currentSessionId.value = newSession.id
    return newSession
  }

  const selectSession = (sessionId: string | null) => {
    currentSessionId.value = sessionId
  }

  const deleteSession = (sessionId: string) => {
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = sessions.value.length > 0 ? sessions.value[0].id : null
    }
  }

  const sendMessage = async (content: string) => {
    if (!currentSession.value) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    }
    currentSession.value.messages.push(userMessage)

    if (currentSession.value.messages.length === 1) {
      currentSession.value.title = content.substring(0, 20)
    }

    // 模拟AI回复
    const assistantMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '这是一个模拟回复，对话功能正在开发中。',
      timestamp: new Date(),
    }

    setTimeout(() => {
      currentSession.value?.messages.push(assistantMessage)
    }, 1000)
  }

  const loadChatHistory = async (sessionId: string) => {
    console.log(`Loading history for session ${sessionId}...`)
  }

  return {
    sessions,
    currentSessionId,
    isLoading,
    error,
    currentSession,
    createSession,
    selectSession,
    deleteSession,
    sendMessage,
    loadChatHistory
  }
})
