import axios from 'axios'

// API基础配置
const API_BASE_URL = 'http://localhost:8000'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API请求] ${config.method?.toUpperCase()} ${config.url}`, config.data)
    return config
  },
  (error) => {
    console.error('[API请求错误]', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API响应] ${response.config.url}`, response.data)
    return response
  },
  (error) => {
    console.error('[API响应错误]', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default apiClient
export { API_BASE_URL } 