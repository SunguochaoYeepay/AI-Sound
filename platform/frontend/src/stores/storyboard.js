import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { storyboardAPI, ANALYSIS_STATUS, CARD_TYPES } from '@/api/storyboard'
import booksAPI from '@/api/books'

/**
 * 故事板分析状态管理
 */
export const useStoryboardStore = defineStore('storyboard', () => {
  // 状态
  const sessions = ref([])
  const currentSession = ref(null)
  const cards = ref([])
  const analysisProgress = ref(0)
  const currentStep = ref('')
  const isAnalyzing = ref(false)
  const loading = ref(false)
  const error = ref(null)

  // 计算属性
  const sessionCount = computed(() => sessions.value.length)
  
  const completedSessions = computed(() => 
    sessions.value.filter(s => s.status === ANALYSIS_STATUS.COMPLETED || s.status === ANALYSIS_STATUS.CONFIRMED)
  )
  
  const pendingSessions = computed(() => 
    sessions.value.filter(s => s.status === ANALYSIS_STATUS.PENDING || s.status === ANALYSIS_STATUS.ANALYZING)
  )
  
  const failedSessions = computed(() => 
    sessions.value.filter(s => s.status === ANALYSIS_STATUS.FAILED)
  )
  
  const cardsByType = computed(() => {
    const grouped = {}
    Object.values(CARD_TYPES).forEach(type => {
      grouped[type] = cards.value.filter(card => card.card_type === type)
    })
    return grouped
  })
  
  const cardCounts = computed(() => {
    const counts = {}
    Object.values(CARD_TYPES).forEach(type => {
      counts[type] = cardsByType.value[type]?.length || 0
    })
    return counts
  })

  // 获取书籍信息
  const getBookInfo = async (bookId) => {
    try {
      const response = await booksAPI.getBook(bookId)
      return response.data
    } catch (err) {
      console.warn('获取书籍信息失败:', err)
      return null
    }
  }

  // 会话管理
  const createAnalysisSession = async (bookId, sessionName = null, description = null, analysisType = 'standard') => {
    try {
      loading.value = true
      error.value = null
      
      // 如果没有提供会话名称，生成一个默认名称
      if (!sessionName) {
        const book = await getBookInfo(bookId)
        sessionName = `${book?.title || '未知书籍'} - AI分析会话`
      }
      
      const response = await storyboardAPI.createSession(bookId, sessionName, description, analysisType)
      const newSession = response.data
      
      sessions.value.unshift(newSession)
      return newSession
    } catch (err) {
      error.value = '创建分析会话失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  const startAnalysis = async (sessionId) => {
    try {
      loading.value = true
      error.value = null
      
      await storyboardAPI.startAnalysis(sessionId)
      
      // 更新会话状态
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        session.status = ANALYSIS_STATUS.ANALYZING
        session.progress = 0
      }
      
      if (currentSession.value?.id === sessionId) {
        currentSession.value.status = ANALYSIS_STATUS.ANALYZING
        currentSession.value.progress = 0
        isAnalyzing.value = true
      }
    } catch (err) {
      error.value = '开始分析失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  const loadSessions = async (params = {}) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await storyboardAPI.getSessions(params)
      // 根据后端API返回格式处理数据
      if (response.data && response.data.sessions && Array.isArray(response.data.sessions)) {
        sessions.value = response.data.sessions
      } else if (response.data && Array.isArray(response.data)) {
        sessions.value = response.data
      } else {
        console.warn('Unexpected API response format:', response.data)
        sessions.value = []
      }
    } catch (err) {
      error.value = '加载会话列表失败: ' + (err.message || '未知错误')
      console.error('Load sessions error:', err)
      sessions.value = []
      throw err
    } finally {
      loading.value = false
    }
  }

  const loadSessionDetail = async (sessionId) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await storyboardAPI.getSessionStatus(sessionId)
      const session = response.data
      
      // 更新会话列表中的对应项
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessions.value[index] = session
      }
      
      // 设置当前会话
      currentSession.value = session
      
      return session
    } catch (err) {
      error.value = '加载会话详情失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  const setCurrentSession = (session) => {
    currentSession.value = session
    if (session) {
      loadSessionCards(session.id)
    } else {
      cards.value = []
    }
  }

  // 卡片管理
  const loadSessionCards = async (sessionId, params = {}) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await storyboardAPI.getSessionCards(sessionId, params)
      cards.value = response.data
    } catch (err) {
      error.value = '加载卡片失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateCard = async (cardId, data) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await storyboardAPI.updateCard(cardId, data)
      const updatedCard = response.data
      
      // 更新卡片列表中的对应项
      const index = cards.value.findIndex(c => c.id === cardId)
      if (index !== -1) {
        cards.value[index] = updatedCard
      }
      
      return updatedCard
    } catch (err) {
      error.value = '更新卡片失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  const confirmCard = async (cardId) => {
    try {
      loading.value = true
      error.value = null
      
      await storyboardAPI.confirmCard(cardId)
      
      // 更新卡片状态
      const card = cards.value.find(c => c.id === cardId)
      if (card) {
        card.is_confirmed = true
      }
    } catch (err) {
      error.value = '确认卡片失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  const reanalyzeCard = async (cardId) => {
    try {
      loading.value = true
      error.value = null
      
      await storyboardAPI.reanalyzeCard(cardId)
      
      // 重新加载卡片
      if (currentSession.value) {
        await loadSessionCards(currentSession.value.id)
      }
    } catch (err) {
      error.value = '重新分析卡片失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  // 会话操作
  const confirmSession = async (sessionId) => {
    try {
      loading.value = true
      error.value = null
      
      await storyboardAPI.confirmSession(sessionId)
      
      // 更新会话状态
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        session.status = ANALYSIS_STATUS.CONFIRMED
      }
      
      if (currentSession.value?.id === sessionId) {
        currentSession.value.status = ANALYSIS_STATUS.CONFIRMED
      }
    } catch (err) {
      error.value = '确认会话失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  const reanalyzeSession = async (sessionId) => {
    try {
      loading.value = true
      error.value = null
      
      await storyboardAPI.reanalyzeSession(sessionId)
      
      // 重新加载会话详情
      await loadSessionDetail(sessionId)
    } catch (err) {
      error.value = '重新分析会话失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteSession = async (sessionId) => {
    try {
      loading.value = true
      error.value = null
      
      await storyboardAPI.deleteSession(sessionId)
      
      // 从列表中移除
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      
      // 如果是当前会话，清空当前会话
      if (currentSession.value?.id === sessionId) {
        currentSession.value = null
        cards.value = []
      }
    } catch (err) {
      error.value = '删除会话失败: ' + (err.message || '未知错误')
      throw err
    } finally {
      loading.value = false
    }
  }

  // 进度更新
  const updateProgress = (progress, step) => {
    analysisProgress.value = progress
    currentStep.value = step
    
    // 同时更新当前会话的进度
    if (currentSession.value) {
      currentSession.value.progress = progress
      currentSession.value.current_step = step
    }
  }

  const setAnalyzing = (analyzing) => {
    isAnalyzing.value = analyzing
  }

  // 重置状态
  const reset = () => {
    sessions.value = []
    currentSession.value = null
    cards.value = []
    analysisProgress.value = 0
    currentStep.value = ''
    isAnalyzing.value = false
    loading.value = false
    error.value = null
  }

  return {
    // 状态
    sessions,
    currentSession,
    cards,
    analysisProgress,
    currentStep,
    isAnalyzing,
    loading,
    error,
    
    // 计算属性
    sessionCount,
    completedSessions,
    pendingSessions,
    failedSessions,
    cardsByType,
    cardCounts,
    
    // 会话管理
    createAnalysisSession,
    startAnalysis,
    loadSessions,
    loadSessionDetail,
    setCurrentSession,
    
    // 卡片管理
    loadSessionCards,
    updateCard,
    confirmCard,
    reanalyzeCard,
    
    // 会话操作
    confirmSession,
    reanalyzeSession,
    deleteSession,
    
    // 进度管理
    updateProgress,
    setAnalyzing,
    
    // 工具方法
    reset
  }
})
