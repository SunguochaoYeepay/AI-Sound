/**
 * 统一服务端点配置
 * 所有服务URL的集中管理，避免硬编码
 */

const isDevelopment = import.meta.env.DEV

// 基础服务配置
const SERVICE_CONFIG = {
  // 主后端API服务
  API_BASE_URL: '/api/v1',  // 通过Vite代理
  
  // 后端服务基础URL（用于直接访问）
  BACKEND_BASE_URL: isDevelopment 
    ? 'http://localhost:8001'  // 开发环境：本地服务
    : 'http://localhost:8000', // 生产环境：Docker容器
  
  // SongGeneration音乐生成服务
  SONG_GENERATION: {
    BASE_URL: 'http://localhost:7862',
    API: {
      GENERATE: '/generate',
      GENERATE_ASYNC: '/generate_async', 
      HEALTH: '/health',
      PING: '/ping'
    },
    WS: {
      PROGRESS: (taskId) => `ws://localhost:7862/ws/progress/${taskId}`
    }
  },

  // WebSocket服务
  WEBSOCKET: {
    // 主WebSocket连接
    MAIN: () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      
      // 🔧 强制使用正确的后端URL，忽略可能错误的环境变量
      const backendUrl = SERVICE_CONFIG.BACKEND_BASE_URL
      const cleanHost = backendUrl.replace(/^https?:\/\//, '')
      const wsUrl = `${protocol}//${cleanHost}/ws`
      
      console.log('[WebSocket配置]', {
        环境: isDevelopment ? '开发' : '生产',
        后端URL: backendUrl,
        WebSocket地址: wsUrl,
        环境变量覆盖: import.meta.env.VITE_API_BASE_URL
      })
      
      return wsUrl
    },
    
    // 分析进度WebSocket
    ANALYSIS_PROGRESS: (chapterId) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const baseUrl = import.meta.env.VITE_API_BASE_URL || SERVICE_CONFIG.BACKEND_BASE_URL
      const cleanHost = baseUrl.replace(/^https?:\/\//, '')
      return `${protocol}//${cleanHost}/api/v1/analysis/ws/progress/${chapterId}`
    }
  },

  // 其他AI服务
  SERVICES: {
    MEGA_TTS: 'http://localhost:7929',
    TANGO_FLUX: 'http://localhost:7930'
  }
}

/**
 * 获取服务URL
 * @param {string} serviceName 服务名称
 * @param {string} endpoint 端点名称  
 * @param {any} params 参数
 * @returns {string} 完整的服务URL
 */
export function getServiceUrl(serviceName, endpoint = '', params = null) {
  const service = SERVICE_CONFIG[serviceName]
  
  if (!service) {
    console.error(`[服务配置] 未找到服务: ${serviceName}`)
    return ''
  }

  // 如果是函数类型的配置（如WebSocket），直接调用
  if (typeof service === 'function') {
    return service(params)
  }

  // 如果有BASE_URL，构建完整URL
  if (service.BASE_URL) {
    const baseUrl = service.BASE_URL
    
    // 如果endpoint是对象路径（如 API.GENERATE）
    if (endpoint.includes('.')) {
      const [category, method] = endpoint.split('.')
      const endpointPath = service[category]?.[method]
      return endpointPath ? `${baseUrl}${endpointPath}` : baseUrl
    }
    
    // 直接endpoint
    return endpoint ? `${baseUrl}${endpoint}` : baseUrl
  }

  return service
}

/**
 * 获取WebSocket URL
 * @param {string} type WebSocket类型
 * @param {any} params 参数
 * @returns {string} WebSocket URL
 */
export function getWebSocketUrl(type, params = null) {
  const wsConfig = SERVICE_CONFIG.WEBSOCKET[type]
  
  if (!wsConfig) {
    console.error(`[WebSocket配置] 未找到类型: ${type}`)
    return ''
  }

  return typeof wsConfig === 'function' ? wsConfig(params) : wsConfig
}

// 导出配置对象
export default SERVICE_CONFIG

// 导出常用的URL获取函数
export const getBackendUrl = () => SERVICE_CONFIG.BACKEND_BASE_URL
export const getApiBaseUrl = () => SERVICE_CONFIG.API_BASE_URL
export const getSongGenerationUrl = (endpoint = '') => getServiceUrl('SONG_GENERATION', endpoint)

console.log('[服务配置] 初始化完成', {
  environment: isDevelopment ? '开发' : '生产',
  backendUrl: SERVICE_CONFIG.BACKEND_BASE_URL,
  apiBaseUrl: SERVICE_CONFIG.API_BASE_URL
}) 