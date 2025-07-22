import apiClient, { llmAnalysisClient } from './config.js'

// 系统健康检查API
export const systemAPI = {
  // 健康检查
  healthCheck: () => apiClient.get('/health'),

  // 获取系统信息
  getSystemInfo: () => apiClient.get('/'),

  // 触发章节智能准备
  prepareChapterSynthesis: (chapterId) => apiClient.post(`/analysis/chapter/${chapterId}/prepare`)
}

// 语音克隆API
export const voiceAPI = {
  // 上传参考音频文件和可选的latent文件
  uploadVoice: (formData) =>
    apiClient.post('/voice-clone/upload-reference', formData, {
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
  cloneVoice: (formData) =>
    apiClient.post('/voice-clone/clone-voice', formData, {
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
    if (params.book_id) queryParams.append('book_id', params.book_id)
    if (params.management_type) queryParams.append('management_type', params.management_type)
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)

    const queryString = queryParams.toString()
    const url = queryString ? `/characters?${queryString}` : '/characters'
    console.log('[API请求] GET', url, params)
    return apiClient.get(url)
  },

  // 创建角色（Character模型）
  createCharacterRecord: (data) => {
    const formData = new FormData()
    formData.append('name', data.name)
    formData.append('description', data.description || '')
    formData.append('book_id', data.book_id)
    if (data.chapter_id) formData.append('chapter_id', data.chapter_id)
    if (data.voice_profile) formData.append('voice_profile', data.voice_profile)
    if (data.voice_config) formData.append('voice_config', data.voice_config)

    return apiClient.post('/characters/create-character', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 批量创建角色（智能分析后）
  batchCreateCharacters: (formData) => {
    return apiClient.post('/characters/batch-create-characters', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
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
  createCharacter: (data) =>
    apiClient.post('/characters/character', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }),

  // 更新角色
  updateCharacter: (id, data) =>
    apiClient.put(`/characters/character/${id}`, data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }),

  // 删除角色
  deleteCharacter: (id, force = false) => {
    const url = force ? `/characters/${id}?force=true` : `/characters/${id}`
    return apiClient.delete(url)
  },

  // 获取单个声音档案
  getVoiceProfile: (id) => apiClient.get(`/characters/${id}`),

  // 创建声音档案
  createVoiceProfile: (data) => apiClient.post('/characters', data),

  // 更新声音档案
  updateVoiceProfile: (id, data) => {
    const formData =
      data instanceof FormData
        ? data
        : (() => {
            const fd = new FormData()
            Object.keys(data).forEach((key) => {
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
  },

  // 🔥 新增：清除智能准备缓存
  clearPreparationCache: (chapterId, cacheType = 'final_config') => {
    return apiClient.delete(`/content-preparation/cache/${chapterId}`, {
      params: { cache_type: cacheType }
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
    if (params.book_id) queryParams.append('book_id', params.book_id)

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

    // 添加其他可选参数
    if (data.synthesis_mode) {
      formData.append('synthesis_mode', data.synthesis_mode)
    }
    if (data.chapter_ids && Array.isArray(data.chapter_ids)) {
      formData.append('chapter_ids', data.chapter_ids.join(','))
    }

    // 🚀 新增：合成模式参数
    if (data.continue_synthesis !== undefined) {
      formData.append('continue_synthesis', data.continue_synthesis)
    }

    // 环境音混合参数
    if (data.enable_environment !== undefined) {
      formData.append('enable_environment', data.enable_environment)
    }
    if (data.environment_volume !== undefined) {
      formData.append('environment_volume', data.environment_volume)
    }

    return apiClient.post(`/novel-reader/projects/${projectId}/start`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 章节级别的环境音混合合成
  startChapterEnvironmentSynthesis: (projectId, chapterId, data = {}) => {
    const formData = new FormData()
    formData.append('parallel_tasks', data.parallel_tasks || 1)
    formData.append('enable_environment', data.enable_environment || false)
    formData.append('environment_volume', data.environment_volume || 0.3)

    return apiClient.post(
      `/novel-reader/projects/${projectId}/chapters/${chapterId}/start`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
  },

  // 章节级别的环境+角色音混合生成
  startChapterMixedSynthesis: (projectId, chapterId, data = {}) => {
    const formData = new FormData()
    formData.append('parallel_tasks', data.parallel_tasks || 1)
    formData.append('enable_voice', data.enable_voice !== undefined ? data.enable_voice : true)
    formData.append(
      'enable_environment',
      data.enable_environment !== undefined ? data.enable_environment : true
    )
    formData.append('environment_volume', data.environment_volume || 0.3)
    formData.append('synthesis_mode', 'mixed') // 标记为混合模式

    return apiClient.post(
      `/novel-reader/projects/${projectId}/chapters/${chapterId}/start`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
  },

  // 暂停生成
  pauseGeneration: (projectId) => apiClient.post(`/novel-reader/projects/${projectId}/pause`),

  // 取消生成
  cancelGeneration: (projectId) => apiClient.post(`/novel-reader/projects/${projectId}/cancel`),

  // 恢复生成
  resumeGeneration: (projectId, data) => {
    const formData = new FormData()
    formData.append('parallel_tasks', data.parallel_tasks || 2)

    // 添加章节ID参数处理，确保恢复时也能指定章节
    if (data.chapter_ids && Array.isArray(data.chapter_ids)) {
      formData.append('chapter_ids', data.chapter_ids.join(','))
    }

    return apiClient.post(`/novel-reader/projects/${projectId}/resume`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取生成进度
  getProgress: (projectId) => apiClient.get(`/novel-reader/projects/${projectId}/progress`),
  getChapterProgress: (projectId, chapterId) =>
    apiClient.get(`/novel-reader/projects/${projectId}/chapters/${chapterId}/progress`),

  // 🔧 移除项目下载功能 - 用户不需要项目下载功能
  // downloadAudio: (projectId) => apiClient.get(`/novel-reader/projects/${projectId}/download`, { responseType: 'blob' }),

  // 重试失败的段落
  retrySegment: (projectId, segmentId) =>
    apiClient.post(`/novel-reader/projects/${projectId}/retry-segment/${segmentId}`),

  // 重试所有失败的段落
  retryAllFailedSegments: (projectId) =>
    apiClient.post(`/novel-reader/projects/${projectId}/retry-failed-segments`),

  // 获取失败段落详情
  getFailedSegments: (projectId) =>
    apiClient.get(`/novel-reader/projects/${projectId}/failed-segments`),

  // 🔧 移除部分下载功能 - 用户不需要项目下载功能
  // downloadPartialAudio: (projectId) => apiClient.get(`/novel-reader/projects/${projectId}/download-partial`, { responseType: 'blob' }),

  // 章节级别合成API
  // 开始单章节合成
  startChapterSynthesis: (projectId, chapterId, data = {}) => {
    const formData = new FormData()
    formData.append('chapter_id', chapterId)
    formData.append('parallel_tasks', data.parallel_tasks || 1)

    return apiClient.post(
      `/novel-reader/projects/${projectId}/chapters/${chapterId}/start`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
  },

  // 重新合成单章节
  restartChapterSynthesis: (projectId, chapterId, data = {}) => {
    const formData = new FormData()
    formData.append('parallel_tasks', data.parallel_tasks || 1)

    return apiClient.post(
      `/novel-reader/projects/${projectId}/chapters/${chapterId}/restart`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
  },

  // 继续合成单章节
  resumeChapterSynthesis: (projectId, chapterId, data = {}) => {
    const formData = new FormData()
    formData.append('parallel_tasks', data.parallel_tasks || 1)

    return apiClient.post(
      `/novel-reader/projects/${projectId}/chapters/${chapterId}/resume`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
  },

  // 重试单章节失败段落
  retryChapterFailedSegments: (projectId, chapterId) =>
    apiClient.post(`/novel-reader/projects/${projectId}/chapters/${chapterId}/retry-failed`),

  // 下载单章节音频
  downloadChapterAudio: (projectId, chapterId) =>
    apiClient.get(`/novel-reader/projects/${projectId}/chapters/${chapterId}/download`, {
      responseType: 'blob'
    }),

  // 重置项目状态 - 解决项目状态卡死问题
  resetProjectStatus: (projectId) =>
    apiClient.post(`/novel-reader/projects/${projectId}/reset-status`),

  // 环境混音相关API
  getEnvironmentMixingResults: (projectId) =>
    apiClient.get(`/novel-reader/projects/${projectId}/environment-mixing/results`),
  downloadEnvironmentMixing: (resultId) =>
    apiClient.get(`/environment-mixing/results/${resultId}/download`, { responseType: 'blob' }),
  startEnvironmentMixing: (projectId, data = {}) => {
    const formData = new FormData()
    if (data.environment_config) {
      formData.append('environment_config', JSON.stringify(data.environment_config))
    }
    if (data.selected_chapter) {
      formData.append('selected_chapter', data.selected_chapter)
    }

    return apiClient.post(
      `/novel-reader/projects/${projectId}/environment-mixing/start`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
  },

  // 兼容旧API - 已废弃，建议使用 readerAPI 中的对应方法
  uploadText: (formData) =>
    apiClient.post('/novel-reader/upload', formData, {
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
  deleteBook: (bookId, force = false) => apiClient.delete(`/books/${bookId}?force=${force}`),

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

  // 智能检测API
  intelligentDetection: (data) => {
    return apiClient.post('/content-preparation/intelligent-detection', data)
  },

  // 获取书籍章节列表
  getBookChapters: (bookId, params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.skip !== undefined) queryParams.append('skip', params.skip)
    if (params.limit !== undefined) queryParams.append('limit', params.limit)
    if (params.status_filter) queryParams.append('status_filter', params.status_filter)
    if (params.fields) queryParams.append('fields', params.fields)
    if (params.exclude_content !== undefined) queryParams.append('exclude_content', params.exclude_content)
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)

    const queryString = queryParams.toString()
    const url = queryString
      ? `/books/${bookId}/chapters?${queryString}`
      : `/books/${bookId}/chapters`

    return apiClient.get(url)
  },

  // 智能准备章节用于语音合成（使用长超时客户端）
  prepareChapterForSynthesis: (chapterId, params = {}) => {
    // 使用llmAnalysisClient来处理可能的长时间AI分析任务
    return llmAnalysisClient.post(`/content-preparation/prepare-synthesis/${chapterId}`, params)
  },

  // 获取章节智能准备状态
  getPreparationStatus: (chapterId) =>
    apiClient.get(`/content-preparation/preparation-status/${chapterId}`),

  // 获取章节内容统计
  getContentStats: (chapterId) => apiClient.get(`/content-preparation/content-stats/${chapterId}`),

  // 获取章节合成预览
  getSynthesisPreview: (chapterId) =>
    apiClient.get(`/content-preparation/synthesis-preview/${chapterId}`),

  // 获取已有的智能准备结果（不重新执行）
  getPreparationResult: (chapterId, options = {}) => {
    const params = {}
    if (options.force_refresh) {
      params.force_refresh = true
    }

    return apiClient.get(`/content-preparation/result/${chapterId}`, { params })
  },

  // 更新智能准备结果
  updatePreparationResult: (chapterId, data) =>
    apiClient.put(`/content-preparation/result/${chapterId}`, data),

  // AI重新分段
  aiResegmentText: (data) => apiClient.post(`/content-preparation/ai-resegment`, data),

  // 获取书籍的所有智能准备结果
  getBookAnalysisResults: (bookId, params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.chapter_ids && Array.isArray(params.chapter_ids)) {
      queryParams.append('chapter_ids', params.chapter_ids.join(','))
    }

    const queryString = queryParams.toString()
    const url = queryString
      ? `/books/${bookId}/analysis-results?${queryString}`
      : `/books/${bookId}/analysis-results`

    return apiClient.get(url)
  },

  // ========== 角色管理相关API ==========

  // 获取书籍角色汇总
  getBookCharacters: (bookId) => apiClient.get(`/books/${bookId}/characters`),

  // 设置单个角色的语音映射
  setCharacterVoiceMapping: (bookId, characterName, voiceId) => {
    const formData = new FormData()
    formData.append('voice_id', voiceId)

    return apiClient.post(
      `/books/${bookId}/characters/${encodeURIComponent(characterName)}/voice-mapping`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
  },

  // 批量设置角色语音映射
  batchSetCharacterVoiceMappings: (bookId, mappings) => {
    const formData = new FormData()
    formData.append('mappings', JSON.stringify(mappings))

    return apiClient.post(`/books/${bookId}/characters/batch-voice-mappings`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 重建书籍角色汇总
  rebuildCharacterSummary: (bookId) => apiClient.post(`/books/${bookId}/characters/rebuild-summary`)
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
    if (params.include_emotion !== undefined)
      queryParams.append('include_emotion', params.include_emotion)
    if (params.processing_mode) queryParams.append('processing_mode', params.processing_mode)

    const queryString = queryParams.toString()
    const url = queryString
      ? `/chapters/${chapterId}/prepare-synthesis?${queryString}`
      : `/chapters/${chapterId}/prepare-synthesis`

    return apiClient.post(url)
  },

  // 获取合成预览
  getSynthesisPreview: (chapterId, maxSegments = 10) =>
    apiClient.get(`/chapters/${chapterId}/synthesis-preview?max_segments=${maxSegments}`),

  // 获取内容统计
  getContentStats: (chapterId) => apiClient.get(`/chapters/${chapterId}/content-stats`)
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

  // 同步音频文件（旧版，保持兼容性）
  syncFiles: () => apiClient.post('/audio-library/sync'),

  // 下载单个音频文件
  downloadFile: (fileId) =>
    apiClient.get(`/audio-library/download/${fileId}`, {
      responseType: 'blob'
    }),

  // 批量下载音频文件
  batchDownload: (fileIds) =>
    apiClient.post('/audio-library/batch-download', fileIds, {
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

// 音频同步API（新版增强功能）
export const audioSyncAPI = {
  // 同步所有音频文件
  syncAll: (fullScan = false, background = false) => {
    const params = new URLSearchParams()
    if (fullScan) params.append('full_scan', 'true')
    if (background) params.append('background', 'true')

    const queryString = params.toString()
    const url = queryString ? `/audio-sync/sync-all?${queryString}` : '/audio-sync/sync-all'

    return apiClient.post(url)
  },

  // 同步音频库文件
  syncAudioLibrary: (fullScan = false) => {
    const params = new URLSearchParams()
    if (fullScan) params.append('full_scan', 'true')

    const queryString = params.toString()
    const url = queryString
      ? `/audio-sync/sync-audio-library?${queryString}`
      : '/audio-sync/sync-audio-library'

    return apiClient.post(url)
  },

  // 同步环境音文件
  syncEnvironmentSounds: (fullScan = false) => {
    const params = new URLSearchParams()
    if (fullScan) params.append('full_scan', 'true')

    const queryString = params.toString()
    const url = queryString
      ? `/audio-sync/sync-environment-sounds?${queryString}`
      : '/audio-sync/sync-environment-sounds'

    return apiClient.post(url)
  },

  // 验证文件完整性
  verifyIntegrity: () => apiClient.get('/audio-sync/verify-integrity'),

  // 清理孤立记录
  cleanupOrphaned: (dryRun = true) => {
    const params = new URLSearchParams()
    if (!dryRun) params.append('dry_run', 'false')

    const queryString = params.toString()
    const url = queryString
      ? `/audio-sync/cleanup-orphaned?${queryString}`
      : '/audio-sync/cleanup-orphaned'

    return apiClient.post(url)
  },

  // 获取同步状态
  getStatus: () => apiClient.get('/audio-sync/status'),

  // 调度器管理
  scheduler: {
    // 获取调度器状态
    getStatus: () => apiClient.get('/audio-sync/scheduler/status'),

    // 启动调度器
    start: () => apiClient.post('/audio-sync/scheduler/start'),

    // 停止调度器
    stop: () => apiClient.post('/audio-sync/scheduler/stop'),

    // 手动触发同步
    triggerSync: (fullScan = false) => {
      const params = new URLSearchParams()
      if (fullScan) params.append('full_scan', 'true')

      const queryString = params.toString()
      const url = queryString
        ? `/audio-sync/scheduler/trigger?${queryString}`
        : '/audio-sync/scheduler/trigger'

      return apiClient.post(url)
    },

    // 暂停任务
    pauseJob: (jobId) => apiClient.post(`/audio-sync/scheduler/jobs/${jobId}/pause`),

    // 恢复任务
    resumeJob: (jobId) => apiClient.post(`/audio-sync/scheduler/jobs/${jobId}/resume`)
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
  getPerformanceHistory: (hours = 24) =>
    apiClient.get(`/monitor/performance-history?hours=${hours}`)
}

// 智能检测API
export const intelligentDetection = (chapterId, enableAiDetection = true) => {
  return apiClient.post(`/content-preparation/detect/${chapterId}`, {
    use_ai: enableAiDetection,
    auto_fix: false
  })
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

// 环境音管理API
export const environmentSoundsAPI = {
  // 获取分类列表
  getCategories: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.active_only !== undefined) queryParams.append('active_only', params.active_only)

    const queryString = queryParams.toString()
    const url = queryString
      ? `/environment-sounds/categories?${queryString}`
      : '/environment-sounds/categories'
    return apiClient.get(url)
  },

  // 获取标签列表
  getTags: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.popular_only !== undefined) queryParams.append('popular_only', params.popular_only)
    if (params.limit) queryParams.append('limit', params.limit)

    const queryString = queryParams.toString()
    const url = queryString ? `/environment-sounds/tags?${queryString}` : '/environment-sounds/tags'
    return apiClient.get(url)
  },

  // 获取预设列表
  getPresets: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.category_id) queryParams.append('category_id', params.category_id)

    const queryString = queryParams.toString()
    const url = queryString
      ? `/environment-sounds/presets?${queryString}`
      : '/environment-sounds/presets'
    return apiClient.get(url)
  },

  // 获取环境音列表
  getEnvironmentSounds: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)
    if (params.category_id) queryParams.append('category_id', params.category_id)
    if (params.tag_ids) queryParams.append('tag_ids', params.tag_ids)
    if (params.search) queryParams.append('search', params.search)
    if (params.status) queryParams.append('status', params.status)
    if (params.featured_only !== undefined)
      queryParams.append('featured_only', params.featured_only)
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)

    const queryString = queryParams.toString()
    const url = queryString ? `/environment-sounds/?${queryString}` : '/environment-sounds/'
    return apiClient.get(url)
  },

  // 获取单个环境音详情
  getEnvironmentSound: (id) => apiClient.get(`/environment-sounds/${id}`),

  // 生成环境音
  generateEnvironmentSound: (data) => apiClient.post('/environment-sounds/generate', data),

  // 重新生成环境音
  regenerateEnvironmentSound: (id) => apiClient.post(`/environment-sounds/${id}/regenerate`),

  // 播放环境音（记录播放日志）
  playEnvironmentSound: (id) => apiClient.post(`/environment-sounds/${id}/play`),

  // 下载环境音
  downloadEnvironmentSound: (id) =>
    apiClient.get(`/environment-sounds/${id}/download`, {
      responseType: 'blob'
    }),

  // 切换收藏状态
  toggleFavorite: (id) => apiClient.post(`/environment-sounds/${id}/favorite`),

  // 删除环境音
  deleteEnvironmentSound: (id) => apiClient.delete(`/environment-sounds/${id}`),

  // 获取统计数据
  getStats: () => apiClient.get('/environment-sounds/stats'),

  // TangoFlux健康检查
  checkTangoFluxHealth: () => apiClient.get('/environment-sounds/tangoflux/health'),

  // 批量删除
  batchDelete: (soundIds) =>
    apiClient.post('/environment-sounds/batch-delete', {
      sound_ids: soundIds
    }),

  // 批量更新
  batchUpdate: (soundIds, updates) =>
    apiClient.post('/environment-sounds/batch-update', {
      sound_ids: soundIds,
      ...updates
    })
}

// 环境音生成API (新方案A)
export const environmentGenerationAPI = {
  // 第一步：从synthesis_plan分析环境音需求 - 使用LLM专用客户端，支持5分钟超时
  analyzeEnvironment: (projectId, synthesisData) =>
    llmAnalysisClient.post('/environment-generation/analyze', {
      project_id: projectId,
      synthesis_plan: synthesisData?.synthesis_plan || [], // 修复：确保发送正确的数组格式
      options: synthesisData?.options || {}
    }),

  // 第二步：准备人工校对
  prepareValidation: (projectId) =>
    apiClient.post(`/environment-generation/prepare-validation/${projectId}`),

  // 第三步：应用人工编辑
  editValidation: (projectId, trackIndex, manualEdits) =>
    apiClient.post(`/environment-generation/edit-validation/${projectId}`, {
      track_index: trackIndex,
      manual_edits: manualEdits
    }),

  // 第四步：校对审批
  approveValidation: (projectId, trackIndex, validationResult, notes = null) =>
    apiClient.post(`/environment-generation/approve-validation/${projectId}`, {
      track_index: trackIndex,
      validation_result: validationResult,
      notes: notes
    }),

  // 第五步：完成环境音生成流程
  finalizeGeneration: (projectId) =>
    apiClient.post(`/environment-generation/finalize/${projectId}`),

  // 获取环境音生成状态
  getGenerationStatus: (projectId) => apiClient.get(`/environment-generation/status/${projectId}`),

  // 获取已分析的环境音配置（类似角色管理）
  getEnvironmentConfig: (projectId) => apiClient.get(`/environment-generation/config/${projectId}`),

  // 更新环境音轨道配置（支持手动设置环境音ID）
  updateTrackConfig: (projectId, trackIndex, config) =>
    apiClient.put(`/environment-generation/track/${projectId}/${trackIndex}`, config),

  // 清除环境音生成会话
  clearGenerationSession: (projectId) =>
    apiClient.delete(`/environment-generation/session/${projectId}`),

  // === 新流程API ===

  // 章节级环境音智能分析 - 新流程第2步
  analyzeChaptersEnvironment: (chapterIds, analysisOptions = {}) =>
    llmAnalysisClient.post('/environment-generation/chapters/analyze', {
      chapter_ids: chapterIds,
      analysis_options: analysisOptions
    }),

  // 获取章节环境音时间轴
  getChapterTimeline: (chapterId) =>
    apiClient.get(`/environment-generation/chapters/${chapterId}/timeline`),

  // 环境音智能匹配 - 新流程第3步
  matchEnvironmentSounds: (analysisResult, matchingOptions = {}) =>
    apiClient.post('/environment-generation/match-sounds', {
      analysis_result: analysisResult,
      matching_options: matchingOptions
    }),

  // 搜索环境音
  searchEnvironmentSounds: (keywords, maxResults = 10) =>
    apiClient.get(
      `/environment-generation/sounds/search?keywords=${encodeURIComponent(keywords)}&max_results=${maxResults}`
    ),

  // 环境音批量生成 - 新流程第4步
  generateEnvironmentSounds: (generationPlan, generationOptions = {}) =>
    apiClient.post('/environment-generation/generate-sounds', {
      generation_plan: generationPlan,
      generation_options: generationOptions
    }),

  // 创建环境音时间轴
  createEnvironmentTimeline: (analysisResult, matchingResult, projectName = null) =>
    apiClient.post('/environment-generation/create-timeline', {
      analysis_result: analysisResult,
      matching_result: matchingResult,
      project_name: projectName
    }),

  // 导出时间轴
  exportTimeline: (timelineData, exportFormat = 'generic', outputPath = null) =>
    apiClient.post('/environment-generation/export-timeline', {
      timeline_data: timelineData,
      export_format: exportFormat,
      output_path: outputPath
    }),

  // 获取生成任务状态
  getGenerationTaskStatus: (taskId) =>
    apiClient.get(`/environment-generation/generation/status/${taskId}`),

  // 获取所有生成任务
  getAllGenerationTasks: () => apiClient.get('/environment-generation/generation/tasks')
}

// 环境混音API
export const environmentMixingAPI = {
  // 获取环境混音结果
  getResults: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.search) queryParams.append('search', params.search)
    if (params.project_id) queryParams.append('project_id', params.project_id)
    if (params.status) queryParams.append('status', params.status)
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)

    const queryString = queryParams.toString()
    const url = queryString
      ? `/environment/mixing/results?${queryString}`
      : '/environment/mixing/results'
    return apiClient.get(url)
  },

  // 获取混音统计数据
  getStats: () => apiClient.get('/environment/mixing/stats'),

  // 开始环境混音
  startMixing: (projectId, config) =>
    apiClient.post(`/environment/mixing/${projectId}/start`, config),

  // 下载环境混音作品
  downloadMixing: (mixingId) =>
    apiClient.get(`/environment/mixing/${mixingId}/download`, {
      responseType: 'blob'
    }),

  // 删除环境混音作品
  deleteMixing: (mixingId) => apiClient.delete(`/environment/mixing/${mixingId}`),

  // 获取混音详情
  getMixingDetail: (mixingId) => apiClient.get(`/environment/mixing/${mixingId}`),

  // 预览混音作品
  previewMixing: (mixingId) => apiClient.get(`/environment/mixing/${mixingId}/preview`),

  // 获取混音配置
  getMixingConfig: (mixingId) => apiClient.get(`/environment/mixing/${mixingId}/config`),

  // 更新混音配置
  updateMixingConfig: (mixingId, config) =>
    apiClient.put(`/environment/mixing/${mixingId}/config`, config),

  // 更新环境混音
  updateMixing: (mixingId, config) => apiClient.put(`/environment/mixing/${mixingId}`, config)
}

// 背景音乐库API
export const backgroundMusicAPI = {
  // 获取音乐分类
  getCategories: (activeOnly = true) => {
    const params = new URLSearchParams()
    if (activeOnly) params.append('active_only', 'true')

    const queryString = params.toString()
    const url = queryString
      ? `/background-music/categories?${queryString}`
      : '/background-music/categories'

    return apiClient.get(url)
  },

  // 创建音乐分类
  createCategory: (categoryData) => apiClient.post('/background-music/categories', categoryData),

  // 获取背景音乐列表
  getMusic: (params = {}) => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page)
    if (params.page_size) queryParams.append('page_size', params.page_size)
    if (params.category_id) queryParams.append('category_id', params.category_id)
    if (params.search) queryParams.append('search', params.search)
    if (params.emotion_tags && params.emotion_tags.length > 0) {
      params.emotion_tags.forEach((tag) => queryParams.append('emotion_tags', tag))
    }
    if (params.style_tags && params.style_tags.length > 0) {
      params.style_tags.forEach((tag) => queryParams.append('style_tags', tag))
    }
    if (params.active_only !== undefined) queryParams.append('active_only', params.active_only)
    if (params.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params.sort_order) queryParams.append('sort_order', params.sort_order)

    const queryString = queryParams.toString()
    const url = queryString ? `/background-music/music?${queryString}` : '/background-music/music'

    return apiClient.get(url)
  },

  // 上传背景音乐
  uploadMusic: (musicData, file) => {
    const formData = new FormData()
    formData.append('name', musicData.name)
    if (musicData.description) formData.append('description', musicData.description)
    if (musicData.category_id) formData.append('category_id', musicData.category_id)
    if (musicData.emotion_tags)
      formData.append('emotion_tags', JSON.stringify(musicData.emotion_tags))
    if (musicData.style_tags) formData.append('style_tags', JSON.stringify(musicData.style_tags))
    if (musicData.quality_rating) formData.append('quality_rating', musicData.quality_rating)
    formData.append('file', file)

    return apiClient.post('/background-music/music', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 更新背景音乐
  updateMusic: (musicId, musicData) =>
    apiClient.put(`/background-music/music/${musicId}`, musicData),

  // 删除背景音乐
  deleteMusic: (musicId) => apiClient.delete(`/background-music/music/${musicId}`),

  // 下载背景音乐
  downloadMusic: (musicId) =>
    apiClient.get(`/background-music/music/${musicId}/download`, {
      responseType: 'blob'
    }),

  // 播放背景音乐（记录统计）
  playMusic: (musicId) => apiClient.post(`/background-music/music/${musicId}/play`),

  // 音乐推荐
  recommendMusic: (requestData) => apiClient.post('/background-music/recommend', requestData),

  // 获取统计信息
  getStats: () => apiClient.get('/background-music/stats/overview')
}

// 音乐生成API
export const musicGenerationAPI = {
  // 检查音乐生成服务健康状态
  healthCheck: () => apiClient.get('/music-generation/health'),

  // 为章节生成背景音乐
  generateChapterMusic: (data) => apiClient.post('/music-generation/generate', data),

  // 直接基于描述生成音乐（使用异步接口）
  generateDirectMusic: (data) => apiClient.post('/music-generation-async/generate', data),

  // 批量生成背景音乐 (已禁用 - 资源消耗过大)
  // batchGenerateMusic: (data) => apiClient.post('/music-generation/batch-generate', data),

  // 预览音乐风格
  previewMusicStyle: (data) => apiClient.post('/music-generation/preview-style', data),

  // 获取支持的音乐风格列表
  getSupportedStyles: () => apiClient.get('/music-generation/styles'),

  // 获取音乐生成任务状态
  getTaskStatus: (taskId) => apiClient.get(`/music-generation/tasks/${taskId}`),

  // 清理生成的音乐文件
  cleanupFiles: (params = {}) => apiClient.delete('/music-generation/cleanup', { params }),

  // 获取音乐生成统计信息
  getGenerationStats: (hours = 24) =>
    apiClient.get(`/music-generation/stats/generation?hours=${hours}`),

  // 获取服务信息
  getServiceInfo: () => apiClient.get('/music-generation/service-info')
}

// 默认导出所有API
const api = {
  ...systemAPI,
  ...voiceAPI,
  ...charactersAPI,
  ...readerAPI,
  ...booksAPI,
  ...chaptersAPI,
  ...audioAPI,
  ...monitorAPI,
  ...intelligentAnalysisAPI,
  ...environmentSoundsAPI,
  ...environmentGenerationAPI,
  ...environmentMixingAPI,
  ...backgroundMusicAPI,

  // 环境混音专用接口
  getEnvironmentMixingResults: environmentMixingAPI.getResults,
  getEnvironmentMixingStats: environmentMixingAPI.getStats,
  startEnvironmentMixing: environmentMixingAPI.startMixing,
  downloadEnvironmentMixing: environmentMixingAPI.downloadMixing,
  deleteEnvironmentMixing: environmentMixingAPI.deleteMixing,
  getEnvironmentMixingDetail: environmentMixingAPI.getMixingDetail,
  updateEnvironmentMixing: environmentMixingAPI.updateMixing,
  ...musicGenerationAPI,

  // 智能检测API
  intelligentDetection: (chapterId, enableAiDetection = true) => {
    return apiClient.post(`/content-preparation/detect/${chapterId}`, {
      use_ai: enableAiDetection,
      auto_fix: false
    })
  }
}

export default api
