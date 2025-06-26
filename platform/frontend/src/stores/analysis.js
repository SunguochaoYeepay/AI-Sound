/**
 * 智能分析状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { analysisAPI } from '../api/v2.js'

export const useAnalysisStore = defineStore('analysis', () => {
  // 分析会话
  const sessions = ref([])
  const currentSession = ref(null)
  const sessionsLoading = ref(false)
  
  // 分析结果
  const results = ref([])
  const resultsLoading = ref(false)
  
  // 进度跟踪
  const analysisProgress = ref({})
  
  // 计算属性
  const hasActiveSessions = computed(() => 
    sessions.value.some(s => s.status === 'running')
  )
  
  const sessionCount = computed(() => sessions.value.length)
  
  // 获取分析会话列表
  const fetchSessions = async (params = {}) => {
    sessionsLoading.value = true
    try {
      const result = await analysisAPI.getSessions(params)
      if (result.success) {
        sessions.value = result.data.items || result.data || []
      }
      return result
    } finally {
      sessionsLoading.value = false
    }
  }
  
  // 获取分析会话详情
  const fetchSession = async (sessionId) => {
    const result = await analysisAPI.getSession(sessionId)
    if (result.success) {
      currentSession.value = result.data
      
      // 更新本地会话列表中的对应项
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index > -1) {
        sessions.value[index] = result.data
      }
    }
    return result
  }
  
  // 获取分析结果
  const fetchResults = async (sessionId, params = {}) => {
    resultsLoading.value = true
    try {
      const result = await analysisAPI.getResults(sessionId, params)
      if (result.success) {
        results.value = result.data.items || result.data || []
      }
      return result
    } finally {
      resultsLoading.value = false
    }
  }
  
  // 创建分析会话
  const createSession = async (sessionData) => {
    const result = await analysisAPI.createSession(sessionData)
    if (result.success) {
      sessions.value.unshift(result.data)
      currentSession.value = result.data
    }
    return result
  }
  
  // 开始分析
  const startAnalysis = async (sessionId, forceRestart = false) => {
    const result = await analysisAPI.startAnalysis(sessionId, forceRestart)
    if (result.success) {
      // 更新会话状态
      updateSessionStatus(sessionId, 'running')
      
      // 初始化进度
      analysisProgress.value[sessionId] = {
        stage: 'initializing',
        progress: 0,
        message: '正在初始化分析...'
      }
    }
    return result
  }
  
  // 停止分析
  const stopAnalysis = async (sessionId) => {
    const result = await analysisAPI.stopAnalysis(sessionId)
    if (result.success) {
      updateSessionStatus(sessionId, 'stopped')
      delete analysisProgress.value[sessionId]
    }
    return result
  }
  
  // 更新会话状态
  const updateSessionStatus = (sessionId, status) => {
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      session.status = status
    }
    
    if (currentSession.value?.id === sessionId) {
      currentSession.value.status = status
    }
  }
  
  // 更新分析进度
  const updateProgress = (sessionId, progress) => {
    analysisProgress.value[sessionId] = {
      ...analysisProgress.value[sessionId],
      ...progress
    }
  }
  
  // 添加分析结果
  const addResult = (result) => {
    const existingIndex = results.value.findIndex(r => r.id === result.id)
    if (existingIndex > -1) {
      results.value[existingIndex] = result
    } else {
      results.value.unshift(result)
    }
  }
  
  // 确认分析结果
  const confirmResult = async (resultId) => {
    const result = await analysisAPI.confirmResult(resultId)
    if (result.success) {
      const resultIndex = results.value.findIndex(r => r.id === resultId)
      if (resultIndex > -1) {
        results.value[resultIndex].confirmed = true
      }
    }
    return result
  }
  
  return {
    // 状态
    sessions,
    currentSession,
    sessionsLoading,
    results,
    resultsLoading,
    analysisProgress,
    
    // 计算属性
    hasActiveSessions,
    sessionCount,
    
    // 方法
    fetchSessions,
    fetchSession,
    fetchResults,
    createSession,
    startAnalysis,
    stopAnalysis,
    updateSessionStatus,
    updateProgress,
    addResult,
    confirmResult
  }
}) 