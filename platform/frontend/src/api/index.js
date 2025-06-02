import apiClient from './config.js'

// 系统健康检查API
export const systemAPI = {
  // 健康检查
  healthCheck: () => apiClient.get('/health'),
  
  // 获取系统信息
  getSystemInfo: () => apiClient.get('/')
}

// 语音克隆API - 修正为实际后端路径
export const voiceAPI = {
  // 上传参考音频文件和可选的latent文件
  uploadVoice: (formData) => apiClient.post('/api/voice-clone/upload-reference', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  
  // 语音合成
  synthesize: (data) => {
    const formData = new FormData()
    formData.append('text', data.text)
    formData.append('reference_file_id', data.reference_file_id)
    formData.append('time_step', data.time_step)
    formData.append('p_weight', data.p_weight)
    formData.append('t_weight', data.t_weight)
    if (data.latent_file_id) {
      formData.append('latent_file_id', data.latent_file_id)
    }
    
    return apiClient.post('/api/voice-clone/synthesize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取声音模板
  getTemplates: () => apiClient.get('/api/voice-clone/templates'),
  
  // 获取最近合成记录
  getRecentSynthesis: (limit = 10) => apiClient.get(`/api/voice-clone/recent-synthesis?limit=${limit}`)
}

// 角色管理API
export const charactersAPI = {
  // 获取角色列表
  getCharacters: () => apiClient.get('/api/characters'),
  
  // 创建角色
  createCharacter: (data) => apiClient.post('/api/characters', data),
  
  // 更新角色
  updateCharacter: (id, data) => apiClient.put(`/api/characters/${id}`, data),
  
  // 删除角色
  deleteCharacter: (id) => apiClient.delete(`/api/characters/${id}`)
}

// 小说朗读API
export const readerAPI = {
  // 上传文本文件
  uploadText: (formData) => apiClient.post('/api/reader/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  
  // 开始朗读
  startReading: (data) => apiClient.post('/api/reader/start', data),
  
  // 获取朗读状态
  getStatus: (taskId) => apiClient.get(`/api/reader/status/${taskId}`)
}

// 监控API
export const monitorAPI = {
  // 获取系统状态
  getSystemStatus: () => apiClient.get('/api/monitor/system'),
  
  // 获取服务状态
  getServiceStatus: () => apiClient.get('/api/monitor/services')
} 