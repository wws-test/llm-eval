import { defineStore } from 'pinia'
import { ref } from 'vue'

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
      id: uuidv4(),
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
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    }
    currentSession.value.messages.push(userMessage)

    if (currentSession.value.messages.length === 1) {
      currentSession.value.title = content.substring(0, 20)
    }

    const assistantMessage: ChatMessage = {
      id: uuidv4(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true,
    }
    currentSession.value.messages.push(assistantMessage)

    isLoading.value = true
    error.value = null

    const apiMessages: ApiChatMessage[] = currentSession.value.messages
      .filter((msg) => !msg.streaming)
      .map((msg) => ({
        role: msg.role,
        content: msg.content,
      }))

    try {
      streamChat(
        {
          model: currentSession.value.modelId,
          messages: apiMessages,
          stream: true,
        },
        (chunk) => {
          const assistantMsg = currentSession.value?.messages.find((m) => m.id === assistantMessage.id)
          if (assistantMsg) {
            assistantMsg.content += chunk
          }
        },
        () => {
          const assistantMsg = currentSession.value?.messages.find((m) => m.id === assistantMessage.id)
          if (assistantMsg) {
            delete assistantMsg.streaming
          }
          isLoading.value = false
        },
        (err) => {
          error.value = err
          isLoading.value = false
          const assistantMsg = currentSession.value?.messages.find((m) => m.id === assistantMessage.id)
          if (assistantMsg) {
            assistantMsg.content = '抱歉，发生了错误。'
            delete assistantMsg.streaming
          }
        }
      )
    } catch (err) {
      error.value = err
      isLoading.value = false
      const assistantMsg = currentSession.value?.messages.find((m) => m.id === assistantMessage.id)
      if (assistantMsg) {
        assistantMsg.content = '抱歉，启动连接时发生错误。'
        delete assistantMsg.streaming
      }
    }
  }
  
  const loadChatHistory = async (sessionId: string) => {
    // In a real application, you would fetch this from a persistent storage
    console.log(`Loading history for session ${sessionId}...`)
    // This is a placeholder. Implement history loading from your backend if needed.
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
