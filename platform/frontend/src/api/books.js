import request from '@/utils/request'

export default {
  // 获取书籍列表
  getBooks(params) {
    return request({
      url: '/api/v1/books',
      method: 'get',
      params
    })
  },

  // 获取单本书籍
  getBook(id) {
    return request({
      url: `/api/v1/books/${id}`,
      method: 'get'
    })
  },

  // 创建书籍
  createBook(data) {
    return request({
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
    return request({
      url: `/api/v1/books/${id}`,
      method: 'put',
      data
    })
  },

  // 删除书籍
  deleteBook(id) {
    return request({
      url: `/api/v1/books/${id}`,
      method: 'delete'
    })
  },

  // 检测章节
  detectChapters(id, params = {}) {
    return request({
      url: `/api/v1/books/${id}/detect-chapters`,
      method: 'post',
      data: params
    })
  },

  // 获取书籍章节
  getBookChapters(id, params = {}) {
    return request({
      url: `/api/v1/books/${id}/chapters`,
      method: 'get',
      params
    })
  }
} 