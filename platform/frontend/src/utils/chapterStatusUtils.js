/**
 * 章节状态统一管理工具
 * 解决智能准备状态和合成状态耦合严重的问题
 */

// 智能准备状态枚举
export const PREPARATION_STATUS = {
  PENDING: 'pending',
  ANALYZING: 'analyzing', 
  COMPLETED: 'completed',
  FAILED: 'failed'
}

// 语音合成状态枚举
export const SYNTHESIS_STATUS = {
  PENDING: 'pending',
  READY: 'ready',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
}

/**
 * 获取智能准备状态文本
 * @param {Object} chapter - 章节对象
 * @param {Object} preparationStatus - 准备状态对象（来自API）
 * @returns {string} 状态文本
 */
export function getPreparationStatusText(chapter, preparationStatus = null) {
  // 优先使用API返回的状态
  if (preparationStatus) {
    if (preparationStatus.preparation_complete) {
      return `已准备 (${preparationStatus.segments_count || 0}段)`
    }
    if (preparationStatus.analysis_status === 'analyzing') {
      return '准备中...'
    }
    if (preparationStatus.analysis_status === 'failed') {
      return '准备失败'
    }
    return '未准备'
  }

  // 降级使用章节字段
  if (chapter) {
    const status = chapter.analysis_status || PREPARATION_STATUS.PENDING
    const statusMap = {
      [PREPARATION_STATUS.PENDING]: '未准备',
      [PREPARATION_STATUS.ANALYZING]: '准备中...',
      [PREPARATION_STATUS.COMPLETED]: '已准备',
      [PREPARATION_STATUS.FAILED]: '准备失败'
    }
    return statusMap[status] || '未知'
  }

  return '未知'
}

/**
 * 获取智能准备状态颜色
 * @param {Object} chapter - 章节对象
 * @param {Object} preparationStatus - 准备状态对象（来自API）
 * @returns {string} 状态颜色
 */
export function getPreparationStatusColor(chapter, preparationStatus = null) {
  // 优先使用API返回的状态
  if (preparationStatus) {
    if (preparationStatus.preparation_complete) return 'green'
    if (preparationStatus.analysis_status === 'analyzing') return 'blue'
    if (preparationStatus.analysis_status === 'failed') return 'red'
    return 'default'
  }

  // 降级使用章节字段
  if (chapter) {
    const status = chapter.analysis_status || PREPARATION_STATUS.PENDING
    const colorMap = {
      [PREPARATION_STATUS.PENDING]: 'default',
      [PREPARATION_STATUS.ANALYZING]: 'blue',
      [PREPARATION_STATUS.COMPLETED]: 'green',
      [PREPARATION_STATUS.FAILED]: 'red'
    }
    return colorMap[status] || 'default'
  }

  return 'default'
}

/**
 * 获取语音合成状态文本（仅用于合成中心）
 * @param {Object} chapter - 章节对象
 * @returns {string} 状态文本
 */
export function getSynthesisStatusText(chapter) {
  if (!chapter) return '未知'
  
  const status = chapter.synthesis_status || SYNTHESIS_STATUS.PENDING
  const statusMap = {
    [SYNTHESIS_STATUS.PENDING]: '待合成',
    [SYNTHESIS_STATUS.READY]: '待合成',
    [SYNTHESIS_STATUS.PROCESSING]: '合成中',
    [SYNTHESIS_STATUS.COMPLETED]: '已完成',
    [SYNTHESIS_STATUS.FAILED]: '合成失败'
  }
  return statusMap[status] || '待合成'
}

/**
 * 获取语音合成状态颜色（仅用于合成中心）
 * @param {Object} chapter - 章节对象
 * @returns {string} 状态颜色
 */
export function getSynthesisStatusColor(chapter) {
  if (!chapter) return 'gray'
  
  const status = chapter.synthesis_status || SYNTHESIS_STATUS.PENDING
  const colorMap = {
    [SYNTHESIS_STATUS.PENDING]: 'gray',
    [SYNTHESIS_STATUS.READY]: 'gray',
    [SYNTHESIS_STATUS.PROCESSING]: 'blue',
    [SYNTHESIS_STATUS.COMPLETED]: 'green',
    [SYNTHESIS_STATUS.FAILED]: 'red'
  }
  return colorMap[status] || 'gray'
}

/**
 * 判断章节是否已完成智能准备
 * @param {Object} chapter - 章节对象
 * @param {Object} preparationStatus - 准备状态对象（来自API）
 * @returns {boolean} 是否已准备
 */
export function isChapterPrepared(chapter, preparationStatus = null) {
  // 优先使用API返回的状态
  if (preparationStatus) {
    return preparationStatus.preparation_complete === true
  }

  // 降级使用章节字段
  if (chapter) {
    return chapter.analysis_status === PREPARATION_STATUS.COMPLETED
  }

  return false
}

/**
 * 判断章节是否可以开始合成
 * @param {Object} chapter - 章节对象
 * @param {Object} preparationStatus - 准备状态对象（来自API）
 * @returns {boolean} 是否可以开始合成
 */
export function canStartSynthesis(chapter, preparationStatus = null) {
  // 必须先完成智能准备
  if (!isChapterPrepared(chapter, preparationStatus)) {
    return false
  }

  // 不能正在合成中
  if (chapter && chapter.synthesis_status === SYNTHESIS_STATUS.PROCESSING) {
    return false
  }

  return true
}

/**
 * 获取章节综合状态描述（用于调试）
 * @param {Object} chapter - 章节对象
 * @param {Object} preparationStatus - 准备状态对象（来自API）
 * @returns {Object} 状态描述对象
 */
export function getChapterStatusSummary(chapter, preparationStatus = null) {
  return {
    chapter_id: chapter?.id || 'unknown',
    chapter_title: chapter?.chapter_title || chapter?.title || 'unknown',
    analysis_status: chapter?.analysis_status || 'unknown',
    synthesis_status: chapter?.synthesis_status || 'unknown',
    preparation_complete: preparationStatus?.preparation_complete || false,
    preparation_text: getPreparationStatusText(chapter, preparationStatus),
    synthesis_text: getSynthesisStatusText(chapter),
    can_start_synthesis: canStartSynthesis(chapter, preparationStatus)
  }
}

/**
 * 状态管理类
 * 用于复杂的状态管理场景
 */
export class ChapterStatusManager {
  constructor() {
    this.chapters = new Map()
    this.preparationStatuses = new Map()
  }

  /**
   * 更新章节数据
   * @param {Array} chapters - 章节数组
   */
  updateChapters(chapters) {
    chapters.forEach(chapter => {
      this.chapters.set(chapter.id, chapter)
    })
  }

  /**
   * 更新准备状态数据
   * @param {Object} statusMap - 状态映射对象
   */
  updatePreparationStatuses(statusMap) {
    Object.entries(statusMap).forEach(([chapterId, status]) => {
      this.preparationStatuses.set(parseInt(chapterId), status)
    })
  }

  /**
   * 获取章节状态
   * @param {number} chapterId - 章节ID
   * @returns {Object} 状态对象
   */
  getChapterStatus(chapterId) {
    const chapter = this.chapters.get(chapterId)
    const preparationStatus = this.preparationStatuses.get(chapterId)
    
    return {
      chapter,
      preparationStatus,
      preparationText: getPreparationStatusText(chapter, preparationStatus),
      preparationColor: getPreparationStatusColor(chapter, preparationStatus),
      synthesisText: getSynthesisStatusText(chapter),
      synthesisColor: getSynthesisStatusColor(chapter),
      isPrepared: isChapterPrepared(chapter, preparationStatus),
      canStartSynthesis: canStartSynthesis(chapter, preparationStatus),
      summary: getChapterStatusSummary(chapter, preparationStatus)
    }
  }

  /**
   * 获取所有章节状态
   * @returns {Map} 状态映射
   */
  getAllChapterStatuses() {
    const statuses = new Map()
    this.chapters.forEach((chapter, chapterId) => {
      statuses.set(chapterId, this.getChapterStatus(chapterId))
    })
    return statuses
  }
}

/**
 * 章节状态同步管理器
 * 解决前端状态与数据库状态不一致的问题
 */
export class ChapterStatusSyncManager {
  constructor(apiClient) {
    this.apiClient = apiClient
    this.chapters = new Map()
    this.syncCallbacks = new Set()
    this.syncInterval = null
  }

  /**
   * 初始化管理器
   * @param {Array} chapters - 初始章节数据
   * @param {number} bookId - 书籍ID
   */
  initialize(chapters, bookId) {
    this.bookId = bookId
    this.updateChapters(chapters)
    this.startAutoSync()
  }

  /**
   * 更新章节数据
   * @param {Array} chapters - 章节数组
   */
  updateChapters(chapters) {
    chapters.forEach(chapter => {
      this.chapters.set(chapter.id, { ...chapter })
    })
  }

  /**
   * 同步单个章节状态
   * @param {number} chapterId - 章节ID
   * @param {string} newStatus - 新状态
   */
  async syncChapterStatus(chapterId, newStatus) {
    console.log('🔄 [StatusSync] 同步章节状态:', { chapterId, newStatus })
    
    // 更新本地状态
    const chapter = this.chapters.get(chapterId)
    if (chapter) {
      const oldStatus = chapter.synthesis_status
      chapter.synthesis_status = newStatus
      chapter.updated_at = new Date().toISOString()
      
      console.log('✅ [StatusSync] 本地状态更新:', { 
        章节ID: chapterId, 
        旧状态: oldStatus, 
        新状态: newStatus 
      })
    }

    // 验证服务器状态
    await this.validateServerStatus(chapterId, newStatus)
    
    // 通知所有监听器
    this.notifyCallbacks(chapterId, newStatus)
  }

  /**
   * 验证服务器状态
   * @param {number} chapterId - 章节ID
   * @param {string} expectedStatus - 期望状态
   */
  async validateServerStatus(chapterId, expectedStatus) {
    if (!this.bookId) return

    try {
      const response = await this.apiClient.get(`/books/${this.bookId}/chapters`)
      if (response.data.success && response.data.data) {
        const serverChapter = response.data.data.find(ch => ch.id === chapterId)
        if (serverChapter) {
          if (serverChapter.synthesis_status !== expectedStatus) {
            console.warn('⚠️ [StatusSync] 前端状态与服务器不一致:', {
              章节ID: chapterId,
              前端状态: expectedStatus,
              服务器状态: serverChapter.synthesis_status
            })
            
            // 以服务器状态为准
            await this.syncChapterStatus(chapterId, serverChapter.synthesis_status)
          }
        }
      }
    } catch (error) {
      console.error('❌ [StatusSync] 验证服务器状态失败:', error)
    }
  }

  /**
   * 批量同步所有章节状态
   */
  async syncAllChapterStatuses() {
    if (!this.bookId) return

    console.log('🔄 [StatusSync] 批量同步所有章节状态')
    try {
      const response = await this.apiClient.get(`/books/${this.bookId}/chapters`)
      if (response.data.success && response.data.data) {
        const serverChapters = response.data.data
        
        serverChapters.forEach(serverChapter => {
          const localChapter = this.chapters.get(serverChapter.id)
          if (localChapter) {
            let hasChanges = false
            
            if (localChapter.synthesis_status !== serverChapter.synthesis_status) {
              console.log('🔄 [StatusSync] 更新synthesis_status:', {
                章节ID: serverChapter.id,
                章节标题: serverChapter.chapter_title,
                旧状态: localChapter.synthesis_status,
                新状态: serverChapter.synthesis_status
              })
              localChapter.synthesis_status = serverChapter.synthesis_status
              hasChanges = true
            }
            
            if (localChapter.analysis_status !== serverChapter.analysis_status) {
              console.log('🔄 [StatusSync] 更新analysis_status:', {
                章节ID: serverChapter.id,
                旧状态: localChapter.analysis_status,
                新状态: serverChapter.analysis_status
              })
              localChapter.analysis_status = serverChapter.analysis_status
              hasChanges = true
            }
            
            if (hasChanges) {
              localChapter.updated_at = serverChapter.updated_at
              this.notifyCallbacks(serverChapter.id, serverChapter.synthesis_status)
            }
          }
        })
      }
    } catch (error) {
      console.error('❌ [StatusSync] 批量同步状态失败:', error)
    }
  }

  /**
   * 添加状态变化监听器
   * @param {Function} callback - 回调函数
   */
  addSyncCallback(callback) {
    this.syncCallbacks.add(callback)
  }

  /**
   * 移除状态变化监听器
   * @param {Function} callback - 回调函数
   */
  removeSyncCallback(callback) {
    this.syncCallbacks.delete(callback)
  }

  /**
   * 通知所有监听器
   * @param {number} chapterId - 章节ID
   * @param {string} newStatus - 新状态
   */
  notifyCallbacks(chapterId, newStatus) {
    this.syncCallbacks.forEach(callback => {
      try {
        callback(chapterId, newStatus)
      } catch (error) {
        console.error('❌ [StatusSync] 回调执行失败:', error)
      }
    })
  }

  /**
   * 启动自动同步
   */
  startAutoSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval)
    }
    
    this.syncInterval = setInterval(async () => {
      await this.syncAllChapterStatuses()
    }, 30000) // 每30秒同步一次
    
    console.log('🚀 [StatusSync] 启动自动状态同步')
  }

  /**
   * 停止自动同步
   */
  stopAutoSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval)
      this.syncInterval = null
      console.log('🛑 [StatusSync] 停止自动状态同步')
    }
  }

  /**
   * 获取章节状态
   * @param {number} chapterId - 章节ID
   * @returns {Object} 章节对象
   */
  getChapter(chapterId) {
    return this.chapters.get(chapterId)
  }

  /**
   * 获取所有章节
   * @returns {Array} 章节数组
   */
  getAllChapters() {
    return Array.from(this.chapters.values())
  }

  /**
   * 清理资源
   */
  destroy() {
    this.stopAutoSync()
    this.chapters.clear()
    this.syncCallbacks.clear()
    console.log('🧹 [StatusSync] 资源清理完成')
  }
}

// 导出默认实例
export const chapterStatusManager = new ChapterStatusManager() 