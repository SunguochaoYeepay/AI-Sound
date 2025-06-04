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
  
  // 语音合成（使用上传的文件）
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
  
  // 声音库合成（使用声音库中的声音）
  synthesizeFromLibrary: (data) => {
    const formData = new FormData()
    formData.append('text', data.text)
    formData.append('voice_profile_id', data.voice_profile_id)
    formData.append('time_step', data.time_step || 20)
    formData.append('p_weight', data.p_weight || 1.0)
    formData.append('t_weight', data.t_weight || 1.0)
    
    return apiClient.post('/api/voice-clone/synthesize-from-library', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取声音模板
  getTemplates: () => apiClient.get('/api/voice-clone/templates'),
  
  // 获取最近合成记录
  getRecentSynthesis: (limit = 10) => apiClient.get(`/api/voice-clone/recent-synthesis?limit=${limit}`),
  
  // 声音克隆
  cloneVoice: (formData) => apiClient.post('/api/voice-clone/clone-voice', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  
  // 声音库管理 - 添加这些方法
  // 获取声音库列表
  getCharacters: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.search) queryParams.append('search', params.search)
    if (params.voice_type) queryParams.append('voice_type', params.voice_type)
    if (params.quality_filter) queryParams.append('quality_filter', params.quality_filter)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/api/characters/?${queryString}` : '/api/characters/'
    
    return apiClient.get(url)
  },
  
  // 创建声音库
  createCharacter: (data) => {
    // 确保发送FormData格式，设置正确的Content-Type
    return apiClient.post('/api/characters/', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 更新声音库
  updateCharacter: (id, data) => {
    // 确保发送FormData格式，设置正确的Content-Type
    return apiClient.put(`/api/characters/${id}`, data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除声音库
  deleteCharacter: (id) => apiClient.delete(`/api/characters/${id}`)
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
  deleteCharacter: (id) => apiClient.delete(`/api/characters/${id}`),
  
  // 获取声音库列表
  getVoiceProfiles: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.search) queryParams.append('search', params.search)
    if (params.voice_type) queryParams.append('voice_type', params.voice_type)
    if (params.quality_filter) queryParams.append('quality_filter', params.quality_filter)
    
    return apiClient.get(`/api/characters?${queryParams.toString()}`)
  },
  
  // 获取单个声音档案
  getVoiceProfile: (id) => apiClient.get(`/api/characters/${id}`),
  
  // 创建声音档案
  createVoiceProfile: (data) => apiClient.post('/api/characters', data),
  
  // 更新声音档案
  updateVoiceProfile: (id, data) => {
    // 如果data是FormData，直接使用；否则转换为FormData
    const formData = data instanceof FormData ? data : (() => {
      const fd = new FormData()
      Object.keys(data).forEach(key => {
        fd.append(key, data[key])
      })
      return fd
    })()
    
    return apiClient.put(`/api/characters/${id}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除声音档案
  deleteVoiceProfile: (id) => apiClient.delete(`/api/characters/${id}`),
  
  // 测试声音合成
  testVoiceSynthesis: (id, data) => {
    const formData = new FormData()
    formData.append('text', data.text || '这是声音测试，用于验证合成效果。')
    formData.append('time_step', data.time_step || 20)
    formData.append('p_weight', data.p_weight || 1.0)
    formData.append('t_weight', data.t_weight || 1.0)
    
    return apiClient.post(`/api/characters/${id}/test`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

// 小说朗读API
export const readerAPI = {
  // 创建朗读项目
  createProject: (data) => {
    const formData = new FormData()
    formData.append('name', data.name)
    formData.append('description', data.description || '')
    formData.append('text_content', data.text_content || '')
    formData.append('character_mapping', JSON.stringify(data.character_mapping || {}))
    
    if (data.text_file) {
      formData.append('text_file', data.text_file)
    }
    
    return apiClient.post('/api/novel-reader/projects', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取项目列表
  getProjects: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)
    if (params.search) queryParams.append('search', params.search)
    if (params.status) queryParams.append('status', params.status)
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/api/novel-reader/projects?${queryString}` : '/api/novel-reader/projects'
    
    return apiClient.get(url)
  },
  
  // 获取项目详情
  getProjectDetail: (projectId) => apiClient.get(`/api/novel-reader/projects/${projectId}`),
  
  // 更新项目
  updateProject: (projectId, data) => {
    const formData = new FormData()
    formData.append('name', data.name)
    formData.append('description', data.description || '')
    formData.append('character_mapping', JSON.stringify(data.character_mapping || {}))
    
    return apiClient.put(`/api/novel-reader/projects/${projectId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除项目
  deleteProject: (projectId, force = false) => 
    apiClient.delete(`/api/novel-reader/projects/${projectId}?force=${force}`),
  
  // 重新生成文本分段
  regenerateSegments: (projectId, data) => {
    const formData = new FormData()
    formData.append('strategy', data.strategy || 'auto')
    formData.append('custom_rules', data.custom_rules || '')
    
    return apiClient.post(`/api/novel-reader/projects/${projectId}/segments`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 开始音频生成
  startGeneration: (projectId, parallelTasks = 2) => {
    const formData = new FormData()
    formData.append('parallel_tasks', parallelTasks.toString())
    
    return apiClient.post(`/api/novel-reader/projects/${projectId}/start-generation`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 暂停生成
  pauseGeneration: (projectId) => apiClient.post(`/api/novel-reader/projects/${projectId}/pause`),
  
  // 恢复生成
  resumeGeneration: (projectId, parallelTasks = 2) => {
    const formData = new FormData()
    formData.append('parallel_tasks', parallelTasks.toString())
    
    return apiClient.post(`/api/novel-reader/projects/${projectId}/resume`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取生成进度
  getProgress: (projectId) => apiClient.get(`/api/novel-reader/projects/${projectId}/progress`),
  
  // 下载最终音频
  downloadAudio: (projectId) => apiClient.get(`/api/novel-reader/projects/${projectId}/download`, {
    responseType: 'blob'
  }),
  
  // 以下保留兼容旧API的方法
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