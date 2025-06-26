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
      console.log('🎵 [播放请求] 开始播放音频:', audioInfo)
      
      // 验证音频信息
      if (!audioInfo) {
        console.error('🎵 [播放失败] 音频信息为空')
        error.value = '音频信息为空'
        message.error('音频信息为空')
        return
      }

      const audioUrl = audioInfo.url || audioInfo.audioUrl
      if (!audioUrl) {
        console.error('🎵 [播放失败] 音频URL为空:', audioInfo)
        error.value = '音频URL为空'
        message.error('音频URL为空')
        return
      }

      // 验证URL格式
      try {
        new URL(audioUrl)
      } catch (urlError) {
        // 如果不是完整URL，检查是否是相对路径
        if (!audioUrl.startsWith('/') && !audioUrl.startsWith('blob:')) {
          console.error('🎵 [播放失败] 音频URL格式无效:', audioUrl)
          error.value = '音频URL格式无效'
          message.error('音频URL格式无效')
          return
        }
      }
      
      // 如果是同一个音频，切换播放/暂停
      if (currentAudio.value?.id === audioInfo.id) {
        console.log('🎵 [相同音频] 切换播放/暂停状态')
        if (isPlaying.value) {
          pause()
        } else {
          resume()
        }
        return
      }

      // 温和地停止当前播放
      if (audioElement.value) {
        console.log('🎵 [停止当前] 停止当前播放的音频')
        try {
          if (audioElement.value.readyState >= 1) {
            audioElement.value.pause()
          }
        } catch (err) {
          console.debug('🎵 [切换错误] 切换音频时的非关键错误:', err)
        }
        audioElement.value = null
      }

      // 设置新音频
      currentAudio.value = {
        id: audioInfo.id,
        title: audioInfo.title || audioInfo.name || '未知音频',
        url: audioUrl,
        type: audioInfo.type || 'unknown',
        metadata: audioInfo.metadata || {}
      }

      console.log('🎵 [音频信息] 准备播放:', currentAudio.value)

      loading.value = true
      error.value = null

      // 创建新的音频元素
      console.log('🎵 [创建音频] 创建新的音频元素，URL:', currentAudio.value.url)
      audioElement.value = new Audio(currentAudio.value.url)
      
      // 设置音频属性
      audioElement.value.volume = volume.value
      audioElement.value.playbackRate = playbackRate.value

      // 绑定事件监听器
      console.log('🎵 [绑定事件] 设置音频事件监听器')
      setupAudioEventListeners()

      // 等待一下让事件监听器设置完成
      await new Promise(resolve => setTimeout(resolve, 100))

      // 开始播放
      console.log('🎵 [开始播放] 调用play()方法')
      await audioElement.value.play()
      isPlaying.value = true
      
      console.log('🎵 [播放成功] 音频播放成功')
      message.success(`开始播放: ${currentAudio.value.title}`)

    } catch (err) {
      console.error('🎵 [播放失败] 播放音频失败:', {
        error: err,
        name: err.name,
        message: err.message,
        stack: err.stack,
        audioInfo: audioInfo,
        audioElement: audioElement.value,
        readyState: audioElement.value?.readyState,
        networkState: audioElement.value?.networkState,
        src: audioElement.value?.src
      })
      error.value = err.message
      loading.value = false
      
      if (err.name === 'NotAllowedError') {
        message.error('浏览器不允许自动播放音频，请先与页面交互')
      } else if (err.name === 'NotSupportedError') {
        message.error('音频格式不支持')
      } else if (err.name === 'AbortError') {
        console.log('🎵 [播放中止] 播放被中止，这通常是正常的切换行为')
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
      // 移除事件监听器，避免在清理过程中触发事件
      const audio = audioElement.value
      try {
        // 只有在音频处于可控制状态时才暂停
        if (audio.readyState >= 1) { // HAVE_METADATA
          audio.pause()
          audio.currentTime = 0
        } else {
          // 如果音频还在加载，直接设置src为空来停止加载
          audio.src = ''
        }
      } catch (err) {
        // 忽略停止时的错误
        console.debug('停止音频时的非关键错误:', err)
      }
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

    // 📊 调试：添加所有音频事件监听
    const debugEvents = ['loadstart', 'progress', 'suspend', 'abort', 'error', 'emptied', 'stalled', 'loadedmetadata', 'loadeddata', 'canplay', 'canplaythrough', 'playing', 'waiting', 'seeking', 'seeked', 'ended', 'durationchange', 'timeupdate', 'play', 'pause', 'ratechange', 'resize', 'volumechange']
    
    debugEvents.forEach(eventType => {
      audioElement.value.addEventListener(eventType, (e) => {
        console.log(`🎵 [音频事件] ${eventType}:`, {
          readyState: audioElement.value?.readyState,
          networkState: audioElement.value?.networkState,
          duration: audioElement.value?.duration,
          currentTime: audioElement.value?.currentTime,
          paused: audioElement.value?.paused,
          error: audioElement.value?.error,
          src: audioElement.value?.src,
          event: e
        })
      })
    })

    // 加载完成
    audioElement.value.addEventListener('loadedmetadata', () => {
      console.log('🎵 [加载完成] 音频元数据已加载')
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
      console.error('🎵 [播放错误] 音频播放错误:', {
        error: e,
        audioError: audioElement.value?.error,
        networkState: audioElement.value?.networkState,
        readyState: audioElement.value?.readyState,
        src: audioElement.value?.src
      })
      error.value = '音频加载失败'
      loading.value = false
      isPlaying.value = false
      message.error(`播放失败: ${currentAudio.value?.title}`)
    })

    // 播放开始
    audioElement.value.addEventListener('play', () => {
      console.log('🎵 [播放开始] 音频开始播放')
      isPlaying.value = true
    })

    // 播放暂停
    audioElement.value.addEventListener('pause', () => {
      console.log('🎵 [播放暂停] 音频暂停')
      isPlaying.value = false
    })

    // 加载开始
    audioElement.value.addEventListener('loadstart', () => {
      console.log('🎵 [加载开始] 开始加载音频')
      loading.value = true
    })

    // 可以播放
    audioElement.value.addEventListener('canplay', () => {
      console.log('🎵 [可以播放] 音频可以开始播放')
      loading.value = false
    })

    // 网络状态异常检测
    audioElement.value.addEventListener('stalled', () => {
      console.warn('🎵 [网络停滞] 音频加载停滞')
      // 10秒后如果还在加载，显示错误
      setTimeout(() => {
        if (loading.value && audioElement.value?.networkState === 2) { // NETWORK_LOADING
          console.error('🎵 [加载超时] 音频加载超时')
          error.value = '音频加载超时'
          loading.value = false
          message.error('音频加载超时，请检查网络连接')
        }
      }, 10000)
    })

    // 空资源检测
    audioElement.value.addEventListener('emptied', () => {
      console.warn('🎵 [资源为空] 音频资源为空')
    })

    // 中止检测
    audioElement.value.addEventListener('abort', () => {
      console.warn('🎵 [加载中止] 音频加载被中止')
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