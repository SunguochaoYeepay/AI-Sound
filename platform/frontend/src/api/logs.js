/**
 * 日志监控API接口
 */

import apiClient from './config'

export const logApi = {
  /**
   * 获取日志列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getLogs(params = {}) {
    const response = await apiClient.get('/logs/list', { params })
    return response.data
  },

  /**
   * 获取日志统计信息
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getStats(params = {}) {
    const response = await apiClient.get('/logs/stats', { params })
    return response.data
  },

  /**
   * 获取最近日志
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getRecentLogs(params = {}) {
    const response = await apiClient.get('/logs/recent', { params })
    return response.data
  },

  /**
   * 获取错误日志
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getErrorLogs(params = {}) {
    const response = await apiClient.get('/logs/errors', { params })
    return response.data
  },

  /**
   * 清理旧日志
   * @param {Object} params - 清理参数
   * @returns {Promise}
   */
  async clearLogs(params = {}) {
    const response = await apiClient.post('/logs/clear', null, { params })
    return response.data
  },

  /**
   * 导出日志
   * @param {Object} params - 导出参数
   * @returns {Promise}
   */
  async exportLogs(params = {}) {
    const response = await apiClient.get('/logs/export', { 
      params,
      responseType: 'blob'
    })
    
    // 处理文件下载
    const blob = new Blob([response], { 
      type: params.format === 'csv' ? 'text/csv' : 'application/json' 
    })
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${params.format || 'json'}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    return response
  },

  /**
   * 获取可用的日志级别
   * @returns {Promise}
   */
  async getLevels() {
    const response = await apiClient.get('/logs/levels')
    return response.data
  },

  /**
   * 获取可用的日志模块
   * @returns {Promise}
   */
  async getModules() {
    const response = await apiClient.get('/logs/modules')
    return response.data
  }
}