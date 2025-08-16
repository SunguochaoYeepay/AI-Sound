/**
 * 格式化工具函数库
 */

/**
 * 获取状态颜色
 * @param {string} status - 状态值
 * @returns {string} 颜色值
 */
export const getStatusColor = (status) => {
  const colors = {
    draft: 'orange',
    published: 'green',
    archived: 'gray',
    active: 'blue',
    inactive: 'red',
    pending: 'gold'
  }
  return colors[status] || 'default'
}

/**
 * 获取状态文本
 * @param {string} status - 状态值
 * @returns {string} 状态文本
 */
export const getStatusText = (status) => {
  const texts = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档',
    active: '活跃',
    inactive: '停用',
    pending: '待处理'
  }
  return texts[status] || status
}

/**
 * 格式化日期
 * @param {string|Date} dateStr - 日期字符串或Date对象
 * @param {string} format - 格式化类型 ('date' | 'datetime' | 'relative')
 * @returns {string} 格式化后的日期字符串
 */
export const formatDate = (dateStr, format = 'date') => {
  if (!dateStr) return '-'
  
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return '-'

  switch (format) {
    case 'datetime':
      return date.toLocaleString('zh-CN')
    case 'relative':
      return getRelativeTime(date)
    case 'date':
    default:
      return date.toLocaleDateString('zh-CN')
  }
}

/**
 * 获取相对时间
 * @param {Date} date - 日期对象
 * @returns {string} 相对时间字符串
 */
const getRelativeTime = (date) => {
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN')
}

/**
 * 格式化数字
 * @param {number} num - 数字
 * @param {string} unit - 单位
 * @returns {string} 格式化后的数字字符串
 */
export const formatNumber = (num, unit = '') => {
  if (num === null || num === undefined) return '0'
  return `${num.toLocaleString()}${unit}`
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 截断文本
 * @param {string} text - 原文本
 * @param {number} length - 最大长度
 * @param {string} suffix - 后缀
 * @returns {string} 截断后的文本
 */
export const truncateText = (text, length = 50, suffix = '...') => {
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + suffix
}

/**
 * 格式化时长（秒转时分秒）
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时长
 */
export const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return '0:00'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }
}

/**
 * 格式化音乐状态
 * @param {string} status - 状态值
 * @returns {string} 状态文本
 */
export const getMusicStatusText = (status) => {
  const statusMap = {
    completed: '已完成',
    processing: '处理中',
    failed: '失败'
  }
  return statusMap[status] || status
}

/**
 * 格式化音乐状态颜色
 * @param {string} status - 状态值
 * @returns {string} 颜色值
 */
export const getMusicStatusColor = (status) => {
  const colorMap = {
    completed: 'green',
    processing: 'blue',
    failed: 'red'
  }
  return colorMap[status] || 'default'
}
