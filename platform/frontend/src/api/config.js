import axios from 'axios'

// 环境配置 - 支持开发和生产环境
const isDevelopment = import.meta.env.DEV
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (isDevelopment 
  ? 'http://localhost:8000'  // 开发环境：本地后端
  : 'http://soundapi.cpolar.top')  // 生产环境：外网域名

console.log(`[API配置] 当前环境: ${isDevelopment ? '开发' : '生产'}, API地址: ${API_BASE_URL}`)

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 增加超时时间到60秒
  headers: {
    'Content-Type': 'application/json'
  },
  // 大文件传输配置
  maxContentLength: 20 * 1024 * 1024, // 20MB
  maxBodyLength: 20 * 1024 * 1024 // 20MB
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

// 创建用于下载音频文件的实例（不同配置）
export const downloadClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2分钟
  responseType: 'blob', // 用于文件下载
  maxContentLength: 100 * 1024 * 1024, // 100MB
  maxBodyLength: 100 * 1024 * 1024 // 100MB
})

export default apiClient
export { API_BASE_URL } 