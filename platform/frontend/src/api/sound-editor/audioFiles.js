// 音频文件管理API - 适配AI-Sound后端
const API_BASE = '/api/v1/sound-editor/audio-files'

/**
 * 上传单个音频文件
 */
export async function uploadAudioFile(file, category = 'dialogue', projectId = null) {
  const formData = new FormData()
  formData.append('file', file)
  
  // 添加分类和项目ID参数
  const params = new URLSearchParams()
  params.append('category', category)
  if (projectId) {
    params.append('project_id', projectId)
  }
  
  try {
    const response = await fetch(`${API_BASE}/upload?${params}`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`上传失败: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('上传音频文件失败:', error)
    throw error
  }
}

/**
 * 批量上传音频文件
 */
export async function uploadMultipleAudioFiles(files, category = 'dialogue', projectId = null) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  
  // 添加分类和项目ID参数
  const params = new URLSearchParams()
  params.append('category', category)
  if (projectId) {
    params.append('project_id', projectId)
  }
  
  try {
    const response = await fetch(`${API_BASE}/upload/multiple?${params}`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`批量上传失败: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('批量上传音频文件失败:', error)
    throw error
  }
}

/**
 * 获取已上传的音频文件列表
 */
export async function listAudioFiles() {
  try {
    const response = await fetch(`${API_BASE}/list`)
    
    if (!response.ok) {
      throw new Error(`获取文件列表失败: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('获取音频文件列表失败:', error)
    throw error
  }
}

/**
 * 获取音频文件详细信息
 */
export async function getAudioFileInfo(fileId) {
  try {
    const response = await fetch(`${API_BASE}/info/${fileId}`)
    
    if (!response.ok) {
      throw new Error(`获取文件信息失败: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('获取音频文件信息失败:', error)
    throw error
  }
}

/**
 * 获取音频文件波形数据
 */
export async function getAudioWaveform(fileId, width = 800, height = 100) {
  try {
    const response = await fetch(`${API_BASE}/waveform/${fileId}?width=${width}&height=${height}`)
    
    if (!response.ok) {
      throw new Error(`获取波形数据失败: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('获取音频波形失败:', error)
    throw error
  }
}

/**
 * 转换音频文件格式
 */
export async function convertAudioFile(fileId, outputFormat = 'wav', sampleRate = 44100) {
  try {
    const response = await fetch(`${API_BASE}/convert/${fileId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        output_format: outputFormat,
        sample_rate: sampleRate
      })
    })
    
    if (!response.ok) {
      throw new Error(`转换文件失败: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('转换音频文件失败:', error)
    throw error
  }
}

/**
 * 删除音频文件
 */
export async function deleteAudioFile(fileId) {
  try {
    const response = await fetch(`${API_BASE}/${fileId}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error(`删除文件失败: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('删除音频文件失败:', error)
    throw error
  }
}

/**
 * 下载音频文件
 */
export async function downloadAudioFile(fileId) {
  try {
    const response = await fetch(`${API_BASE}/download/${fileId}`)
    
    if (!response.ok) {
      throw new Error(`下载文件失败: ${response.statusText}`)
    }
    
    // 创建下载链接
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audio_${fileId}`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    return { success: true, message: '下载成功' }
  } catch (error) {
    console.error('下载音频文件失败:', error)
    throw error
  }
}

/**
 * 裁剪音频文件
 */
export async function trimAudioFile(fileId, startTime, duration) {
  try {
    const response = await fetch(`${API_BASE}/trim/${fileId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        start_time: startTime,
        duration: duration
      })
    })
    
    if (!response.ok) {
      throw new Error(`裁剪文件失败: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('裁剪音频文件失败:', error)
    throw error
  }
}

/**
 * 检查音频服务健康状态
 */
export async function checkAudioServiceHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`)
    
    if (!response.ok) {
      throw new Error(`健康检查失败: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('音频服务健康检查失败:', error)
    throw error
  }
}

/**
 * 工具函数：格式化文件大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 工具函数：格式化音频时长
 */
export function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }
}

/**
 * 工具函数：验证音频文件类型
 */
export function isValidAudioFile(file) {
  const validTypes = [
    'audio/mp3', 'audio/mpeg',
    'audio/wav', 'audio/wave',
    'audio/flac',
    'audio/aac',
    'audio/ogg',
    'audio/m4a',
    'audio/x-ms-wma',
    'audio/opus',
    'audio/aiff'
  ]
  
  return validTypes.includes(file.type)
}