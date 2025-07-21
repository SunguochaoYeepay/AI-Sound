import apiClient from '@/api/config'

export default {
  // 获取书籍列表
  getBooks(params) {
    return apiClient({
      url: '/api/v1/books',
      method: 'get',
      params
    })
  },

  // 获取单本书籍
  getBook(id) {
    return apiClient({
      url: `/api/v1/books/${id}`,
      method: 'get'
    })
  },

  // 创建书籍
  createBook(data) {
    return apiClient({
      url: '/api/v1/books',
      method: 'post',
      data,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 更新书籍
  updateBook(id, data) {
    return apiClient({
      url: `/api/v1/books/${id}`,
      method: 'put',
      data
    })
  },

  // 删除书籍
  deleteBook(id) {
    return apiClient({
      url: `/api/v1/books/${id}`,
      method: 'delete'
    })
  },

  // 检测章节
  detectChapters(id, params = {}) {
    return apiClient({
      url: `/api/v1/books/${id}/detect-chapters`,
      method: 'post',
      data: params
    })
  },

  // 获取书籍章节
  getBookChapters(id, params = {}) {
    return apiClient({
      url: `/api/v1/books/${id}/chapters`,
      method: 'get',
      params
    })
  },

  // 搜索章节
  searchChapters(bookId, params = {}) {
    return apiClient({
      url: `/api/v1/books/${bookId}/chapters/search`,
      method: 'get',
      params
    })
  },

  // 获取章节内容
  getChapterContent(chapterId) {
    return apiClient({
      url: `/api/v1/chapters/${chapterId}/content`,
      method: 'get'
    })
  },

  // 批量获取章节准备状态
  getChaptersPreparationStatus(bookId, data) {
    return apiClient({
      url: `/api/v1/books/${bookId}/chapters/batch-status`,
      method: 'post',
      data
    })
  },

  // 获取章节准备状态
  getPreparationStatus(chapterId) {
    return apiClient({
      url: `/api/v1/chapters/${chapterId}/preparation-status`,
      method: 'get'
    })
  },

  // 准备章节用于合成
  prepareChapterForSynthesis(chapterId, params = {}) {
    return apiClient({
      url: `/api/v1/chapters/${chapterId}/prepare`,
      method: 'post',
      data: params
    })
  },

  // 更新章节分析结果
  updatePreparationResult(chapterId, data) {
    return apiClient({
      url: `/api/v1/chapters/${chapterId}/analysis`,
      method: 'put',
      data
    })
  }
}
