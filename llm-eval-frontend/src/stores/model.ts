import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Model {
  id: string
  name: string
  description: string
}

export const useModelStore = defineStore('model', () => {
  const models = ref<Model[]>([
    { id: 'gpt-4o', name: 'GPT-4o', description: 'The latest model from OpenAI.' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'A cost-effective and capable model.' }
  ])

  // In a real app, you'd likely fetch this from an API
  // const fetchModels = async () => { ... }

  return {
    models,
  }
}) 