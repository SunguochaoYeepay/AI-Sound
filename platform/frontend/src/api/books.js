import apiClient from '@/api/config'

export default {
  // 获取书籍列表
  getBooks(params) {
    return apiClient.get('/books', { params })
  },

  // 获取单本书籍
  getBook(id) {
    return apiClient.get(`/books/${id}`)
  },

  // 创建书籍
  createBook(data) {
    return apiClient.post('/books', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 更新书籍
  updateBook(id, data) {
    return apiClient.put(`/books/${id}`, data)
  },

  // 删除书籍
  deleteBook(id) {
    return apiClient.delete(`/books/${id}`)
  },

  // 检测章节
  detectChapters(id, params = {}) {
    return apiClient.post(`/books/${id}/detect-chapters`, params)
  },

  // 获取书籍章节
  getBookChapters(id, params = {}) {
    return apiClient.get(`/books/${id}/chapters`, { params })
  },

  // 搜索章节
  searchChapters(bookId, params = {}) {
    return apiClient.get(`/books/${bookId}/chapters/search`, { params })
  },

  // 获取章节内容
  getChapterContent(chapterId) {
    return apiClient.get(`/chapters/${chapterId}/content`)
  },

  // 批量获取章节准备状态
  getChaptersPreparationStatus(bookId, data) {
    return apiClient.post(`/books/${bookId}/chapters/batch-status`, data)
  },

  // 获取章节准备状态
  getPreparationStatus(chapterId) {
    return apiClient.get(`/chapters/${chapterId}/preparation-status`)
  },

  // 准备章节用于合成
  prepareChapterForSynthesis(chapterId, params = {}) {
    return apiClient.post(`/chapters/${chapterId}/prepare`, params)
  },

  // 更新章节分析结果
  updatePreparationResult(chapterId, data) {
    return apiClient.put(`/chapters/${chapterId}/analysis`, data)
  }
}
