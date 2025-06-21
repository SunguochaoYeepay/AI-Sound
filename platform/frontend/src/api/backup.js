/**
 * 数据库备份恢复API接口
 */

import apiClient from './config'

// ======================== 备份管理接口 ========================

/**
 * 获取备份任务列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.status - 状态筛选
 * @param {string} params.backup_type - 类型筛选
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 * @returns {Promise} API响应
 */
export const getBackupList = async (params = {}) => {
  try {
    const response = await apiClient.get('/backup/list', { params })
    return response.data
  } catch (error) {
    console.error('获取备份列表失败:', error)
    throw error
  }
}

/**
 * 创建备份任务
 * @param {Object} backupData - 备份任务数据
 * @param {string} backupData.task_name - 任务名称
 * @param {string} backupData.backup_type - 备份类型: full, incremental, manual
 * @param {boolean} backupData.include_audio - 是否包含音频文件
 * @param {boolean} backupData.encryption_enabled - 是否启用加密
 * @param {string} backupData.storage_location - 存储位置: local, s3, oss
 * @param {number} backupData.retention_days - 保留天数
 * @returns {Promise} API响应
 */
export const createBackup = async (backupData) => {
  try {
    const response = await apiClient.post('/backup/create', backupData)
    return response.data
  } catch (error) {
    console.error('创建备份任务失败:', error)
    throw error
  }
}

/**
 * 获取备份任务状态
 * @param {number} taskId - 备份任务ID
 * @returns {Promise} API响应
 */
export const getBackupStatus = async (taskId) => {
  try {
    const response = await apiClient.get(`/backup/${taskId}/status`)
    return response.data
  } catch (error) {
    console.error('获取备份状态失败:', error)
    throw error
  }
}

/**
 * 删除备份任务
 * @param {number} taskId - 备份任务ID
 * @returns {Promise} API响应
 */
export const deleteBackup = async (taskId) => {
  try {
    const response = await apiClient.delete(`/backup/${taskId}`)
    return response.data
  } catch (error) {
    console.error('删除备份任务失败:', error)
    throw error
  }
}

// ======================== 恢复管理接口 ========================

/**
 * 创建恢复任务
 * @param {Object} restoreData - 恢复任务数据
 * @param {number} restoreData.backup_id - 备份任务ID
 * @param {string} restoreData.task_name - 恢复任务名称
 * @param {string} restoreData.restore_type - 恢复类型: full, partial, point_in_time
 * @param {string} restoreData.target_database - 目标数据库名
 * @param {boolean} restoreData.include_audio - 是否恢复音频文件
 * @param {string} restoreData.restore_point - 恢复到指定时间点
 * @returns {Promise} API响应
 */
export const createRestore = async (restoreData) => {
  try {
    const response = await apiClient.post('/backup/restore', restoreData)
    return response.data
  } catch (error) {
    console.error('创建恢复任务失败:', error)
    throw error
  }
}

/**
 * 获取恢复任务详情
 * @param {number} restoreId - 恢复任务ID
 * @returns {Promise} API响应
 */
export const getRestoreDetails = async (restoreId) => {
  try {
    const response = await apiClient.get(`/backup/restore/${restoreId}`)
    return response.data
  } catch (error) {
    console.error('获取恢复任务详情失败:', error)
    throw error
  }
}

/**
 * 取消恢复任务
 * @param {number} restoreId - 恢复任务ID
 * @returns {Promise} API响应
 */
export const cancelRestoreTask = async (restoreId) => {
  try {
    const response = await apiClient.post(`/backup/restore/${restoreId}/cancel`)
    return response.data
  } catch (error) {
    console.error('取消恢复任务失败:', error)
    throw error
  }
}

/**
 * 获取恢复任务列表
 * @param {Object} params - 查询参数
 * @returns {Promise} API响应
 */
export const getRestoreList = async (params = {}) => {
  try {
    const response = await apiClient.get('/backup/restore/list', { params })
    return response.data
  } catch (error) {
    console.error('获取恢复列表失败:', error)
    throw error
  }
}

/**
 * 获取恢复建议
 * @param {number} backupId - 备份任务ID
 * @returns {Promise} API响应
 */
export const getRestoreSuggestions = async (backupId) => {
  try {
    const response = await apiClient.get(`/backup/restore/suggestions/${backupId}`)
    return response.data
  } catch (error) {
    console.error('获取恢复建议失败:', error)
    throw error
  }
}

// ======================== 统计信息接口 ========================

/**
 * 获取备份统计信息
 * @param {number} days - 统计天数，默认30天
 * @returns {Promise} API响应
 */
export const getBackupStats = async (days = 30) => {
  try {
    const response = await apiClient.get('/backup/stats', {
      params: { days }
    })
    return response.data
  } catch (error) {
    console.error('获取备份统计失败:', error)
    throw error
  }
}

/**
 * 获取备份系统健康状态
 * @returns {Promise} API响应
 */
export const getBackupHealth = async () => {
  try {
    const response = await apiClient.get('/backup/health')
    return response.data
  } catch (error) {
    console.error('获取备份健康状态失败:', error)
    throw error
  }
}

// ======================== 配置管理接口 ========================

/**
 * 获取备份配置
 * @returns {Promise} API响应
 */
export const getBackupConfigs = async () => {
  try {
    const response = await apiClient.get('/backup/configs')
    return response.data
  } catch (error) {
    console.error('获取备份配置失败:', error)
    throw error
  }
}

/**
 * 更新备份配置
 * @param {Object} configs - 配置数据
 * @returns {Promise} API响应
 */
export const updateBackupConfigs = async (configs) => {
  try {
    const response = await apiClient.put('/backup/configs', { configs })
    return response.data
  } catch (error) {
    console.error('更新备份配置失败:', error)
    throw error
  }
}

// ======================== 调度管理接口 ========================

/**
 * 获取备份调度列表
 * @returns {Promise} API响应
 */
export const getBackupSchedules = async () => {
  try {
    const response = await apiClient.get('/backup/schedules')
    return response.data
  } catch (error) {
    console.error('获取备份调度失败:', error)
    throw error
  }
}

/**
 * 创建备份调度
 * @param {Object} scheduleData - 调度数据
 * @returns {Promise} API响应
 */
export const createBackupSchedule = async (scheduleData) => {
  try {
    const response = await apiClient.post('/backup/schedules', scheduleData)
    return response.data
  } catch (error) {
    console.error('创建备份调度失败:', error)
    throw error
  }
}

/**
 * 更新备份调度
 * @param {number} scheduleId - 调度ID
 * @param {Object} scheduleData - 调度数据
 * @returns {Promise} API响应
 */
export const updateBackupSchedule = async (scheduleId, scheduleData) => {
  try {
    const response = await apiClient.put(`/backup/schedules/${scheduleId}`, scheduleData)
    return response.data
  } catch (error) {
    console.error('更新备份调度失败:', error)
    throw error
  }
}

/**
 * 删除备份调度
 * @param {number} scheduleId - 调度ID
 * @returns {Promise} API响应
 */
export const deleteBackupSchedule = async (scheduleId) => {
  try {
    const response = await apiClient.delete(`/backup/schedules/${scheduleId}`)
    return response.data
  } catch (error) {
    console.error('删除备份调度失败:', error)
    throw error
  }
}

// ======================== 文件管理接口 ========================

/**
 * 获取备份任务详情
 * @param {number} taskId - 任务ID
 * @returns {Promise} API响应
 */
export const getBackupDetails = async (taskId) => {
  try {
    const response = await apiClient.get(`/backup/${taskId}/details`)
    return response.data
  } catch (error) {
    console.error('获取备份详情失败:', error)
    throw error
  }
}

/**
 * 下载备份文件
 * @param {number} taskId - 备份任务ID
 * @returns {Promise} 文件下载
 */
export const downloadBackupFile = async (taskId) => {
  try {
    const response = await apiClient.get(`/backup/${taskId}/download`, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition']
    let filename = `backup_${taskId}.sql.gz`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    return { success: true, filename }
  } catch (error) {
    console.error('下载备份文件失败:', error)
    throw error
  }
}

/**
 * 导出备份报告
 * @param {Object} params - 导出参数
 * @param {string} params.format - 导出格式: json, csv, xlsx
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 * @returns {Promise} 文件下载
 */
export const exportBackupReport = async (params) => {
  try {
    const response = await apiClient.get('/backup/export', {
      params,
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    const timestamp = new Date().toISOString().slice(0, 10)
    const filename = `backup_report_${timestamp}.${params.format}`
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    return { success: true, filename }
  } catch (error) {
    console.error('导出备份报告失败:', error)
    throw error
  }
}

// ======================== 实时监控接口 ========================

/**
 * 获取运行中的任务
 * @returns {Promise} API响应
 */
export const getRunningTasks = async () => {
  try {
    const response = await apiClient.get('/backup/running')
    return response.data
  } catch (error) {
    console.error('获取运行中任务失败:', error)
    throw error
  }
}

/**
 * 取消运行中的任务
 * @param {number} taskId - 任务ID
 * @returns {Promise} API响应
 */
export const cancelRunningTask = async (taskId) => {
  try {
    const response = await apiClient.post(`/backup/${taskId}/cancel`)
    return response.data
  } catch (error) {
    console.error('取消任务失败:', error)
    throw error
  }
}