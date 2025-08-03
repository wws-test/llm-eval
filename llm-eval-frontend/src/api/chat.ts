import { API_BASE_URL } from '@/utils/constants'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatCompletionParams {
  messages: ChatMessage[]
  model: string
  stream: boolean
}

export const streamChat = (
  params: ChatCompletionParams,
  onMessage: (data: string) => void,
  onClose: () => void,
  onError: (error: any) => void
) => {
  const eventSource = new EventSource(
    `${API_BASE_URL}/chat/completions?` +
      new URLSearchParams({
        model: params.model,
        messages: JSON.stringify(params.messages),
      })
  )

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close()
      onClose()
    } else {
      onMessage(JSON.parse(event.data).content)
    }
  }

  eventSource.onerror = (error) => {
    eventSource.close()
    onError(error)
  }

  return () => {
    eventSource.close()
  }
} 