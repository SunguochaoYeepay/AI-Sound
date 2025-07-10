import apiClient from './config'

export default {
  // 获取章节列表
  getChapters(params) {
    return apiClient({
      url: '/api/v1/chapters',
      method: 'get',
      params
    })
  },

  // 创建单个章节
  createChapter(data) {
    const formData = new FormData()
    for (const key in data) {
      formData.append(key, data[key])
    }
    return apiClient({
      url: '/api/v1/chapters',
      method: 'post',
      data: formData
    })
  },

  // 批量创建章节
  createChaptersBatch(data) {
    const formData = new FormData()
    formData.append('book_id', data.book_id)
    if (data.start_chapter_number) {
      formData.append('start_chapter_number', data.start_chapter_number)
    }
    if (data.batch_size) {
      formData.append('batch_size', data.batch_size)
    }
    
    return apiClient({
      url: '/api/v1/chapters/batch',
      method: 'post',
      data: {
        ...Object.fromEntries(formData),
        chapters: data.chapters
      },
      headers: {
        'Content-Type': 'application/json'
      }
    })
  },

  // 更新章节
  updateChapter(chapterId, data) {
    const formData = new FormData()
    for (const key in data) {
      formData.append(key, data[key])
    }
    return apiClient({
      url: `/api/v1/chapters/${chapterId}`,
      method: 'patch',
      data: formData
    })
  },

  // 删除章节
  deleteChapter(chapterId, force = false) {
    return apiClient({
      url: `/api/v1/chapters/${chapterId}`,
      method: 'delete',
      params: { force }
    })
  },

  // 获取章节分析结果
  getChapterAnalysisResult(chapterId) {
    return apiClient({
      url: `/content-preparation/result/${chapterId}`,
      method: 'get'
    }).then(response => {
      if (response.data) {
        return {
          success: true,
          data: response.data,
          message: response.data.message || '获取分析结果成功'
        }
      }
      return {
        success: false,
        data: null,
        message: '获取分析结果失败'
      }
    }).catch(error => {
      console.error('获取分析结果失败:', error)
      return {
        success: false,
        data: null,
        message: error.response?.data?.message || '获取分析结果失败'
      }
    })
  }
} 