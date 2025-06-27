/**
 * 资源管理器 - 用于管理音频、语音等资源
 */
class ResourceManager {
  constructor() {
    this.resources = {
      voice: [],      // 声音资源
      audio: [],      // 音频资源
      music: [],      // 音乐资源
      sound: []       // 音效资源
    }
    this.loaded = false
  }

  /**
   * 加载所有资源
   */
  async loadAllResources() {
    try {
      // 模拟加载资源数据
      // 在实际项目中，这里应该调用API获取资源列表
      await this.loadVoiceResources()
      await this.loadAudioResources()
      await this.loadMusicResources()
      await this.loadSoundResources()
      
      this.loaded = true
    } catch (error) {
      console.error('加载资源失败:', error)
      throw error
    }
  }

  /**
   * 加载声音资源
   */
  async loadVoiceResources() {
    // 模拟声音资源数据
    this.resources.voice = [
      {
        id: 'voice_1',
        name: '男声-成熟',
        type: 'voice',
        duration: 0,
        size: 0,
        url: '/api/v1/voices/preview/1',
        tags: ['男声', '成熟', '磁性'],
        description: '成熟男性声音，适合商务场景'
      },
      {
        id: 'voice_2', 
        name: '女声-温柔',
        type: 'voice',
        duration: 0,
        size: 0,
        url: '/api/v1/voices/preview/2',
        tags: ['女声', '温柔', '甜美'],
        description: '温柔女性声音，适合故事朗读'
      }
    ]
  }

  /**
   * 加载音频资源
   */
  async loadAudioResources() {
    // 模拟音频资源数据
    this.resources.audio = [
      {
        id: 'audio_1',
        name: '示例音频1.mp3',
        type: 'audio',
        duration: 120,
        size: 5242880, // 5MB
        url: '/api/v1/audio/1',
        tags: ['音乐', '背景'],
        description: '示例音频文件'
      }
    ]
  }

  /**
   * 加载音乐资源
   */
  async loadMusicResources() {
    // 模拟音乐资源数据
    this.resources.music = [
      {
        id: 'music_1',
        name: '轻音乐-春天',
        type: 'music',
        duration: 180,
        size: 7340032, // 7MB
        url: '/api/v1/music/1',
        tags: ['轻音乐', '春天', '清新'],
        description: '清新的春天主题轻音乐'
      }
    ]
  }

  /**
   * 加载音效资源
   */
  async loadSoundResources() {
    // 模拟音效资源数据
    this.resources.sound = [
      {
        id: 'sound_1',
        name: '鸟叫声',
        type: 'sound',
        duration: 5,
        size: 204800, // 200KB
        url: '/api/v1/sounds/1',
        tags: ['自然', '鸟类', '环境'],
        description: '清晨鸟叫声音效'
      }
    ]
  }

  /**
   * 根据分类获取资源
   */
  getResourcesByCategory(category) {
    return this.resources[category] || []
  }

  /**
   * 搜索资源
   */
  searchResources(query, category = null) {
    const searchQuery = query.toLowerCase()
    let resources = []

    if (category) {
      resources = this.resources[category] || []
    } else {
      // 搜索所有分类
      resources = Object.values(this.resources).flat()
    }

    return resources.filter(resource => {
      return resource.name.toLowerCase().includes(searchQuery) ||
             resource.description.toLowerCase().includes(searchQuery) ||
             resource.tags.some(tag => tag.toLowerCase().includes(searchQuery))
    })
  }

  /**
   * 根据ID获取资源
   */
  getResourceById(id) {
    const allResources = Object.values(this.resources).flat()
    return allResources.find(resource => resource.id === id)
  }

  /**
   * 添加资源
   */
  addResource(resource, category) {
    if (!this.resources[category]) {
      this.resources[category] = []
    }
    this.resources[category].push(resource)
  }

  /**
   * 删除资源
   */
  removeResource(id, category) {
    if (this.resources[category]) {
      this.resources[category] = this.resources[category].filter(
        resource => resource.id !== id
      )
    }
  }

  /**
   * 格式化持续时间
   */
  formatDuration(seconds) {
    if (!seconds || seconds === 0) return '--'
    
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    
    if (minutes === 0) {
      return `${remainingSeconds}秒`
    }
    
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '--'
    
    const units = ['B', 'KB', 'MB', 'GB']
    let size = bytes
    let unitIndex = 0
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`
  }

  /**
   * 验证资源文件格式
   */
  validateFileFormat(file, allowedFormats) {
    const fileExtension = file.name.split('.').pop().toLowerCase()
    return allowedFormats.includes(fileExtension)
  }

  /**
   * 获取支持的音频格式
   */
  getSupportedAudioFormats() {
    return ['mp3', 'wav', 'ogg', 'aac', 'm4a', 'flac']
  }

  /**
   * 检查资源是否已加载
   */
  isLoaded() {
    return this.loaded
  }

  /**
   * 清空资源缓存
   */
  clearCache() {
    this.resources = {
      voice: [],
      audio: [],
      music: [],
      sound: []
    }
    this.loaded = false
  }
}

export default ResourceManager