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

  /**
   * 播放项目完整音频
   * @param {number} projectId 项目ID
   * @param {string} projectTitle 项目标题
   */
  async playProjectAudio(projectId, projectTitle = '完整音频') {
    const audioInfo = {
      id: `project_${projectId}`,
      title: projectTitle,
      url: `/api/v1/novel-reader/projects/${projectId}/download`,
      type: 'project',
      metadata: {
        projectId,
        onEnded: () => {
          console.log(`项目 ${projectId} 播放完成`)
        }
      }
    }

    await this.store.playAudio(audioInfo)
  }

  /**
   * 播放段落音频
   * @param {number} projectId 项目ID
   * @param {number} segmentId 段落ID
   * @param {string} segmentText 段落文本
   */
  async playSegmentAudio(projectId, segmentId, segmentText = `段落 ${segmentId}`) {
    const audioInfo = {
      id: `segment_${projectId}_${segmentId}`,
      title: `段落 ${segmentId}`,
      url: `/api/v1/novel-reader/projects/${projectId}/segments/${segmentId}/download`,
      type: 'segment',
      metadata: {
        projectId,
        segmentId,
        text: segmentText,
        onEnded: () => {
          console.log(`段落 ${segmentId} 播放完成`)
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
      // 调用TTS API生成试听音频
      const response = await fetch('/api/v1/tts/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          voice_id: voiceId,
          text: sampleText,
          format: 'wav'
        })
      })

      if (!response.ok) {
        throw new Error('生成试听音频失败')
      }

      const blob = await response.blob()
      const audioUrl = URL.createObjectURL(blob)

      const audioInfo = {
        id: `voice_preview_${voiceId}_${Date.now()}`,
        title: `${voiceName} - 试听`,
        url: audioUrl,
        type: 'voice_preview',
        metadata: {
          voiceId,
          voiceName,
          sampleText,
          onEnded: () => {
            // 清理blob URL
            URL.revokeObjectURL(audioUrl)
            console.log(`声音 ${voiceName} 试听完成`)
          }
        }
      }

      await this.store.playAudio(audioInfo)
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
          tags: sound.tags?.map(tag => tag.name).join(', '),
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
export const playProjectAudio = (...args) => getAudioService().playProjectAudio(...args)
export const playSegmentAudio = (...args) => getAudioService().playSegmentAudio(...args)
export const playLibraryAudio = (...args) => getAudioService().playLibraryAudio(...args)
export const playVoicePreview = (...args) => getAudioService().playVoicePreview(...args)
export const playCustomAudio = (...args) => getAudioService().playCustomAudio(...args)
export const playEnvironmentSound = (...args) => getAudioService().playEnvironmentSound(...args)
export const pauseAudio = () => getAudioService().pause()
export const stopAudio = () => getAudioService().stop()
export const setVolume = (...args) => getAudioService().setVolume(...args)
export const setPlaybackRate = (...args) => getAudioService().setPlaybackRate(...args)
export const getCurrentState = () => getAudioService().getCurrentState()
export const isCurrentlyPlaying = (...args) => getAudioService().isCurrentlyPlaying(...args)
export const isCurrentAudio = (...args) => getAudioService().isCurrentAudio(...args)
export const cleanupAudio = () => getAudioService().cleanup()

export default getAudioService 