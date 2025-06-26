import { request } from './index'

/**
 * 智能编辑API
 */
export const smartEditingApi = {
  /**
   * 自动章节分割
   */
  analyzeChapters: (data) => {
    return request({
      url: '/api/v1/smart-editing/chapter-split',
      method: 'post',
      data
    })
  },

  /**
   * 语音识别
   */
  recognizeSpeech: (data) => {
    return request({
      url: '/api/v1/smart-editing/speech-recognition',
      method: 'post',
      data
    })
  },

  /**
   * 情感分析
   */
  analyzeEmotions: (data) => {
    return request({
      url: '/api/v1/smart-editing/emotion-analysis',
      method: 'post',
      data
    })
  },

  /**
   * 背景音乐推荐
   */
  recommendMusic: (data) => {
    return request({
      url: '/api/v1/smart-editing/music-recommendation',
      method: 'post',
      data
    })
  },

  /**
   * 批量处理
   */
  batchProcess: (data) => {
    return request({
      url: '/api/v1/smart-editing/batch-processing',
      method: 'post',
      data
    })
  },

  /**
   * 获取测试音频
   */
  getTestAudio: () => {
    return request({
      url: '/api/v1/smart-editing/test-audio',
      method: 'get'
    })
  },

  /**
   * 获取支持的语音识别语言
   */
  getSupportedLanguages: () => {
    return request({
      url: '/api/v1/smart-editing/supported-languages',
      method: 'get'
    })
  },

  /**
   * 获取支持的音乐风格
   */
  getMusicStyles: () => {
    return request({
      url: '/api/v1/smart-editing/music-styles',
      method: 'get'
    })
  }
} 