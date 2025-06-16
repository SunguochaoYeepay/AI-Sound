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
    const url = queryString ? `/characters?${queryString}` : '/characters'
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
  createCharacter: (data) => apiClient.post('/characters', data, {
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
  getProject: (projectId) => apiClient.get(`/novel-reader/projects/${projectId}`),
  
  getProjectDetail: (projectId) => apiClient.get(`/novel-reader/projects/${projectId}`),
  
  // 获取项目音频文件（基于项目详情）
  getProjectAudioFiles: async (projectId) => {
    const response = await apiClient.get(`/novel-reader/projects/${projectId}`)
    if (response.data.success) {
      return {
        data: {
          success: true,
          data: response.data.data.audio_files || []
        }
      }
    }
    return response
  },
  
  // 更新项目
  updateProject: (projectId, data) => {
    const formData = new FormData()
    formData.append('name', data.name)
    formData.append('description', data.description || '')
    
    // 添加book_id字段
    if (data.book_id !== undefined && data.book_id !== null) {
      formData.append('book_id', data.book_id)
    }
    
    // 处理character_mapping - 如果已经是字符串就直接使用，否则序列化
    let characterMapping = data.character_mapping || {}
    if (typeof characterMapping === 'string') {
      formData.append('character_mapping', characterMapping)
    } else {
      formData.append('character_mapping', JSON.stringify(characterMapping))
    }
    
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
  startGeneration: (projectId, data = {}) => {
    const formData = new FormData()
    formData.append('parallel_tasks', data.parallel_tasks || 1)
    
    return apiClient.post(`/novel-reader/projects/${projectId}/start`, formData, {
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
  
  // 兼容旧API - 已废弃，建议使用 readerAPI 中的对应方法
  uploadText: (formData) => apiClient.post('/novel-reader/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  
  startReading: (data) => apiClient.post('/novel-reader/start', data),
  
  getStatus: (taskId) => apiClient.get(`/novel-reader/status/${taskId}`)
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
    const url = queryString ? `/books?${queryString}` : '/books'
    
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
    
    return apiClient.post('/books', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取书籍详情
  getBookDetail: (bookId) => apiClient.get(`/books/${bookId}`),
  
  // 更新书籍
  updateBook: (bookId, data) => {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('author', data.author || '')
    formData.append('description', data.description || '')
    formData.append('content', data.content || '')
    formData.append('tags', JSON.stringify(data.tags || []))
    formData.append('status', data.status || 'draft')
    
    return apiClient.put(`/books/${bookId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除书籍
  deleteBook: (bookId, force = false) => 
    apiClient.delete(`/books/${bookId}?force=${force}`),
  
  // 获取书籍内容
  getBookContent: (bookId, params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.chapter) queryParams.append('chapter', params.chapter)
    if (params.start) queryParams.append('start', params.start)
    if (params.length) queryParams.append('length', params.length)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/books/${bookId}/content?${queryString}` : `/books/${bookId}/content`
    
    return apiClient.get(url)
  },
  
  // 获取书籍统计
  getBookStats: (bookId) => apiClient.get(`/books/${bookId}/stats`),
  
  // 检测章节结构
  detectChapters: (bookId, config = {}) => {
    const params = new URLSearchParams()
    params.append('force_reprocess', config.force_reprocess || false)
    if (config.detection_config) {
      params.append('detection_config', JSON.stringify(config.detection_config))
    }
    
    return apiClient.post(`/books/${bookId}/detect-chapters?${params.toString()}`)
  },
  
  // 获取书籍章节列表
  getBookChapters: (bookId, params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.skip) queryParams.append('skip', params.skip)
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.status_filter) queryParams.append('status_filter', params.status_filter)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/books/${bookId}/chapters?${queryString}` : `/books/${bookId}/chapters`
    
    return apiClient.get(url)
  },

  // 智能准备章节用于语音合成
  prepareChapterForSynthesis: (chapterId) => 
    apiClient.post(`/content-preparation/prepare-synthesis/${chapterId}`),

  // 获取章节智能准备状态
  getPreparationStatus: (chapterId) => 
    apiClient.get(`/content-preparation/preparation-status/${chapterId}`),

  // 获取章节内容统计
  getContentStats: (chapterId) => 
    apiClient.get(`/content-preparation/content-stats/${chapterId}`),

  // 获取章节合成预览
  getSynthesisPreview: (chapterId) => 
    apiClient.get(`/content-preparation/synthesis-preview/${chapterId}`),

  // 获取已有的智能准备结果（不重新执行）
  getPreparationResult: (chapterId) => 
    apiClient.get(`/content-preparation/result/${chapterId}`),

  // 更新智能准备结果
  updatePreparationResult: (chapterId, data) => 
    apiClient.put(`/content-preparation/result/${chapterId}`, data),

  // AI重新分段
  aiResegmentText: (data) => 
    apiClient.post(`/content-preparation/ai-resegment`, data),

  // 获取书籍的所有智能准备结果
  getBookAnalysisResults: (bookId) => 
    apiClient.get(`/books/${bookId}/analysis-results`)
}

// 章节管理API
export const chaptersAPI = {
  // 获取章节列表
  getChapters: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.book_id) queryParams.append('book_id', params.book_id)
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)
    if (params.search) queryParams.append('search', params.search)
    if (params.status) queryParams.append('status', params.status)
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/chapters?${queryString}` : '/chapters'
    
    return apiClient.get(url)
  },

  // 获取章节详情
  getChapter: (chapterId) => apiClient.get(`/chapters/${chapterId}`),

  // 创建章节
  createChapter: (data) => {
    const formData = new FormData()
    formData.append('book_id', data.book_id)
    formData.append('title', data.title)
    formData.append('content', data.content)
    if (data.chapter_number) formData.append('chapter_number', data.chapter_number)
    
    return apiClient.post('/chapters', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 更新章节
  updateChapter: (chapterId, data) => {
    const formData = new FormData()
    if (data.title !== undefined) formData.append('title', data.title)
    if (data.content !== undefined) formData.append('content', data.content)
    if (data.analysis_status !== undefined) formData.append('analysis_status', data.analysis_status)
    
    return apiClient.patch(`/chapters/${chapterId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除章节
  deleteChapter: (chapterId, force = false) => 
    apiClient.delete(`/chapters/${chapterId}?force=${force}`),

  // 分割章节
  splitChapter: (chapterId, data) => {
    const formData = new FormData()
    formData.append('split_position', data.split_position)
    formData.append('new_title', data.new_title)
    
    return apiClient.post(`/chapters/${chapterId}/split`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 合并章节
  mergeChapters: (chapterId, data) => {
    const formData = new FormData()
    formData.append('target_chapter_id', data.target_chapter_id)
    formData.append('merge_direction', data.merge_direction || 'after')
    
    return apiClient.post(`/chapters/${chapterId}/merge`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取章节统计
  getChapterStats: (chapterId) => apiClient.get(`/chapters/${chapterId}/statistics`),

  // 智能准备章节
  prepareChapter: (chapterId, params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.include_emotion !== undefined) queryParams.append('include_emotion', params.include_emotion)
    if (params.processing_mode) queryParams.append('processing_mode', params.processing_mode)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/chapters/${chapterId}/prepare-synthesis?${queryString}` : `/chapters/${chapterId}/prepare-synthesis`
    
    return apiClient.post(url)
  },

  // 获取合成预览
  getSynthesisPreview: (chapterId, maxSegments = 10) => 
    apiClient.get(`/chapters/${chapterId}/synthesis-preview?max_segments=${maxSegments}`),

  // 获取内容统计
  getContentStats: (chapterId) => 
    apiClient.get(`/chapters/${chapterId}/content-stats`)
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
    if (params.projectId) queryParams.append('project_id', params.projectId)
    if (params.audioType) queryParams.append('audio_type', params.audioType)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/audio-library/files?${queryString}` : '/audio-library/files'
    
    return apiClient.get(url)
  },
  
  // 获取统计信息
  getStats: () => apiClient.get('/audio-library/stats'),
  
  // 同步音频文件
  syncFiles: () => apiClient.post('/audio-library/sync'),
  
  // 下载单个音频文件
  downloadFile: (fileId) => apiClient.get(`/audio-library/download/${fileId}`, {
    responseType: 'blob'
  }),
  
  // 批量下载音频文件
  batchDownload: (fileIds) => apiClient.post('/audio-library/batch-download', fileIds, {
    responseType: 'blob'
  }),
  
  // 删除单个音频文件
  deleteFile: (fileId) => apiClient.delete(`/audio-library/files/${fileId}`),
  
  // 批量删除音频文件
  batchDelete: (fileIds) => apiClient.post('/audio-library/batch-delete', fileIds),
  
  // 设置收藏状态
  setFavorite: (fileId, isFavorite) => {
    const formData = new FormData()
    formData.append('is_favorite', isFavorite)
    return apiClient.put(`/audio-library/files/${fileId}/favorite`, formData)
  }
}

// 监控API
export const monitorAPI = {
  // 获取系统状态
  getSystemStatus: () => apiClient.get('/monitor/system-status'),
  
  // 获取服务状态
  getServiceStatus: () => apiClient.get('/monitor/service-health'),
  
  // 获取角色分析进度（包含GPU监控）
  getAnalysisProgress: (sessionId) => apiClient.get(`/monitor/analysis-progress/${sessionId}`),
  
  // 获取性能历史
  getPerformanceHistory: (hours = 24) => apiClient.get(`/monitor/performance-history?hours=${hours}`)
}

// 智能分析API (Mock)
export const intelligentAnalysisAPI = {
  // 分析项目角色和文本
  analyzeProject: (projectId, params = null) => {
    if (params) {
      return apiClient.post(`/intelligent-analysis/analyze/${projectId}`, params)
    } else {
      return apiClient.post(`/intelligent-analysis/analyze/${projectId}`)
    }
  },
  
  // 应用分析结果
  applyAnalysis: (projectId, analysisData) => 
    apiClient.post(`/intelligent-analysis/apply/${projectId}`, analysisData)
}