import { request } from './index'

// ==================== 项目模板API ====================

/**
 * 获取项目模板列表
 */
export function getTemplates(params = {}) {
  return request({
    url: '/api/v1/collaboration/templates',
    method: 'get',
    params
  })
}

/**
 * 获取模板分类列表
 */
export function getTemplateCategories() {
  return request({
    url: '/api/v1/collaboration/templates/categories',
    method: 'get'
  })
}

/**
 * 创建项目模板
 */
export function createTemplate(data) {
  return request({
    url: '/api/v1/collaboration/templates',
    method: 'post',
    data
  })
}

/**
 * 使用模板
 */
export function useTemplate(templateId) {
  return request({
    url: `/api/v1/collaboration/templates/${templateId}/use`,
    method: 'post'
  })
}

// ==================== 版本控制API ====================

/**
 * 获取项目编辑历史
 */
export function getEditHistory(projectId, params = {}) {
  return request({
    url: `/api/v1/collaboration/projects/${projectId}/history`,
    method: 'get',
    params
  })
}

/**
 * 回滚到指定版本
 */
export function revertToVersion(projectId, versionNumber) {
  return request({
    url: `/api/v1/collaboration/projects/${projectId}/revert/${versionNumber}`,
    method: 'post'
  })
}

// ==================== 导出任务API ====================

/**
 * 创建导出任务
 */
export function createExportTask(data) {
  return request({
    url: '/api/v1/collaboration/export',
    method: 'post',
    data
  })
}

/**
 * 获取导出任务列表
 */
export function getExportTasks(params = {}) {
  return request({
    url: '/api/v1/collaboration/export/tasks',
    method: 'get',
    params
  })
}

/**
 * 获取导出任务详情
 */
export function getExportTask(taskId) {
  return request({
    url: `/api/v1/collaboration/export/tasks/${taskId}`,
    method: 'get'
  })
}

/**
 * 获取支持的导出格式
 */
export function getExportFormats() {
  return request({
    url: '/api/v1/collaboration/export/formats',
    method: 'get'
  })
}

/**
 * 批量导出项目
 */
export function batchExport(data) {
  return request({
    url: '/api/v1/collaboration/export/batch',
    method: 'post',
    data
  })
}

// ==================== 项目分享API ====================

/**
 * 创建项目分享
 */
export function createProjectShare(data) {
  return request({
    url: '/api/v1/collaboration/share',
    method: 'post',
    data
  })
}

/**
 * 获取项目分享信息
 */
export function getProjectShare(shareToken) {
  return request({
    url: `/api/v1/collaboration/share/${shareToken}`,
    method: 'get'
  })
}

/**
 * 更新项目分享设置
 */
export function updateProjectShare(shareId, data) {
  return request({
    url: `/api/v1/collaboration/share/${shareId}`,
    method: 'put',
    data
  })
}

// ==================== 云端同步API ====================

/**
 * 获取项目同步状态
 */
export function getSyncStatus(projectId) {
  return request({
    url: `/api/v1/collaboration/sync/${projectId}`,
    method: 'get'
  })
}

/**
 * 同步项目到云端
 */
export function syncToCloud(projectId) {
  return request({
    url: `/api/v1/collaboration/sync/${projectId}/upload`,
    method: 'post'
  })
}

/**
 * 从云端同步项目
 */
export function syncFromCloud(projectId) {
  return request({
    url: `/api/v1/collaboration/sync/${projectId}/download`,
    method: 'post'
  })
}

// ==================== 统计API ====================

/**
 * 获取模板使用统计
 */
export function getTemplateStats() {
  return request({
    url: '/api/v1/collaboration/stats/templates',
    method: 'get'
  })
}

/**
 * 获取导出统计
 */
export function getExportStats() {
  return request({
    url: '/api/v1/collaboration/stats/exports',
    method: 'get'
  })
}
