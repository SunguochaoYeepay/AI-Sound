import { useAudioPlayerStore } from '@/stores/audioPlayer'
import { message } from 'ant-design-vue'

/**
 * 统一的音频播放服务
 */
export class AudioService {
  constructor() {
    this._store = null
  }

  get store() {
    if (!this._store) {
      this._store = useAudioPlayerStore()
    }
    return this._store
  }

  /**
   * 播放章节音频
   * @param {number} projectId 项目ID
   * @param {number} chapterId 章节ID
   * @param {string} chapterTitle 章节标题
   */
  async playChapterAudio(projectId, chapterId, chapterTitle = `第${chapterId}章`) {
    const audioInfo = {
      id: `chapter_${projectId}_${chapterId}`,
      title: chapterTitle,
      url: `/api/v1/novel-reader/projects/${projectId}/chapters/${chapterId}/download`,
      type: 'chapter',
      metadata: {
        projectId,
        chapterId,
        onEnded: () => {
          console.log(`章节 ${chapterId} 播放完成`)
        }
      }
    }

    await this.store.playAudio(audioInfo)
  }

  // 🔧 移除项目播放功能 - 用户不需要项目播放按钮
  // 已移除 playProjectAudio 函数

  /**
   * 播放段落音频
   * @param {number} projectId 项目ID
   * @param {number} segmentId 段落ID
   * @param {string} segmentTitle 段落完整标题（包含章节信息）
   */
  async playSegmentAudio(projectId, segmentId, segmentTitle = `段落 ${segmentId}`) {
    const audioInfo = {
      id: `segment_${projectId}_${segmentId}`,
      title: segmentTitle, // 🎯 使用传入的完整标题
      url: `/api/v1/novel-reader/projects/${projectId}/segments/${segmentId}/download`,
      type: 'segment',
      metadata: {
        projectId,
        segmentId,
        text: segmentTitle,
        onEnded: () => {
          console.log(`段落播放完成: ${segmentTitle}`)
        }
      }
    }

    await this.store.playAudio(audioInfo)
  }

  /**
   * 播放音频库文件
   * @param {Object} audioFile 音频文件对象
   */
  async playLibraryAudio(audioFile) {
    const audioInfo = {
      id: `library_${audioFile.id}`,
      title: audioFile.originalName || audioFile.filename,
      url: `/api/v1/audio-library/files/${audioFile.id}/download`,
      type: 'library',
      metadata: {
        fileId: audioFile.id,
        duration: audioFile.duration,
        fileSize: audioFile.fileSize,
        projectName: audioFile.projectName,
        textContent: audioFile.textContent,
        onEnded: () => {
          console.log(`音频文件 ${audioFile.id} 播放完成`)
        }
      }
    }

    await this.store.playAudio(audioInfo)
  }

  /**
   * 播放声音配置试听
   * @param {number} voiceId 声音ID
   * @param {string} voiceName 声音名称
   * @param {string} sampleText 试听文本
   */
  async playVoicePreview(voiceId, voiceName, sampleText = '这是一段试听文本') {
    try {
      // 创建FormData对象，因为后端API期望Form数据
      const formData = new FormData()
      formData.append('voice_id', voiceId.toString())
      formData.append('text', sampleText)
      formData.append('time_step', '20')
      formData.append('p_weight', '1.0')
      formData.append('t_weight', '1.0')

      // 调用TTS API生成试听音频
      const response = await fetch('/api/v1/tts/preview', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('TTS API错误响应:', errorText)
        throw new Error('生成试听音频失败')
      }

      const result = await response.json()
      
      if (!result.success) {
        throw new Error(result.message || '生成试听音频失败')
      }

      // 确保audioUrl能正确通过代理访问
      // 后端返回的是 /audio/filename.wav，前端代理会将其重写为 /api/v1/audio/filename.wav
      let audioUrl = result.audioUrl
      if (audioUrl && audioUrl.startsWith('/audio/')) {
        // 保持原样，让vite代理处理重写
        audioUrl = result.audioUrl
      }

      // 使用返回的音频URL
      const audioInfo = {
        id: `voice_preview_${voiceId}_${Date.now()}`,
        title: `${voiceName} - 试听`,
        url: audioUrl,
        type: 'voice_preview',
        metadata: {
          voiceId,
          voiceName,
          sampleText,
          processingTime: result.processingTime,
          onEnded: () => {
            console.log(`声音 ${voiceName} 试听完成`)
          }
        }
      }

      await this.store.playAudio(audioInfo)
      message.success(`正在播放：${voiceName} 试听`)
    } catch (error) {
      console.error('播放声音试听失败:', error)
      message.error('播放声音试听失败: ' + error.message)
    }
  }

  /**
   * 播放自定义URL音频
   * @param {string} url 音频URL
   * @param {string} title 音频标题
   * @param {Object} metadata 额外元数据
   */
  async playCustomAudio(url, title = '音频', metadata = {}) {
    const audioInfo = {
      id: `custom_${Date.now()}`,
      title,
      url,
      type: 'custom',
      metadata: {
        ...metadata,
        onEnded: () => {
          console.log(`自定义音频 ${title} 播放完成`)
        }
      }
    }

    await this.store.playAudio(audioInfo)
  }

  /**
   * 播放环境音
   * @param {Object} sound 环境音对象
   */
  async playEnvironmentSound(sound) {
    try {
      if (!sound.file_path && sound.generation_status !== 'completed') {
        throw new Error('环境音尚未生成完成')
      }

      const audioInfo = {
        id: `env_sound_${sound.id}`,
        title: sound.name,
        url: `/api/v1/environment-sounds/${sound.id}/download`,
        type: 'environment',
        metadata: {
          soundId: sound.id,
          prompt: sound.prompt,
          description: sound.description,
          duration: sound.duration,
          category: sound.category?.name,
          tags: sound.tags?.map((tag) => tag.name).join(', '),
          onEnded: () => {
            console.log(`环境音 ${sound.name} 播放完成`)
          }
        }
      }

      await this.store.playAudio(audioInfo)
    } catch (error) {
      console.error('播放环境音失败:', error)
      throw error
    }
  }

  /**
   * 播放环境音项目轨道
   * @param {number} projectId 项目ID
   * @param {number} trackIndex 轨道索引
   * @param {string} trackTitle 轨道标题
   */
  async playEnvironmentTrack(projectId, trackIndex, trackTitle = `环境音轨道 ${trackIndex}`) {
    const audioInfo = {
      id: `env_track_${projectId}_${trackIndex}`,
      title: trackTitle,
      url: `/api/v1/environment-generation/preview/${projectId}/${trackIndex}`,
      type: 'environment_track',
      metadata: {
        projectId,
        trackIndex,
        onEnded: () => {
          console.log(`环境音轨道 ${trackIndex} 播放完成`)
        }
      }
    }

    await this.store.playAudio(audioInfo)
  }

  /**
   * 播放环境音项目混音结果
   * @param {number} projectId 项目ID
   * @param {string} projectTitle 项目标题
   */
  async playEnvironmentMixing(projectId, projectTitle = `环境音混音 ${projectId}`) {
    const audioInfo = {
      id: `env_mixing_${projectId}`,
      title: projectTitle,
      url: `/api/v1/environment-generation/mix-preview/${projectId}`,
      type: 'environment_mixing',
      metadata: {
        projectId,
        onEnded: () => {
          console.log(`环境音混音 ${projectId} 播放完成`)
        }
      }
    }

    await this.store.playAudio(audioInfo)
  }

  /**
   * 暂停当前播放
   */
  pause() {
    this.store.pause()
  }

  /**
   * 停止当前播放
   */
  stop() {
    this.store.stop()
  }

  /**
   * 设置音量
   * @param {number} volume 音量 (0-1)
   */
  setVolume(volume) {
    this.store.setVolume(volume)
  }

  /**
   * 设置播放速度
   * @param {number} rate 播放速度倍率
   */
  setPlaybackRate(rate) {
    this.store.setPlaybackRate(rate)
  }

  /**
   * 获取当前播放状态
   */
  getCurrentState() {
    return {
      currentAudio: this.store.currentAudio,
      isPlaying: this.store.isPlaying,
      currentTime: this.store.currentTime,
      duration: this.store.duration,
      progress: this.store.progress,
      volume: this.store.volume,
      playbackRate: this.store.playbackRate,
      loading: this.store.loading,
      error: this.store.error
    }
  }

  /**
   * 检查是否正在播放指定音频
   * @param {string} audioId 音频ID
   */
  isCurrentlyPlaying(audioId) {
    return this.store.isCurrentlyPlaying(audioId)
  }

  /**
   * 检查是否是当前音频
   * @param {string} audioId 音频ID
   */
  isCurrentAudio(audioId) {
    return this.store.isCurrentAudio(audioId)
  }

  /**
   * 清理资源
   */
  cleanup() {
    this.store.cleanup()
  }
}

// 延迟创建全局实例
let _audioService = null

export const getAudioService = () => {
  if (!_audioService) {
    _audioService = new AudioService()
  }
  return _audioService
}

// 便捷函数导出
export const playChapterAudio = (...args) => getAudioService().playChapterAudio(...args)
// 🔧 移除项目播放功能 - export const playProjectAudio = (...args) => getAudioService().playProjectAudio(...args)
export const playSegmentAudio = (...args) => getAudioService().playSegmentAudio(...args)
export const playLibraryAudio = (...args) => getAudioService().playLibraryAudio(...args)
export const playVoicePreview = (...args) => getAudioService().playVoicePreview(...args)
export const playCustomAudio = (...args) => getAudioService().playCustomAudio(...args)
export const playEnvironmentSound = (...args) => getAudioService().playEnvironmentSound(...args)
export const playEnvironmentTrack = (...args) => getAudioService().playEnvironmentTrack(...args)
export const playEnvironmentMixing = (...args) => getAudioService().playEnvironmentMixing(...args)
export const pauseAudio = () => getAudioService().pause()
export const stopAudio = () => getAudioService().stop()
export const setVolume = (...args) => getAudioService().setVolume(...args)
export const setPlaybackRate = (...args) => getAudioService().setPlaybackRate(...args)
export const getCurrentState = () => getAudioService().getCurrentState()
export const isCurrentlyPlaying = (...args) => getAudioService().isCurrentlyPlaying(...args)
export const isCurrentAudio = (...args) => getAudioService().isCurrentAudio(...args)
export const cleanupAudio = () => getAudioService().cleanup()

export default getAudioService
