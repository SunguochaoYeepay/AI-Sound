import apiClient from './config.js'

// 系统健康检查API
export const systemAPI = {
  // 健康检查
  healthCheck: () => apiClient.get('/health'),
  
  // 获取系统信息
  getSystemInfo: () => apiClient.get('/')
}

// 语音克隆API
export const voiceAPI = {
  // 上传参考音频文件和可选的latent文件
  uploadVoice: (formData) => apiClient.post('/voice-clone/upload-reference', formData, {
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
    
    return apiClient.post('/voice-clone/synthesize', formData, {
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
    
    return apiClient.post('/voice-clone/synthesize-from-library', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取声音模板
  getTemplates: () => apiClient.get('/voice-clone/templates'),
  
  // 获取最近合成记录
  getRecentSynthesis: (limit = 10) => apiClient.get(`/voice-clone/recent-synthesis?limit=${limit}`),
  
  // 声音克隆
  cloneVoice: (formData) => apiClient.post('/voice-clone/clone-voice', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 角色管理API
export const charactersAPI = {
  // 获取角色列表
  getCharacters: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.search) queryParams.append('search', params.search)
    if (params.voice_type) queryParams.append('voice_type', params.voice_type)
    if (params.quality_filter) queryParams.append('quality_filter', params.quality_filter)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/characters/?${queryString}` : '/characters/'
    console.log('[API请求] GET', url, params)
    return apiClient.get(url)
  },

  // 获取声音档案列表
  getVoiceProfiles: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.search) queryParams.append('search', params.search)
    if (params.status) queryParams.append('status', params.status)
    if (params.gender) queryParams.append('gender', params.gender)
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/characters?${queryString}` : '/characters'
    return apiClient.get(url)
  },
  
  // 创建角色
  createCharacter: (data) => apiClient.post('/characters/', data, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  
  // 更新角色
  updateCharacter: (id, data) => apiClient.put(`/characters/${id}`, data, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  
  // 删除角色
  deleteCharacter: (id) => apiClient.delete(`/characters/${id}`),
  
  // 获取单个声音档案
  getVoiceProfile: (id) => apiClient.get(`/characters/${id}`),
  
  // 创建声音档案
  createVoiceProfile: (data) => apiClient.post('/characters', data),
  
  // 更新声音档案
  updateVoiceProfile: (id, data) => {
    const formData = data instanceof FormData ? data : (() => {
      const fd = new FormData()
      Object.keys(data).forEach(key => {
        fd.append(key, data[key])
      })
      return fd
    })()
    
    return apiClient.put(`/characters/${id}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除声音档案
  deleteVoiceProfile: (id) => apiClient.delete(`/characters/${id}`),
  
  // 测试声音合成
  testVoiceSynthesis: (id, data) => {
    const formData = new FormData()
    formData.append('text', data.text || '这是声音测试，用于验证合成效果。')
    formData.append('time_step', data.time_step || 20)
    formData.append('p_weight', data.p_weight || 1.0)
    formData.append('t_weight', data.t_weight || 1.0)
    
    return apiClient.post(`/characters/${id}/test`, formData, {
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
    if (data.book_id && data.book_id !== null) {
      formData.append('book_id', data.book_id)
    }
    if (data.content) {
      formData.append('content', data.content)
    }
    formData.append('initial_characters', JSON.stringify(data.initial_characters || []))
    formData.append('settings', JSON.stringify(data.settings || {}))
    
    // 兼容旧版本参数
    if (data.text_content) {
      formData.append('content', data.text_content)
    }
    if (data.character_mapping) {
      formData.append('character_mapping', JSON.stringify(data.character_mapping))
    }
    if (data.text_file) {
      formData.append('text_file', data.text_file)
    }
    
    return apiClient.post('/novel-reader/projects', formData, {
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
    const url = queryString ? `/novel-reader/projects?${queryString}` : '/novel-reader/projects'
    
    return apiClient.get(url)
  },
  
  // 获取项目详情
  getProjectDetail: (projectId) => apiClient.get(`/novel-reader/projects/${projectId}`),
  
  // 更新项目
  updateProject: (projectId, data) => {
    const formData = new FormData()
    formData.append('name', data.name)
    formData.append('description', data.description || '')
    formData.append('character_mapping', JSON.stringify(data.character_mapping || {}))
    
    return apiClient.put(`/novel-reader/projects/${projectId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除项目
  deleteProject: (projectId, force = false) => 
    apiClient.delete(`/novel-reader/projects/${projectId}?force=${force}`),
  
  // 开始音频生成
  startGeneration: (projectId, data) => {
    const formData = new FormData()
    formData.append('parallel_tasks', data.parallel_tasks || 2)
    
    return apiClient.post(`/novel-reader/projects/${projectId}/start-generation`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 暂停生成
  pauseGeneration: (projectId) => apiClient.post(`/novel-reader/projects/${projectId}/pause`),
  
  // 恢复生成
  resumeGeneration: (projectId, data) => {
    const formData = new FormData()
    formData.append('parallel_tasks', data.parallel_tasks || 2)
    
    return apiClient.post(`/novel-reader/projects/${projectId}/resume`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取生成进度
  getProgress: (projectId) => apiClient.get(`/novel-reader/projects/${projectId}/progress`),
  
  // 下载音频
  downloadAudio: (projectId) => apiClient.get(`/novel-reader/projects/${projectId}/download`, {
    responseType: 'blob'
  }),
  
  // 兼容旧API
  uploadText: (formData) => apiClient.post('/reader/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  
  startReading: (data) => apiClient.post('/reader/start', data),
  
  getStatus: (taskId) => apiClient.get(`/reader/status/${taskId}`)
}

// 书籍管理API
export const booksAPI = {
  // 获取书籍列表
  getBooks: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)
    if (params.search) queryParams.append('search', params.search)
    if (params.status) queryParams.append('status', params.status)
    if (params.author) queryParams.append('author', params.author)
    if (params.tags) queryParams.append('tags', params.tags)
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/api/books?${queryString}` : '/api/books'
    
    console.log('[API请求] GET', url, params)
    console.log('[API请求] 完整URL:', url)
    return apiClient.get(url)
  },
  
  // 创建书籍
  createBook: (data) => {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('author', data.author || '')
    formData.append('description', data.description || '')
    formData.append('content', data.content || '')
    formData.append('tags', JSON.stringify(data.tags || []))
    
    if (data.text_file) {
      formData.append('text_file', data.text_file)
    }
    
    return apiClient.post('/api/books', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取书籍详情
  getBookDetail: (bookId) => apiClient.get(`/api/books/${bookId}`),
  
  // 更新书籍
  updateBook: (bookId, data) => {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('author', data.author || '')
    formData.append('description', data.description || '')
    formData.append('content', data.content || '')
    formData.append('tags', JSON.stringify(data.tags || []))
    formData.append('status', data.status || 'draft')
    
    return apiClient.put(`/api/books/${bookId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除书籍
  deleteBook: (bookId, force = false) => 
    apiClient.delete(`/api/books/${bookId}?force=${force}`),
  
  // 获取书籍内容
  getBookContent: (bookId, params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.chapter) queryParams.append('chapter', params.chapter)
    if (params.start) queryParams.append('start', params.start)
    if (params.length) queryParams.append('length', params.length)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/api/books/${bookId}/content?${queryString}` : `/api/books/${bookId}/content`
    
    return apiClient.get(url)
  },
  
  // 获取书籍统计
  getBookStats: (bookId) => apiClient.get(`/api/books/${bookId}/stats`)
}

// 音频库API
export const audioAPI = {
  // 获取音频文件列表
  getFiles: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)
    if (params.search) queryParams.append('search', params.search)
    if (params.character) queryParams.append('character', params.character)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/audio-library/files?${queryString}` : '/audio-library/files'
    
    return apiClient.get(url)
  },
  
  // 获取统计信息
  getStats: () => apiClient.get('/audio-library/stats')
}

// 监控API
export const monitorAPI = {
  // 获取系统状态
  getSystemStatus: () => apiClient.get('/monitor/system'),
  
  // 获取服务状态
  getServiceStatus: () => apiClient.get('/monitor/services')
}