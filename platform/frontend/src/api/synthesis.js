import apiClient from './config.js'

// 获取项目段落状态
export async function getSegmentsStatus(projectId, chapterId = null) {
  try {
    const params = chapterId ? { chapter_id: chapterId } : {}
    const response = await apiClient.get(`/novel-reader/projects/${projectId}/segments/status`, {
      params
    })

    if (response.data?.success) {
      return {
        success: true,
        data: response.data.data
      }
    } else {
      return {
        success: false,
        error: response.data?.message || '获取段落状态失败'
      }
    }
  } catch (error) {
    console.error('获取段落状态失败:', error)
    return {
      success: false,
      error: error.response?.data?.detail || error.message || '获取段落状态失败'
    }
  }
}

// 获取章节段落状态
export async function getChapterSegmentsStatus(projectId, chapterId) {
  try {
    const response = await apiClient.get(
      `/novel-reader/projects/${projectId}/chapters/${chapterId}/segments/status`
    )

    if (response.data?.success) {
      return {
        success: true,
        data: response.data.data
      }
    } else {
      return {
        success: false,
        error: response.data?.message || '获取章节段落状态失败'
      }
    }
  } catch (error) {
    console.error('获取章节段落状态失败:', error)
    return {
      success: false,
      error: error.response?.data?.detail || error.message || '获取章节段落状态失败'
    }
  }
}
