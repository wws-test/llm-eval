<template>
  <div class="login-container">
    <el-row type="flex" justify="center" align="middle" class="h-full">
      <el-col :xs="24" :sm="16" :md="12" :lg="8" class="flex items-center justify-center">
        <div class="login-card-wrapper">
          <div class="text-center lg:text-left lg:pr-10 mb-8 lg:mb-0">
            <h1 class="text-5xl font-bold text-gray-700">立即登录!</h1>
            <p class="py-6 text-gray-500">
              首次登录将使用用户名作为初始密码自动创建账户。登录后请及时修改密码以确保账户安全。
            </p>
          </div>
          <el-card class="login-card" shadow="always">
            <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" @submit.prevent="handleLogin">
              <el-form-item prop="username">
                <el-input v-model="loginForm.username" placeholder="请输入用户名" size="large">
                  <template #prepend>
                    <el-icon><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password size="large">
                  <template #prepend>
                    <el-icon><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="rememberMe">记住我</el-checkbox>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" native-type="submit" :loading="loading" class="w-full" size="large">
                  登录
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();
const loginFormRef = ref<FormInstance>();
const loading = ref(false);
const rememberMe = ref(false);

const loginForm = reactive({
  username: '',
  password: '',
});

const loginRules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
});

const handleLogin = async () => {
  if (!loginFormRef.value) return;
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await authStore.login(); // 使用 authStore.login()
        console.log('Login form submitted:', loginForm);
        ElMessage.success('登录成功！');
        
        if (rememberMe.value) {
          saveCredentials();
        } else {
          clearSavedCredentials();
        }

        await router.push('/');
      } catch (error) {
        ElMessage.error('登录失败，请检查用户名和密码');
        console.error(error);
      } finally {
        loading.value = false;
      }
    }
  });
};

const saveCredentials = () => {
  localStorage.setItem('rememberedUsername', btoa(loginForm.username));
  localStorage.setItem('rememberedPassword', btoa(loginForm.password));
  localStorage.setItem('credentialsRemembered', 'true');
};

const loadSavedCredentials = () => {
  const remembered = localStorage.getItem('credentialsRemembered');
  if (remembered === 'true') {
    const savedUsername = localStorage.getItem('rememberedUsername');
    const savedPassword = localStorage.getItem('rememberedPassword');
    if (savedUsername && savedPassword) {
      try {
        loginForm.username = atob(savedUsername);
        loginForm.password = atob(savedPassword);
        rememberMe.value = true;
      } catch (e) {
        clearSavedCredentials();
      }
    }
  }
};

const clearSavedCredentials = () => {
  localStorage.removeItem('rememberedUsername');
  localStorage.removeItem('rememberedPassword');
  localStorage.removeItem('credentialsRemembered');
};

onMounted(() => {
  loadSavedCredentials();
});
</script>

<style scoped>
.login-container {
  height: calc(100vh - 120px); /* Adjust based on header/footer height */
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
.login-card-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

@media (min-width: 1024px) {
  .login-card-wrapper {
    flex-direction: row;
    align-items: center;
  }
}
.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 8px;
}
.text-center {
  text-align: center;
}
.lg\:text-left {
  text-align: left;
}
</style> 