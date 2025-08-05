import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

interface User {
  id: number
  username: string
  created_at?: string
}

interface LoginResponse {
  success: boolean
  data: {
    token: string
    user: User
    is_new_user: boolean
  }
  message?: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const isAuthenticated = computed(() => !!user.value && !!token.value)

  // 兼容旧版本的username属性
  const username = computed(() => user.value?.username || '')

  const login = async (username: string, password: string) => {
    try {
      const response: any = await request.post('/auth/login', {
        username,
        password
      })

      if (response.data) {
        const { token: authToken, user: userData, is_new_user } = response.data

        // 保存认证信息
        token.value = authToken
        user.value = userData

        // 保存到localStorage
        localStorage.setItem('token', authToken)
        localStorage.setItem('user', JSON.stringify(userData))

        // 兼容旧版本
        localStorage.setItem('isAuthenticated', 'true')
        localStorage.setItem('username', userData.username)

        return {
          success: true,
          isNewUser: is_new_user,
          message: response.message || '登录成功'
        }
      } else {
        throw new Error('登录响应格式错误')
      }
    } catch (error: any) {
      console.error('Login failed:', error)
      throw new Error(error.message || '登录失败')
    }
  }

  const logout = async () => {
    try {
      // 调用后端登出API
      if (token.value) {
        await request.post('/auth/logout')
      }
    } catch (error) {
      console.error('Logout API failed:', error)
      // 即使API调用失败，也要清除本地状态
    } finally {
      // 清除本地状态
      user.value = null
      token.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('username')
    }
  }

  const verifyToken = async () => {
    try {
      if (!token.value) {
        return false
      }

      await request.post('/auth/verify-token')
      return true
    } catch (error) {
      console.error('Token verification failed:', error)
      // Token无效，清除本地状态
      user.value = null
      token.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('username')
      return false
    }
  }

  const initAuth = () => {
    // 从localStorage恢复认证信息
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')

    if (savedToken && savedUser) {
      try {
        token.value = savedToken
        user.value = JSON.parse(savedUser)

        // 验证token有效性（异步，不阻塞初始化）
        verifyToken().then(isValid => {
          if (!isValid) {
            console.log('Token expired, user needs to login again')
          }
        })
      } catch (e) {
        console.error('Failed to parse saved auth data:', e)
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('isAuthenticated')
        localStorage.removeItem('username')
      }
    }
  }

  return {
    user,
    token,
    username, // 兼容旧版本
    isAuthenticated,
    login,
    logout,
    verifyToken,
    initAuth
  }
})
