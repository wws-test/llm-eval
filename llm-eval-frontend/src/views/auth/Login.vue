<template>
  <div class="login-container">
    <div class="login-content">
      <!-- 左侧信息区域 -->
      <div class="login-info">
        <div class="info-content">
          <n-space vertical align="center" size="large">
            <n-icon size="80" color="#18a058">
              <Star />
            </n-icon>
            <div style="text-align: center;">
              <h1 class="welcome-title">欢迎使用</h1>
              <h2 class="platform-title">大模型评估平台</h2>
              <p class="welcome-desc">
                全面的AI模型评估解决方案<br>
                支持多种模型类型和评估维度
              </p>
            </div>
          </n-space>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="login-form-container">
        <n-card class="login-card" size="large">
          <template #header>
            <div style="text-align: center;">
              <h3 style="margin: 0; font-size: 24px; font-weight: 600;">立即登录</h3>
              <p style="margin: 8px 0 0 0; color: #909399; font-size: 14px;">
                首次登录将自动创建账户，请及时修改密码
              </p>
            </div>
          </template>

          <n-form
            ref="formRef"
            :model="loginForm"
            :rules="formRules"
            @submit.prevent="handleLogin"
          >
            <n-form-item path="username" label="用户名">
              <n-input
                v-model:value="loginForm.username"
                placeholder="请输入用户名"
                size="large"
                clearable
              >
                <template #prefix>
                  <n-icon>
                    <Person />
                  </n-icon>
                </template>
              </n-input>
            </n-form-item>

            <n-form-item path="password" label="密码">
              <n-input
                v-model:value="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                show-password-on="click"
                clearable
              >
                <template #prefix>
                  <n-icon>
                    <LockClosed />
                  </n-icon>
                </template>
              </n-input>
            </n-form-item>

            <n-form-item>
              <n-checkbox v-model:checked="rememberMe">
                记住我
              </n-checkbox>
            </n-form-item>

            <n-form-item>
              <n-button
                type="primary"
                size="large"
                block
                :loading="loading"
                attr-type="submit"
                @click="handleLogin"
              >
                登录
              </n-button>
            </n-form-item>
          </n-form>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import {
  Star,
  Person,
  LockClosed
} from '@vicons/ionicons5'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()
const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const formRules: FormRules = {
  username: [
    {
      required: true,
      message: '请输入用户名',
      trigger: ['input', 'blur']
    }
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: ['input', 'blur']
    }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    // 调用真实的登录API
    const result = await authStore.login(loginForm.username, loginForm.password)

    if (result.success) {
      message.success(result.message || '登录成功！')

      if (result.isNewUser) {
        message.info('这是您首次登录，建议及时修改密码', { duration: 5000 })
      }

      if (rememberMe.value) {
        saveCredentials()
      } else {
        clearSavedCredentials()
      }

      await router.push('/')
    }
  } catch (error: any) {
    console.error('登录失败:', error)
    message.error(error.message || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

const saveCredentials = () => {
  const username = loginForm.username
  const password = loginForm.password

  if (username && password) {
    // 使用Base64编码存储（简单混淆，不是真正的加密）
    localStorage.setItem('rememberedUsername', btoa(username))
    localStorage.setItem('rememberedPassword', btoa(password))
    localStorage.setItem('credentialsRemembered', 'true')
  }
}

const loadSavedCredentials = () => {
  const remembered = localStorage.getItem('credentialsRemembered')

  if (remembered === 'true') {
    const savedUsername = localStorage.getItem('rememberedUsername')
    const savedPassword = localStorage.getItem('rememberedPassword')

    if (savedUsername && savedPassword) {
      try {
        // 解码并填充字段
        loginForm.username = atob(savedUsername)
        loginForm.password = atob(savedPassword)
        rememberMe.value = true
      } catch (e) {
        // 如果解码失败，清除保存的数据
        clearSavedCredentials()
      }
    }
  }
}

const clearSavedCredentials = () => {
  localStorage.removeItem('rememberedUsername')
  localStorage.removeItem('rememberedPassword')
  localStorage.removeItem('credentialsRemembered')
}

// 监听记住我复选框的变化
watch(rememberMe, (newValue) => {
  if (!newValue) {
    // 如果取消勾选记住我，清除保存的账号密码
    clearSavedCredentials()
  }
})

onMounted(() => {
  loadSavedCredentials()
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-content {
  display: flex;
  max-width: 1000px;
  width: 100%;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.login-info {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
}

.info-content {
  text-align: center;
}

.welcome-title {
  font-size: 2.5rem;
  font-weight: 300;
  margin: 0;
  opacity: 0.9;
}

.platform-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 8px 0 24px 0;
}

.welcome-desc {
  font-size: 1.1rem;
  line-height: 1.6;
  opacity: 0.8;
  margin: 0;
}

.login-form-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  border: none;
  box-shadow: none;
}

@media (max-width: 768px) {
  .login-content {
    flex-direction: column;
    max-width: 400px;
  }

  .login-info {
    padding: 40px 20px;
  }

  .welcome-title {
    font-size: 2rem;
  }

  .platform-title {
    font-size: 1.5rem;
  }

  .welcome-desc {
    font-size: 1rem;
  }

  .login-form-container {
    padding: 20px;
  }
}
</style>

