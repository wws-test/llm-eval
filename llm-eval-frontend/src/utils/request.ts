import axios from 'axios';

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
  timeout: 10000,
  withCredentials: true, // 支持跨域携带cookie
});

service.interceptors.request.use(
  (config) => {
    // 添加认证token
    let token = localStorage.getItem('auth_token') || localStorage.getItem('token');

    // 如果没有token，为内部项目设置一个默认token
    if (!token) {
      token = 'dev';  // 使用后端的开发者后门token
      localStorage.setItem('auth_token', token);
    }

    config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

service.interceptors.response.use(
  (response) => {
    const res = response.data;

    // 新的API响应格式：{ success: boolean, data?: any, message?: string, error?: string }
    if (res.success === false) {
      // API返回错误
      const errorMessage = res.error || res.message || 'Unknown error';
      console.error('API Error:', errorMessage);

      // 如果是认证错误，清除token并跳转到登录页
      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }

      return Promise.reject(new Error(errorMessage));
    } else {
      // API成功响应
      return res;
    }
  },
  (error) => {
    console.error('Response error:', error);

    let errorMessage = 'Network error';

    if (error.response) {
      // 服务器响应了错误状态码
      const { status, data } = error.response;

      if (status === 401) {
        // 认证失败
        localStorage.removeItem('token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        errorMessage = '认证失败，请重新登录';
      } else if (status === 403) {
        errorMessage = '权限不足';
      } else if (status === 404) {
        errorMessage = '接口不存在';
      } else if (status === 500) {
        errorMessage = '服务器内部错误';
      } else if (data && data.error) {
        errorMessage = data.error;
      } else {
        errorMessage = `请求失败 (${status})`;
      }
    } else if (error.request) {
      // 请求发出但没有收到响应
      errorMessage = '网络连接失败，请检查网络';
    }

    return Promise.reject(new Error(errorMessage));
  }
);

export default service;