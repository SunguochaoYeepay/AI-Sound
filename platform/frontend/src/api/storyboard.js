import apiClient from './config.js'

/**
 * 故事板分析API
 * 提供会话管理、卡片管理和WebSocket连接功能
 */
export const storyboardAPI = {
  /**
   * 创建分析会话
   * @param {number} bookId - 书籍ID
   * @param {string} sessionName - 会话名称
   * @param {string} description - 会话描述
   * @param {string} analysisType - 分析类型
   * @returns {Promise} 创建结果
   */
  createSession: (bookId, sessionName, description = null, analysisType = 'standard') => {
    return apiClient.post('/storyboard/sessions', {
      book_id: bookId,
      session_name: sessionName,
      description: description,
      analysis_type: analysisType
    })
  },

  /**
   * 开始分析
   * @param {number} sessionId - 会话ID
   * @returns {Promise} 开始分析结果
   */
  startAnalysis: (sessionId) => {
    return apiClient.post(`/storyboard/sessions/${sessionId}/start`)
  },

  /**
   * 获取会话状态
   * @param {number} sessionId - 会话ID
   * @returns {Promise} 会话状态
   */
  getSessionStatus: (sessionId) => {
    return apiClient.get(`/storyboard/sessions/${sessionId}`)
  },

  /**
   * 获取会话列表
   * @param {Object} params - 查询参数
   * @returns {Promise} 会话列表
   */
  getSessions: (params = {}) => {
    return apiClient.get('/storyboard/sessions', { params })
  },

  /**
   * 获取会话卡片
   * @param {number} sessionId - 会话ID
   * @param {Object} params - 查询参数
   * @returns {Promise} 卡片列表
   */
  getSessionCards: (sessionId, params = {}) => {
    return apiClient.get(`/storyboard/sessions/${sessionId}/cards`, { params })
  },

  /**
   * 获取会话章节
   * @param {number} sessionId - 会话ID
   * @returns {Promise} 章节列表
   */
  getSessionChapters: (sessionId) => {
    return apiClient.get(`/storyboard/sessions/${sessionId}/chapters`)
  },

  /**
   * 获取章节详情
   * @param {number} chapterId - 章节ID
   * @returns {Promise} 章节详情
   */
  getChapterDetail: (chapterId) => {
    return apiClient.get(`/chapters/${chapterId}`)
  },

  /**
   * 获取审核数据
   * @param {number} sessionId - 会话ID
   * @param {number} chapterId - 章节ID
   * @returns {Promise} 审核数据
   */
  getReviewData: (sessionId, chapterId) => {
    return apiClient.get(`/storyboard/sessions/${sessionId}/chapters/${chapterId}/cards`)
  },

  /**
   * 确认章节
   * @param {number} sessionId - 会话ID
   * @param {number} chapterId - 章节ID
   * @returns {Promise} 确认结果
   */
  confirmChapter: (sessionId, chapterId) => {
    return apiClient.post(`/storyboard/review/${sessionId}/${chapterId}/confirm`)
  },

  /**
   * 分析单个章节
   * @param {number} sessionId - 会话ID
   * @param {number} chapterId - 章节ID
   * @returns {Promise} 分析结果
   */
  analyzeChapter: (sessionId, chapterId) => {
    return apiClient.post(`/storyboard/sessions/${sessionId}/chapters/${chapterId}/analyze`)
  },

  /**
   * 评估分析质量（临时实现）
   * @param {number} sessionId - 会话ID
   * @returns {Promise} 质量评估结果
   */
  assessQuality: (sessionId) => {
    // 临时实现，返回模拟数据
    return Promise.resolve({
      data: {
        overall_score: 75,
        card_type_scores: {
          story: { count: 1, score: 80, confirmed_count: 1, total_confidence: 0.8 },
          character: { count: 2, score: 70, confirmed_count: 1, total_confidence: 0.7 },
          scene: { count: 3, score: 75, confirmed_count: 2, total_confidence: 0.75 },
          event: { count: 4, score: 80, confirmed_count: 3, total_confidence: 0.8 },
          emotion: { count: 2, score: 70, confirmed_count: 1, total_confidence: 0.7 },
          audio_storyboard: { count: 1, score: 75, confirmed_count: 1, total_confidence: 0.75 }
        },
        recommendations: [
          '整体分析质量良好',
          '建议优化角色卡片内容',
          '情绪分析可以更细致'
        ],
        total_cards: 13
      }
    })
  },

  /**
   * 更新卡片
   * @param {number} cardId - 卡片ID
   * @param {Object} data - 更新数据
   * @returns {Promise} 更新结果
   */
  updateCard: (cardId, data) => {
    return apiClient.put(`/storyboard/cards/${cardId}`, data)
  },

  /**
   * 确认卡片
   * @param {number} cardId - 卡片ID
   * @returns {Promise} 确认结果
   */
  confirmCard: (cardId) => {
    return apiClient.post(`/storyboard/cards/${cardId}/confirm`)
  },

  /**
   * 重新分析卡片
   * @param {number} cardId - 卡片ID
   * @returns {Promise} 重新分析结果
   */
  reanalyzeCard: (cardId) => {
    return apiClient.post(`/storyboard/cards/${cardId}/reanalyze`)
  },

  /**
   * 确认会话
   * @param {number} sessionId - 会话ID
   * @returns {Promise} 确认结果
   */
  confirmSession: (sessionId) => {
    return apiClient.post(`/storyboard/sessions/${sessionId}/confirm`)
  },

  /**
   * 重新分析会话
   * @param {number} sessionId - 会话ID
   * @returns {Promise} 重新分析结果
   */
  reanalyzeSession: (sessionId) => {
    return apiClient.post(`/storyboard/sessions/${sessionId}/reanalyze`)
  },

  /**
   * 分析单个章节
   * @param {number} sessionId - 会话ID
   * @param {number} chapterId - 章节ID
   * @returns {Promise} 分析结果
   */
  analyzeChapter: (sessionId, chapterId) => {
    return apiClient.post(`/storyboard/sessions/${sessionId}/chapters/${chapterId}/analyze`)
  },

  /**
   * 评估分析质量（使用临时实现）
   * @param {number} sessionId - 会话ID
   * @returns {Promise} 质量评估结果
   */
  // assessQuality: (sessionId) => {
  //   return apiClient.get(`/storyboard/sessions/${sessionId}/quality-assessment`)
  // },

  /**
   * 删除会话
   * @param {number} sessionId - 会话ID
   * @returns {Promise} 删除结果
   */
  deleteSession: (sessionId) => {
    return apiClient.delete(`/storyboard/sessions/${sessionId}`)
  },

  /**
   * 创建WebSocket连接
   * @param {number} sessionId - 会话ID
   * @returns {WebSocket} WebSocket实例
   */
  createWebSocket: (sessionId) => {
    // 使用通用的WebSocket端点，让Vite代理处理连接
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`
    console.log('WebSocket URL:', wsUrl)
    return new WebSocket(wsUrl)
  }
}

/**
 * 卡片类型常量
 */
export const CARD_TYPES = {
  STORY: 'story',
  CHARACTER: 'character',
  SCENE: 'scene',
  EVENT: 'event',
  EMOTION: 'emotion',
  AUDIO_STORYBOARD: 'audio_storyboard'
}

/**
 * 卡片类型配置
 */
export const CARD_TYPE_CONFIG = {
  [CARD_TYPES.STORY]: {
    name: '故事卡',
    icon: '📖',
    color: '#fa8c16',
    description: '故事主题和结构分析'
  },
  [CARD_TYPES.CHARACTER]: {
    name: '角色卡',
    icon: '🎭',
    color: '#1890ff',
    description: '角色特征和语音设定'
  },
  [CARD_TYPES.SCENE]: {
    name: '场景卡',
    icon: '🎬',
    color: '#52c41a',
    description: '场景环境和氛围描述'
  },
  [CARD_TYPES.EVENT]: {
    name: '事件卡',
    icon: '📝',
    color: '#722ed1',
    description: '事件情节和对话内容'
  },
  [CARD_TYPES.EMOTION]: {
    name: '情绪卡',
    icon: '💝',
    color: '#eb2f96',
    description: '情感变化和表达方式'
  },
  [CARD_TYPES.AUDIO_STORYBOARD]: {
    name: '音频分镜卡',
    icon: '🎵',
    color: '#13c2c2',
    description: '音频制作时间轴和配置'
  }
}

/**
 * 分析状态常量
 */
export const ANALYSIS_STATUS = {
  PENDING: 'pending',
  ANALYZING: 'analyzing',
  COMPLETED: 'completed',
  READY_FOR_REVIEW: 'ready_for_review',
  CONFIRMED: 'confirmed',
  FAILED: 'failed'
}

/**
 * 分析状态配置
 */
export const STATUS_CONFIG = {
  [ANALYSIS_STATUS.PENDING]: {
    name: '等待分析',
    color: '#faad14',
    icon: '⏳'
  },
  [ANALYSIS_STATUS.ANALYZING]: {
    name: '分析中',
    color: '#1890ff',
    icon: '🔄'
  },
  [ANALYSIS_STATUS.COMPLETED]: {
    name: '分析完成',
    color: '#52c41a',
    icon: '✅'
  },
  [ANALYSIS_STATUS.READY_FOR_REVIEW]: {
    name: '待确认',
    color: '#fa8c16',
    icon: '👀'
  },
  [ANALYSIS_STATUS.CONFIRMED]: {
    name: '已确认',
    color: '#52c41a',
    icon: '✅'
  },
  [ANALYSIS_STATUS.FAILED]: {
    name: '分析失败',
    color: '#f5222d',
    icon: '❌'
  }
}
