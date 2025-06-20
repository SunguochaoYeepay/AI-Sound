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
  getLogs(params = {}) {
    return apiClient.get('/logs/list', { params })
  },

  /**
   * 获取日志统计信息
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getStats(params = {}) {
    return apiClient.get('/logs/stats', { params })
  },

  /**
   * 获取最近日志
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getRecentLogs(params = {}) {
    return apiClient.get('/logs/recent', { params })
  },

  /**
   * 获取错误日志
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getErrorLogs(params = {}) {
    return apiClient.get('/logs/errors', { params })
  },

  /**
   * 清理旧日志
   * @param {Object} params - 清理参数
   * @returns {Promise}
   */
  clearLogs(params = {}) {
    return apiClient.post('/logs/clear', null, { params })
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
  getLevels() {
    return apiClient.get('/logs/levels')
  },

  /**
   * 获取可用的日志模块
   * @returns {Promise}
   */
  getModules() {
    return apiClient.get('/logs/modules')
  }
}