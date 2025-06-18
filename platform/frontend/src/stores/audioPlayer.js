import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'

export const useAudioPlayerStore = defineStore('audioPlayer', () => {
  // 状态
  const currentAudio = ref(null) // 当前播放的音频信息
  const audioElement = ref(null) // 音频DOM元素引用
  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const volume = ref(0.8)
  const playbackRate = ref(1.0)
  const loading = ref(false)
  const error = ref(null)

  // 计算属性
  const progress = computed(() => {
    if (duration.value === 0) return 0
    return (currentTime.value / duration.value) * 100
  })

  const formattedCurrentTime = computed(() => formatTime(currentTime.value))
  const formattedDuration = computed(() => formatTime(duration.value))

  // 工具函数
  const formatTime = (seconds) => {
    if (isNaN(seconds) || seconds === 0) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // 播放音频
  const playAudio = async (audioInfo) => {
    try {
      // 如果是同一个音频，切换播放/暂停
      if (currentAudio.value?.id === audioInfo.id) {
        if (isPlaying.value) {
          pause()
        } else {
          resume()
        }
        return
      }

      // 停止当前播放
      stop()

      // 设置新音频
      currentAudio.value = {
        id: audioInfo.id,
        title: audioInfo.title || audioInfo.name || '未知音频',
        url: audioInfo.url || audioInfo.audioUrl,
        type: audioInfo.type || 'unknown',
        metadata: audioInfo.metadata || {}
      }

      loading.value = true
      error.value = null

      // 创建新的音频元素
      audioElement.value = new Audio(currentAudio.value.url)
      
      // 设置音频属性
      audioElement.value.volume = volume.value
      audioElement.value.playbackRate = playbackRate.value

      // 绑定事件监听器
      setupAudioEventListeners()

      // 开始播放
      await audioElement.value.play()
      isPlaying.value = true
      
      message.success(`开始播放: ${currentAudio.value.title}`)

    } catch (err) {
      console.error('播放音频失败:', err)
      error.value = err.message
      loading.value = false
      
      if (err.name === 'NotAllowedError') {
        message.error('浏览器不允许自动播放音频，请先与页面交互')
      } else if (err.name === 'NotSupportedError') {
        message.error('音频格式不支持')
      } else {
        message.error(`播放失败: ${err.message}`)
      }
    }
  }

  // 暂停播放
  const pause = () => {
    if (audioElement.value && isPlaying.value) {
      audioElement.value.pause()
      isPlaying.value = false
    }
  }

  // 恢复播放
  const resume = async () => {
    if (audioElement.value && !isPlaying.value) {
      try {
        await audioElement.value.play()
        isPlaying.value = true
      } catch (err) {
        console.error('恢复播放失败:', err)
        message.error('恢复播放失败')
      }
    }
  }

  // 停止播放
  const stop = () => {
    if (audioElement.value) {
      audioElement.value.pause()
      audioElement.value.currentTime = 0
      audioElement.value = null
    }
    isPlaying.value = false
    currentTime.value = 0
    duration.value = 0
    loading.value = false
    error.value = null
  }

  // 设置播放进度
  const seekTo = (percentage) => {
    if (audioElement.value && duration.value > 0) {
      const newTime = (percentage / 100) * duration.value
      audioElement.value.currentTime = newTime
      currentTime.value = newTime
    }
  }

  // 设置音量
  const setVolume = (vol) => {
    volume.value = Math.max(0, Math.min(1, vol))
    if (audioElement.value) {
      audioElement.value.volume = volume.value
    }
  }

  // 设置播放速度
  const setPlaybackRate = (rate) => {
    playbackRate.value = rate
    if (audioElement.value) {
      audioElement.value.playbackRate = rate
    }
    message.success(`播放速度设置为 ${rate}x`)
  }

  // 设置音频事件监听器
  const setupAudioEventListeners = () => {
    if (!audioElement.value) return

    // 加载完成
    audioElement.value.addEventListener('loadedmetadata', () => {
      duration.value = audioElement.value.duration
      loading.value = false
    })

    // 时间更新
    audioElement.value.addEventListener('timeupdate', () => {
      currentTime.value = audioElement.value.currentTime
    })

    // 播放结束
    audioElement.value.addEventListener('ended', () => {
      isPlaying.value = false
      currentTime.value = 0
      message.success(`播放完成: ${currentAudio.value?.title}`)
      
      // 触发播放完成事件
      if (currentAudio.value?.metadata?.onEnded) {
        currentAudio.value.metadata.onEnded()
      }
    })

    // 播放错误
    audioElement.value.addEventListener('error', (e) => {
      console.error('音频播放错误:', e)
      error.value = '音频加载失败'
      loading.value = false
      isPlaying.value = false
      message.error(`播放失败: ${currentAudio.value?.title}`)
    })

    // 播放开始
    audioElement.value.addEventListener('play', () => {
      isPlaying.value = true
    })

    // 播放暂停
    audioElement.value.addEventListener('pause', () => {
      isPlaying.value = false
    })

    // 加载开始
    audioElement.value.addEventListener('loadstart', () => {
      loading.value = true
    })

    // 可以播放
    audioElement.value.addEventListener('canplay', () => {
      loading.value = false
    })
  }

  // 清理资源
  const cleanup = () => {
    stop()
    currentAudio.value = null
  }

  // 检查是否正在播放指定音频
  const isCurrentlyPlaying = (audioId) => {
    return currentAudio.value?.id === audioId && isPlaying.value
  }

  // 检查是否是当前音频
  const isCurrentAudio = (audioId) => {
    return currentAudio.value?.id === audioId
  }

  return {
    // 状态
    currentAudio,
    isPlaying,
    currentTime,
    duration,
    volume,
    playbackRate,
    loading,
    error,
    
    // 计算属性
    progress,
    formattedCurrentTime,
    formattedDuration,
    
    // 方法
    playAudio,
    pause,
    resume,
    stop,
    seekTo,
    setVolume,
    setPlaybackRate,
    cleanup,
    isCurrentlyPlaying,
    isCurrentAudio,
    
    // 工具函数
    formatTime
  }
}) 