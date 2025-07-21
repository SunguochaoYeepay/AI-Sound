import axios from 'axios'

// 音频编辑器与书籍集成API
const API_BASE = '/api/v1/sound-editor'

/**
 * 获取可用的书籍列表
 */
export async function getAvailableBooks() {
  const res = await axios.get(`${API_BASE}/books/list`)
  return res.data
}

/**
 * 获取书籍的章节列表
 * @param {number} bookId 书籍ID
 */
export async function getBookChapters(bookId, params = {}) {
  const defaultParams = {
    sort_by: 'chapter_number',
    sort_order: 'asc',
    ...params
  }
  const res = await axios.get(`${API_BASE}/books/${bookId}/chapters`, { params: defaultParams })
  return res.data
}

/**
 * 获取指定章节的所有资源
 * @param {number} bookId 书籍ID
 * @param {number[]} chapterIds 章节ID列表
 */
export async function getChapterResources(bookId, chapterIds) {
  const res = await axios.post(`${API_BASE}/books/${bookId}/chapters/resources`, {
    chapter_ids: chapterIds
  })
  return res.data
}

/**
 * 从书籍章节创建音频编辑器项目
 * @param {string} projectName 项目名称
 * @param {number} bookId 书籍ID
 * @param {number[]} chapterIds 章节ID列表
 * @param {Object} selectedResources 选中的资源 {dialogue_audio: [id1, id2], environment_configs: [id1]}
 */
export async function createProjectFromChapters(
  projectName,
  bookId,
  chapterIds,
  selectedResources
) {
  const res = await axios.post(`${API_BASE}/create-from-chapters`, {
    project_name: projectName,
    book_id: bookId,
    chapter_ids: chapterIds,
    selected_resources: selectedResources
  })
  return res.data
}
