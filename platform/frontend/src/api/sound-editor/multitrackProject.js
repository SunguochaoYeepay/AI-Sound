import axios from 'axios'

// 适配AI-Sound后端API
const API_BASE = '/api/v1/sound-editor/multitrack'

// 项目管理接口
export async function createProject(projectData) {
  const res = await axios.post(`${API_BASE}/create`, projectData)
  return res.data
}

export async function loadProject(projectId) {
  const res = await axios.get(`${API_BASE}/load/${projectId}`)
  return res.data
}

export async function saveProject(projectId, projectData) {
  const res = await axios.put(`${API_BASE}/save/${projectId}`, { project: projectData })
  return res.data
}

export async function listProjects() {
  const res = await axios.get(`${API_BASE}/list`)
  return res.data
}

export async function deleteProject(projectId) {
  const res = await axios.delete(`${API_BASE}/delete/${projectId}`)
  return res.data
}

// 格式转换接口
export async function convertToStandardFormat(conversionData) {
  const res = await axios.post(`${API_BASE}/convert`, conversionData)
  return res.data
}

// 项目验证接口
export async function validateProject(projectId) {
  const res = await axios.get(`${API_BASE}/validate/${projectId}`)
  return res.data
}

// 导出相关接口
export async function exportProject(projectId) {
  const res = await axios.post(`${API_BASE}/export/${projectId}`)
  return res.data
}

export async function getExportStatus(exportTaskId) {
  const res = await axios.get(`${API_BASE}/export/status/${exportTaskId}`)
  return res.data
}

export async function downloadExportedAudio(exportTaskId) {
  const response = await axios.get(`${API_BASE}/export/download/${exportTaskId}`, {
    responseType: 'blob'
  })
  
  // 创建下载链接
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `multitrack_export_${exportTaskId}.wav`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

// 预览播放相关接口
export async function generatePreviewAudio(projectId, startTime = 0, duration = null) {
  const params = { start_time: startTime }
  if (duration !== null) {
    params.duration = duration
  }
  
  const res = await axios.post(`${API_BASE}/preview/${projectId}`, null, { params })
  return res.data
}

export function getPreviewAudioUrl(fileId) {
  const url = `${API_BASE}/preview/download/${fileId}`
  console.log('构建预览音频URL:', url)
  return url
}

export async function deletePreviewFile(filename) {
  const res = await axios.delete(`/api/v1/sound-editor/preview/${filename}`)
  return res.data
}

// 工具函数：创建空项目模板
export function createEmptyProject(title = '新建项目') {
  return {
    project: {
      id: '',
      title,
      description: '',
      author: 'AI-Sound',
      totalDuration: 60, // 最小时长，会根据内容自动扩展
      sampleRate: 44100,
      channels: 2,
      bitDepth: 16,
      exportFormat: 'wav',
      createdAt: null,
      version: '1.0'
    },
    tracks: [
      {
        id: 'track_dialogue',
        name: '角色对话',
        type: 'dialogue',
        volume: 1.0,
        muted: false,
        solo: false,
        color: '#3498db',
        order: 1,
        clips: []
      },
      {
        id: 'track_environment',
        name: '环境音效',
        type: 'environment',
        volume: 0.8,
        muted: false,
        solo: false,
        color: '#27ae60',
        order: 2,
        clips: []
      },
      {
        id: 'track_background',
        name: '背景音乐',
        type: 'background',
        volume: 0.5,
        muted: false,
        solo: false,
        color: '#e74c3c',
        order: 3,
        clips: []
      }
    ],
    markers: []
  }
}

// 工具函数：计算项目总时长
export function calculateProjectDuration(project) {
  let maxDuration = 0
  
  project.tracks.forEach(track => {
    track.clips.forEach(clip => {
      const endTime = clip.startTime + clip.duration
      maxDuration = Math.max(maxDuration, endTime)
    })
  })
  
  return maxDuration
}

// 工具函数：时间格式化
export function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

// 工具函数：生成唯一ID
export function generateId(prefix = 'item') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
} 