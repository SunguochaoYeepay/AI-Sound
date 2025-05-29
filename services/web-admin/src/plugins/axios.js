import axios from 'axios'

// 创建axios实例
const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:9930',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// 请求拦截器
axiosInstance.interceptors.request.use(
  config => {
    // 可以在这里添加请求前的处理，如添加token等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一处理新的API响应格式
axiosInstance.interceptors.response.use(
  response => {
    // 检查响应数据格式，如果是新的标准格式则自动提取data字段
    if (response.data && typeof response.data === 'object' && 'success' in response.data && 'data' in response.data) {
      // 新的API响应格式: { success: true, data: {...} }
      // 将内层的data提升到response.data，保持向后兼容
      response.data = response.data.data
    }
    return response
  },
  error => {
    console.error('API请求错误', error)
    return Promise.reject(error)
  }
)

export default axiosInstance 