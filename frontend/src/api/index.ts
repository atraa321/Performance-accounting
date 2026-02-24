import axios from 'axios'
import { getMessageApi } from '@/lib/antdApp'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const errorMessage = error.response?.data?.detail || error.message || '请求失败'
    getMessageApi()?.error(errorMessage)
    return Promise.reject(error)
  }
)

export default api
