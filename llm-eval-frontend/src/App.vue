<template>
  <n-config-provider :theme="isDark ? darkTheme : null" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <div class="app-container">
            <!-- 导航栏 -->
            <n-layout has-sider>
              <n-layout-sider
                bordered
                collapse-mode="width"
                :collapsed-width="64"
                :width="240"
                :collapsed="collapsed"
                show-trigger
                @collapse="collapsed = true"
                @expand="collapsed = false"
              >
                <div class="logo-container">
                  <n-icon size="32" color="#18a058" v-if="collapsed">
                    <Star />
                  </n-icon>
                  <div v-else class="logo-text">
                    <n-icon size="32" color="#18a058">
                      <Star />
                    </n-icon>
                    <span class="logo-title">LLM评估平台</span>
                  </div>
                </div>

                <n-menu
                  v-if="authStore.isAuthenticated"
                  :collapsed="collapsed"
                  :collapsed-width="64"
                  :collapsed-icon-size="22"
                  :options="menuOptions"
                  :value="activeKey"
                  @update:value="handleMenuSelect"
                />

                <div v-else class="login-prompt">
                  <n-button type="primary" @click="$router.push('/login')" block>
                    登录
                  </n-button>
                </div>
              </n-layout-sider>

              <n-layout>
                <!-- 顶部栏 -->
                <n-layout-header bordered class="header">
                  <div class="header-content">
                    <div class="header-left">
                      <n-breadcrumb>
                        <n-breadcrumb-item>{{ currentPageTitle }}</n-breadcrumb-item>
                      </n-breadcrumb>
                    </div>

                    <div class="header-right">
                      <!-- 主题切换 -->
                      <n-tooltip trigger="hover">
                        <template #trigger>
                          <n-button
                            quaternary
                            circle
                            @click="toggleTheme"
                          >
                            <template #icon>
                              <n-icon>
                                <Sunny v-if="isDark" />
                                <Moon v-else />
                              </n-icon>
                            </template>
                          </n-button>
                        </template>
                        切换主题
                      </n-tooltip>

                      <!-- 用户菜单 -->
                      <n-dropdown
                        v-if="authStore.isAuthenticated"
                        trigger="click"
                        :options="userMenuOptions"
                        @select="handleUserMenuSelect"
                      >
                        <n-button quaternary circle>
                          <template #icon>
                            <n-icon>
                              <Person />
                            </n-icon>
                          </template>
                        </n-button>
                      </n-dropdown>
                    </div>
                  </div>
                </n-layout-header>

                <!-- 主要内容区域 -->
                <n-layout-content class="content">
                  <div class="page-container">
                    <router-view />
                  </div>
                </n-layout-content>
              </n-layout>
            </n-layout>
          </div>
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { darkTheme } from 'naive-ui'
import type { MenuOption } from 'naive-ui'

import {
  Star,
  Sunny,
  Moon,
  Person,
  Home,
  Settings,
  ChatbubbleEllipses,
  BarChart,
  Library,
  Rocket,
  Search
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 主题相关
const isDark = ref(localStorage.getItem('theme') === 'dark')
const collapsed = ref(false)

const themeOverrides = {
  common: {
    primaryColor: '#18a058',
    primaryColorHover: '#36ad6a',
    primaryColorPressed: '#0c7a43',
    primaryColorSuppl: '#36ad6a'
  }
}

// 菜单选项
const menuOptions: MenuOption[] = [
  {
    label: '仪表盘',
    key: 'dashboard',
    icon: () => h(Home),
    route: '/'
  },
  {
    label: '模型管理',
    key: 'models',
    icon: () => h(Settings),
    route: '/models'
  },
  {
    label: '对话',
    key: 'chat',
    icon: () => h(ChatbubbleEllipses),
    children: [
      {
        label: '开始新对话',
        key: 'new-chat',
        route: '/chat'
      },
      {
        label: '对话历史',
        key: 'chat-history',
        route: '/chat/history'
      }
    ]
  },
  {
    label: '测试集管理',
    key: 'datasets',
    icon: () => h(Library),
    route: '/datasets'
  },
  {
    label: '效果评估',
    key: 'evaluations',
    icon: () => h(BarChart),
    children: [
      {
        label: '开始评估',
        key: 'new-evaluation',
        route: '/evaluations/create'
      },
      {
        label: '评估历史',
        key: 'evaluation-history',
        route: '/evaluations'
      }
    ]
  },
  {
    label: '性能评估',
    key: 'perf-eval',
    icon: () => h(Rocket),
    children: [
      {
        label: '开始评估',
        key: 'new-perf-eval',
        route: '/perf-eval/create'
      },
      {
        label: '评估历史',
        key: 'perf-eval-history',
        route: '/perf-eval/history'
      }
    ]
  },
  {
    label: 'RAG评估',
    key: 'rag-eval',
    icon: () => h(Search),
    children: [
      {
        label: '开始评估',
        key: 'new-rag-eval',
        route: '/rag-eval/create'
      },
      {
        label: '评估历史',
        key: 'rag-eval-history',
        route: '/rag-eval/history'
      }
    ]
  }
]

// 用户菜单选项
const userMenuOptions = [
  {
    label: '修改密码',
    key: 'change-password'
  },
  {
    label: '退出登录',
    key: 'logout'
  }
]

// 当前激活的菜单项
const activeKey = computed(() => {
  const path = route.path
  if (path === '/') return 'dashboard'
  if (path.startsWith('/models')) return 'models'
  if (path.startsWith('/chat')) return 'chat'
  if (path.startsWith('/datasets')) return 'datasets'
  if (path.startsWith('/evaluations')) return 'evaluations'
  if (path.startsWith('/perf-eval')) return 'perf-eval'
  if (path.startsWith('/rag-eval')) return 'rag-eval'
  return 'dashboard'
})

// 当前页面标题
const currentPageTitle = computed(() => {
  const path = route.path
  if (path === '/') return '仪表盘'
  if (path.startsWith('/models')) return '模型管理'
  if (path.startsWith('/chat')) return '对话'
  if (path.startsWith('/datasets')) return '测试集管理'
  if (path.startsWith('/evaluations')) return '效果评估'
  if (path.startsWith('/perf-eval')) return '性能评估'
  if (path.startsWith('/rag-eval')) return 'RAG评估'
  return '大模型评估平台'
})

// 主题切换
const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

// 菜单选择处理
const handleMenuSelect = (key: string, option: MenuOption) => {
  if (option.route) {
    router.push(option.route)
  }
}

// 用户菜单选择处理
const handleUserMenuSelect = (key: string) => {
  switch (key) {
    case 'change-password':
      router.push('/auth/change-password')
      break
    case 'logout':
      // 简单的确认退出
      if (confirm('您确定要退出登录吗？')) {
        authStore.logout()
        router.push('/login')
      }
      break
  }
}

// 初始化认证状态
onMounted(() => {
  authStore.initAuth()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.logo-container {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--n-border-color);
}

.logo-text {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--n-text-color-base);
}

.login-prompt {
  padding: 16px;
}

.header {
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.content {
  padding: 0;
  background-color: var(--n-color);
}

.page-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>
