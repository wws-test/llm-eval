import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import HomeView from '../views/Home.vue'
import LoginView from '../views/auth/Login.vue'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true } // 首页也需要认证
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/Chat.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/models',
    name: 'Models',
    component: () => import('@/views/Models.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/datasets',
    name: 'Datasets',
    component: () => import('@/views/Datasets.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/evaluations',
    name: 'Evaluations',
    component: () => import('@/views/Evaluations.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/perf-eval',
    name: 'PerformanceEvaluation',
    component: () => import('@/views/PerformanceEvaluation.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/perf-eval/create',
    name: 'PerformanceEvaluationCreate',
    component: () => import('@/views/PerformanceEvaluationCreate.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/perf-eval/history',
    name: 'PerformanceEvaluationHistory',
    component: () => import('@/views/PerformanceEvaluationHistory.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/perf-eval/results/:taskId',
    name: 'PerformanceEvaluationResults',
    component: () => import('@/views/PerformanceEvaluationResults.vue'),
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth

  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
