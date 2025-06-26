/**
 * AI-Sound API客户端 v2
 * 对接新后端架构的API接口
 */

import apiClient from './config.js'
import { message } from 'ant-design-vue'

// API版本前缀 - 因为apiClient已经包含了/api/v1，这里留空
const API_V2_PREFIX = ''

/**
 * 通用API请求包装器
 */
const apiRequest = async (requestFn, showError = true) => {
  try {
    const response = await requestFn()
    return {
      success: true,
      data: response.data,
      status: response.status
    }
  } catch (error) {
    const errorMsg = error.response?.data?.message || error.message || '请求失败'
    
    if (showError) {
      message.error(errorMsg)
    }
    
    console.error('API请求失败:', error)
    
    return {
      success: false,
      error: errorMsg,
      status: error.response?.status || 0,
      details: error.response?.data
    }
  }
}

/**
 * 书籍管理API
 */
export const bookAPI = {
  // 获取书籍列表
  async getBooks(params = {}) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/books`, { params })
    )
  },
  
  // 获取书籍详情
  async getBook(bookId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/books/${bookId}`)
    )
  },
  
  // 创建书籍
  async createBook(bookData) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/books`, bookData)
    )
  },
  
  // 更新书籍
  async updateBook(bookId, bookData) {
    return apiRequest(() => 
      apiClient.put(`${API_V2_PREFIX}/books/${bookId}`, bookData)
    )
  },
  
  // 删除书籍
  async deleteBook(bookId) {
    return apiRequest(() => 
      apiClient.delete(`${API_V2_PREFIX}/books/${bookId}`)
    )
  },
  
  // 上传书籍文件
  async uploadBook(file, config = {}) {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/books/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: config.onProgress,
        ...config
      })
    )
  },
  
  // 检测章节结构
  async detectChapters(bookId, config = {}) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/books/${bookId}/detect-chapters`, config)
    )
  },
  
  // 获取书籍结构状态
  async getBookStructure(bookId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/books/${bookId}/structure`)
    )
  },
  
  // 获取书籍章节列表
  async getBookChapters(bookId, params = {}) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/books/${bookId}/chapters`, { params })
    )
  }
}

/**
 * 章节管理API
 */
export const chapterAPI = {
  // 获取章节列表
  async getChapters(bookId, params = {}) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/chapters`, { 
        params: { book_id: bookId, ...params } 
      })
    )
  },
  
  // 获取章节详情
  async getChapter(chapterId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/chapters/${chapterId}`)
    )
  },
  
  // 更新章节
  async updateChapter(chapterId, chapterData) {
    return apiRequest(() => 
      apiClient.put(`${API_V2_PREFIX}/chapters/${chapterId}`, chapterData)
    )
  },
  
  // 分割章节
  async splitChapter(chapterId, splitData) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/chapters/${chapterId}/split`, splitData)
    )
  },
  
  // 合并章节
  async mergeChapters(mergeData) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/chapters/merge`, mergeData)
    )
  }
}

/**
 * 智能分析API
 */
export const analysisAPI = {
  // 创建分析会话
  async createSession(sessionData) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/analysis/sessions`, sessionData)
    )
  },
  
  // 获取分析会话列表
  async getSessions(params = {}) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/analysis/sessions`, { params })
    )
  },
  
  // 获取分析会话详情
  async getSession(sessionId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/analysis/sessions/${sessionId}`)
    )
  },
  
  // 开始分析
  async startAnalysis(sessionId, forceRestart = false) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/analysis/sessions/${sessionId}/start`, {
        force_restart: forceRestart
      })
    )
  },
  
  // 停止分析
  async stopAnalysis(sessionId) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/analysis/sessions/${sessionId}/stop`)
    )
  },
  
  // 获取分析结果
  async getResults(sessionId, params = {}) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/analysis/sessions/${sessionId}/results`, { params })
    )
  },
  
  // 获取特定分析结果
  async getResult(resultId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/analysis/results/${resultId}`)
    )
  },
  
  // 更新分析结果配置
  async updateResultConfig(resultId, modifications) {
    return apiRequest(() => 
      apiClient.put(`${API_V2_PREFIX}/analysis/results/${resultId}/config`, {
        modifications
      })
    )
  },
  
  // 确认分析结果
  async confirmResult(resultId) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/analysis/results/${resultId}/confirm`)
    )
  }
}

/**
 * 音频合成API
 */
export const synthesisAPI = {
  // 创建合成任务
  async createTask(taskData) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/synthesis/tasks`, taskData)
    )
  },
  
  // 获取合成任务列表
  async getTasks(params = {}) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/synthesis/tasks`, { params })
    )
  },
  
  // 获取合成任务详情
  async getTask(taskId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/synthesis/tasks/${taskId}`)
    )
  },
  
  // 开始合成
  async startSynthesis(taskId) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/synthesis/tasks/${taskId}/start`)
    )
  },
  
  // 停止合成
  async stopSynthesis(taskId) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/synthesis/tasks/${taskId}/stop`)
    )
  },
  
  // 获取音频文件
  async getAudioFiles(taskId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/synthesis/tasks/${taskId}/audio-files`)
    )
  },
  
  // 下载音频文件
  async downloadAudio(taskId, fileId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/synthesis/tasks/${taskId}/audio-files/${fileId}/download`, {
        responseType: 'blob'
      })
    )
  }
}

/**
 * 预设配置API
 */
export const presetAPI = {
  // 获取预设列表
  async getPresets(params = {}) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/presets`, { params })
    )
  },
  
  // 获取预设详情
  async getPreset(presetId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/presets/${presetId}`)
    )
  },
  
  // 创建预设
  async createPreset(presetData) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/presets`, presetData)
    )
  },
  
  // 更新预设
  async updatePreset(presetId, presetData) {
    return apiRequest(() => 
      apiClient.put(`${API_V2_PREFIX}/presets/${presetId}`, presetData)
    )
  },
  
  // 删除预设
  async deletePreset(presetId) {
    return apiRequest(() => 
      apiClient.delete(`${API_V2_PREFIX}/presets/${presetId}`)
    )
  },
  
  // 验证预设
  async validatePreset(presetData) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/presets/validate`, presetData)
    )
  },
  
  // 导入预设
  async importPresets(presetsData) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/presets/import`, presetsData)
    )
  },
  
  // 导出预设
  async exportPresets(presetIds = []) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/presets/export`, { preset_ids: presetIds })
    )
  }
}

/**
 * 项目管理API
 */
export const projectAPI = {
  // 获取项目列表
  async getProjects(params = {}) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/projects`, { params })
    )
  },
  
  // 获取项目详情
  async getProject(projectId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/projects/${projectId}`)
    )
  },
  
  // 创建项目
  async createProject(projectData) {
    return apiRequest(() => 
      apiClient.post(`${API_V2_PREFIX}/projects`, projectData)
    )
  },
  
  // 更新项目
  async updateProject(projectId, projectData) {
    return apiRequest(() => 
      apiClient.put(`${API_V2_PREFIX}/projects/${projectId}`, projectData)
    )
  },
  
  // 删除项目
  async deleteProject(projectId) {
    return apiRequest(() => 
      apiClient.delete(`${API_V2_PREFIX}/projects/${projectId}`)
    )
  },
  
  // 获取项目统计
  async getProjectStats(projectId) {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/projects/${projectId}/stats`)
    )
  }
}

/**
 * 系统状态API
 */
export const systemAPI = {
  // 健康检查
  async healthCheck() {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/health`), false // 不显示错误消息
    )
  },
  
  // 获取系统状态
  async getSystemStatus() {
    return apiRequest(() => 
      apiClient.get(`${API_V2_PREFIX}/system/status`)
    )
  }
}

// 导出所有API
export default {
  book: bookAPI,
  chapter: chapterAPI,
  analysis: analysisAPI,
  synthesis: synthesisAPI,
  preset: presetAPI,
  project: projectAPI,
  system: systemAPI
} 