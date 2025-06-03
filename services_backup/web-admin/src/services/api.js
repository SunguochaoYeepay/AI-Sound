/**
 * API服务模块
 * 统一管理所有API调用，适配新的后端接口
 */

import axios from '../plugins/axios'

// 基础API类
class BaseAPI {
  constructor(baseUrl) {
    this.baseUrl = baseUrl
  }

  // 处理API响应
  handleResponse(response) {
    return response.data
  }

  // 处理API错误
  handleError(error) {
    console.error('API Error:', error)
    throw error
  }
}

// 引擎管理API
class EngineAPI extends BaseAPI {
  constructor() {
    super('/api/tts')
  }

  // 获取所有引擎
  async getEngines() {
    try {
      const response = await axios.get(`${this.baseUrl}/engines`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取单个引擎
  async getEngine(engineId) {
    try {
      const response = await axios.get(`${this.baseUrl}/${engineId}`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 创建引擎
  async createEngine(engineData) {
    try {
      const response = await axios.post(this.baseUrl, engineData)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 更新引擎
  async updateEngine(engineId, engineData) {
    try {
      const response = await axios.put(`${this.baseUrl}/${engineId}`, engineData)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 删除引擎
  async deleteEngine(engineId) {
    try {
      const response = await axios.delete(`${this.baseUrl}/${engineId}`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 健康检查
  async checkHealth(engineId) {
    try {
      const response = await axios.get(`${this.baseUrl}/${engineId}/health`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取引擎配置
  async getConfig(engineId) {
    try {
      const response = await axios.get(`${this.baseUrl}/${engineId}/config`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 更新引擎配置
  async updateConfig(engineId, config) {
    try {
      const response = await axios.put(`${this.baseUrl}/${engineId}/config`, { config })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 重启引擎
  async restartEngine(engineId) {
    try {
      const response = await axios.post(`${this.baseUrl}/${engineId}/restart`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }
}

// 声音管理API
class VoiceAPI extends BaseAPI {
  constructor() {
    super('/api/voices')
  }

  // 获取所有声音
  async getVoices(params = {}) {
    try {
      const response = await axios.get(this.baseUrl, { params })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取单个声音
  async getVoice(voiceId) {
    try {
      const response = await axios.get(`${this.baseUrl}/${voiceId}`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 创建声音
  async createVoice(voiceData) {
    try {
      const response = await axios.post(this.baseUrl, voiceData)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 更新声音
  async updateVoice(voiceId, voiceData) {
    try {
      const response = await axios.put(`${this.baseUrl}/${voiceId}`, voiceData)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 删除声音
  async deleteVoice(voiceId) {
    try {
      const response = await axios.delete(`${this.baseUrl}/${voiceId}`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 上传声音文件
  async uploadVoice(formData, options = {}) {
    try {
      const response = await axios.post(`${this.baseUrl}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        ...options
      })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // MegaTTS3专用：上传参考音频和特征文件
  async uploadMegaTTS3Voice(voiceId, audioFile, npyFile = null) {
    try {
      const formData = new FormData()
      formData.append('audio', audioFile)
      if (npyFile) {
        formData.append('npy', npyFile)
      }
      
      const response = await axios.post(`/api/engines/megatts3/voices/${voiceId}/upload-reference`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 提取音频特征（自动生成.npy文件）
  async extractFeatures(audioFile, engine = 'megatts3') {
    try {
      const formData = new FormData()
      formData.append('audio', audioFile)
      formData.append('engine', engine)
      
      const response = await axios.post(`${this.baseUrl}/extract-features`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 预览声音
  async previewVoice(voiceId, text) {
    try {
      const response = await axios.post(`${this.baseUrl}/${voiceId}/preview`, { text })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 分析声音特征
  async analyzeVoice(voiceId) {
    try {
      const response = await axios.post(`${this.baseUrl}/${voiceId}/analyze`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }
}

// 角色管理API
class CharacterAPI extends BaseAPI {
  constructor() {
    super('/api/characters')
  }

  // 获取所有角色
  async getCharacters(params = {}) {
    try {
      const response = await axios.get(this.baseUrl, { params })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取单个角色
  async getCharacter(characterId) {
    try {
      const response = await axios.get(`${this.baseUrl}/${characterId}`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 创建角色
  async createCharacter(characterData) {
    try {
      const response = await axios.post(this.baseUrl, characterData)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 更新角色
  async updateCharacter(characterId, characterData) {
    try {
      const response = await axios.put(`${this.baseUrl}/${characterId}`, characterData)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 删除角色
  async deleteCharacter(characterId) {
    try {
      const response = await axios.delete(`${this.baseUrl}/${characterId}`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 设置角色声音映射
  async setVoiceMapping(characterId, voiceId) {
    try {
      const response = await axios.post(`${this.baseUrl}/${characterId}/voice-mapping`, {
        voice_id: voiceId
      })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 批量操作
  async batchOperation(operation, characterIds, data = {}) {
    try {
      const response = await axios.post(`${this.baseUrl}/batch`, {
        operation,
        character_ids: characterIds,
        ...data
      })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }
}

// TTS合成API
class TTSAPI extends BaseAPI {
  constructor() {
    super('/api/tts')
  }

  // 文本转语音
  async synthesize(data) {
    try {
      const response = await axios.post(`${this.baseUrl}/synthesize`, data)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 批量合成
  async batchSynthesize(data) {
    try {
      const response = await axios.post(`${this.baseUrl}/batch-synthesize`, data)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取任务状态
  async getTaskStatus(taskId) {
    try {
      const response = await axios.get(`${this.baseUrl}/tasks/${taskId}`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取任务列表
  async getTasks(params = {}) {
    try {
      const response = await axios.get(`${this.baseUrl}/tasks`, { params })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 取消任务
  async cancelTask(taskId) {
    try {
      const response = await axios.post(`${this.baseUrl}/tasks/${taskId}/cancel`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取支持的格式
  async getSupportedFormats() {
    try {
      const response = await axios.get(`${this.baseUrl}/formats`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }
}

// 系统API
class SystemAPI extends BaseAPI {
  constructor() {
    super('/api')
  }

  // 健康检查
  async healthCheck() {
    try {
      const response = await axios.get(`${this.baseUrl}/health`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取系统信息
  async getSystemInfo() {
    try {
      const response = await axios.get(`${this.baseUrl}/system/info`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取系统统计
  async getSystemStats() {
    try {
      const response = await axios.get(`${this.baseUrl}/system/stats`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取日志
  async getLogs(params = {}) {
    try {
      const response = await axios.get(`${this.baseUrl}/system/logs`, { params })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 获取系统设置
  async getSettings() {
    try {
      const response = await axios.get(`${this.baseUrl}/system/settings`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 更新系统设置
  async updateSettings(data) {
    try {
      const response = await axios.put(`${this.baseUrl}/system/settings`, data)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 导出设置
  async exportSettings() {
    try {
      const response = await axios.get(`${this.baseUrl}/system/settings/export`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 导入设置
  async importSettings(data) {
    try {
      const response = await axios.post(`${this.baseUrl}/system/settings/import`, data)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // 下载日志
  async downloadLogs() {
    try {
      const response = await axios.get(`${this.baseUrl}/system/logs/download`, {
        responseType: 'blob'
      })
      return response
    } catch (error) {
      this.handleError(error)
    }
  }

  // 清空日志
  async clearLogs() {
    try {
      const response = await axios.delete(`${this.baseUrl}/system/logs`)
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }
}

// 创建API实例
export const engineAPI = new EngineAPI()
export const voiceAPI = new VoiceAPI()
export const characterAPI = new CharacterAPI()
export const ttsAPI = new TTSAPI()
export const systemAPI = new SystemAPI()

// 默认导出所有API
export default {
  engine: engineAPI,
  voice: voiceAPI,
  character: characterAPI,
  tts: ttsAPI,
  system: systemAPI
}