import apiClient from './config.js'

/**
 * 项目管理API
 * 提供项目创建、查询、更新、删除功能
 */
export const projectsAPI = {
  /**
   * 获取项目列表
   * @param {Object} params - 查询参数
   * @returns {Promise} 项目列表
   */
  getProjects: (params = {}) => {
    return apiClient.get('/projects', { params })
  },

  /**
   * 获取项目详情
   * @param {number} projectId - 项目ID
   * @returns {Promise} 项目详情
   */
  getProject: (projectId) => {
    return apiClient.get(`/projects/${projectId}`)
  },

  /**
   * 创建新项目
   * @param {Object} projectData - 项目数据
   * @returns {Promise} 创建结果
   */
  createProject: (projectData) => {
    const formData = new FormData()
    formData.append('name', projectData.name)
    formData.append('description', projectData.description || '')
    formData.append('content', projectData.content || '')
    formData.append('book_id', projectData.book_id || '')
    formData.append('initial_characters', projectData.initial_characters || '[]')
    formData.append('settings', projectData.settings || '{}')
    formData.append('status', projectData.status || 'pending')
    
    return apiClient.post('/projects', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 更新项目
   * @param {number} projectId - 项目ID
   * @param {Object} projectData - 项目数据
   * @returns {Promise} 更新结果
   */
  updateProject: (projectId, projectData) => {
    return apiClient.put(`/projects/${projectId}`, projectData)
  },

  /**
   * 删除项目
   * @param {number} projectId - 项目ID
   * @returns {Promise} 删除结果
   */
  deleteProject: (projectId) => {
    return apiClient.delete(`/projects/${projectId}`)
  },

  /**
   * 获取项目统计信息
   * @returns {Promise} 统计信息
   */
  getProjectStats: () => {
    return apiClient.get('/projects/stats')
  }
}

export default projectsAPI
