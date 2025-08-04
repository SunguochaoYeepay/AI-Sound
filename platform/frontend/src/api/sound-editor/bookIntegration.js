import axios from 'axios'

// 获取章节相关的音频资源
export async function getChapterAudioResources(bookId, chapterId) {
  try {
    const response = await axios.get(`/api/v1/sound-editor/book/${bookId}/chapter/${chapterId}/resources`)
    return response.data
  } catch (error) {
    console.error('获取章节音频资源失败:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

// 获取书籍的合成计划
export async function getBookSynthesisPlan(bookId, chapterId) {
  try {
    const response = await axios.get(`/api/v1/books/${bookId}/synthesis-plan`, {
      params: { chapter_id: chapterId }
    })
    return response.data
  } catch (error) {
    console.error('获取书籍合成计划失败:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

// 获取章节的音频段落
export async function getChapterAudioSegments(projectId, chapterId) {
  try {
    const response = await axios.get(`/api/v1/novel-projects/${projectId}/chapters/${chapterId}/segments`)
    return response.data
  } catch (error) {
    console.error('获取章节音频段落失败:', error)
    return {
      success: false,
      error: error.message
    }
  }
}