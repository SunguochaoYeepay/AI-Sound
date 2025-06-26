import axios from 'axios'

// 环境配置 - 统一使用相对路径，让Vite代理处理
const isDevelopment = import.meta.env.DEV
// 强制使用v1 API路径，因为后端在v1路径下
const API_BASE_URL = '/api/v1'  // 统一使用v1路径

console.log(`[API配置] 当前环境: ${isDevelopment ? '开发' : '生产'}, API地址: ${API_BASE_URL}`)

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 增加超时时间60秒
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
    console.log(`[API请求] ${config.method?.toUpperCase()} ${config.url}`, config.data || '')
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

// 创建用于LLM分析的实例（超长超时时间）
export const llmAnalysisClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5分钟超时时间，用于LLM分析（处理大量段落时需要更长时间）
  headers: {
    'Content-Type': 'application/json'
  },
  maxContentLength: 20 * 1024 * 1024, // 20MB
  maxBodyLength: 20 * 1024 * 1024 // 20MB
})

// LLM分析客户端拦截器
llmAnalysisClient.interceptors.request.use(
  (config) => {
    console.log(`[LLM API请求] ${config.method?.toUpperCase()} ${config.url}`, config.data || '')
    return config
  },
  (error) => {
    console.error('[LLM API请求错误]', error)
    return Promise.reject(error)
  }
)

llmAnalysisClient.interceptors.response.use(
  (response) => {
    console.log(`[LLM API响应] ${response.config.url}`, response.data)
    return response
  },
  (error) => {
    console.error('[LLM API响应错误]', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default apiClient
export { API_BASE_URL } 