<template>
  <div class="preview-panel">
    <!-- 简洁的预览头部 -->
    <div class="preview-header">
      <div class="preview-title">
        <h3>预览</h3>
      </div>
    </div>

    <!-- 主要显示区域 -->
    <div class="waveform-container" ref="waveformContainer">
      <div v-if="!hasAudio" class="waveform-placeholder">
        <SoundOutlined />
        <p>选择音频文件开始编辑</p>
        <a-button type="primary" @click="$emit('importAudio')">
          <PlusOutlined /> 导入音频
        </a-button>
      </div>
      
      <!-- 酷炫音频可视化动画 -->
      <div v-else class="audio-visualizer">
        <!-- 中央播放控制 -->
        <div class="visualizer-center">
          <div class="play-button-visual" :class="{ 'playing': isPlaying }" @click="togglePlayback">
            <div class="play-icon">
              <PlayCircleOutlined v-if="!isPlaying" />
              <PauseCircleOutlined v-else />
            </div>
            <div class="pulse-rings">
              <div class="pulse-ring pulse-ring-1"></div>
              <div class="pulse-ring pulse-ring-2"></div>
              <div class="pulse-ring pulse-ring-3"></div>
            </div>
          </div>
        </div>
        
        <!-- 音频条形可视化 -->
        <div class="audio-bars" :class="{ 'animating': isPlaying }">
          <div 
            v-for="(height, index) in barHeights" 
            :key="index" 
            class="audio-bar" 
            :style="{ 
              animationDelay: (index * 0.05) + 's',
              height: isPlaying ? height + '%' : '10%'
            }"
          ></div>
        </div>
        
        <!-- 时间显示 -->
        <div class="time-overlay">
          <div class="current-time">{{ formatTime(currentTime) }}</div>
          <div class="progress-line" @click="handleProgressClick">
            <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
          </div>
          <div class="total-time">{{ formatTime(duration) }}</div>
        </div>
        
        <!-- 多轨道状态显示 -->
        <div v-if="audioSources.length > 0" class="multi-track-status">
          <div class="status-badge">
            <SoundOutlined />
            {{ audioSources.length }} 个音轨混音中
          </div>
        </div>
        
        <!-- 粒子效果 -->
        <div class="particles" v-if="isPlaying">
          <div v-for="i in 20" :key="i" class="particle" :style="{
            left: Math.random() * 100 + '%',
            animationDelay: Math.random() * 2 + 's',
            animationDuration: (Math.random() * 3 + 2) + 's'
          }"></div>
        </div>
      </div>
    </div>

    <!-- 极简播放控制栏 -->
    <div class="simple-controls" v-if="hasAudio">
      <div class="control-left">
        <a-button 
          type="primary" 
          shape="circle" 
          size="large"
          @click="togglePlayback"
          class="main-play-btn"
        >
          <PlayCircleOutlined v-if="!isPlaying" />
          <PauseCircleOutlined v-else />
        </a-button>

        <div class="time-display">
          <span>{{ formatTime(currentTime) }}</span>
          <span class="time-separator">/</span>
          <span>{{ formatTime(duration) }}</span>
        </div>
      </div>

      <div class="control-right">
        <!-- 只保留音量控制 -->
        <div class="volume-controls">
          <SoundOutlined />
          <a-slider
            v-model:value="volume"
            :min="0"
            :max="100"
            style="width: 80px; margin: 0 8px;"
            @change="handleVolumeChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { 
  PlayCircleOutlined, PauseCircleOutlined, BorderOutlined,
  SoundOutlined, PlusOutlined, MinusOutlined, CompressOutlined,
  ZoomInOutlined, AppstoreOutlined, TableOutlined,
  FullscreenOutlined, FullscreenExitOutlined
} from '@ant-design/icons-vue'
// import WaveformViewer from './WaveformViewer.vue' // 已移除，改为酷炫动画

export default {
  name: 'PreviewPanel',
  components: {
    PlayCircleOutlined, PauseCircleOutlined, BorderOutlined,
    SoundOutlined, PlusOutlined, MinusOutlined, CompressOutlined,
    ZoomInOutlined, AppstoreOutlined, TableOutlined,
    FullscreenOutlined, FullscreenExitOutlined
    // WaveformViewer 已移除
  },
  props: {
    audioData: {
      type: Object,
      default: null
    },
    // 修改：接受所有轨道信息用于混音
    tracks: {
      type: Array,
      default: () => []
    },
    // 新增：外部播放控制
    externalIsPlaying: {
      type: Boolean,
      default: false
    },
    externalCurrentTime: {
      type: Number,
      default: 0
    },
    // 新增：项目总时长
    totalDuration: {
      type: Number,
      default: 0
    }
  },
  emits: ['play', 'pause', 'stop', 'seek', 'volumeChange', 'importAudio', 'togglePlay'],
  setup(props, { emit }) {
    // 核心状态
    const waveformContainer = ref(null)
    const volume = ref(80)
    
    // 音频播放相关状态
    const audioElement = ref(null)
    const audioContext = ref(null)
    const audioSources = ref([])
    const masterGainNode = ref(null)
    const isPlaying = ref(false)
    const currentTime = ref(0)
    const duration = ref(0)
    const isLoading = ref(false)
    
    // 动画相关状态
    const animationTimer = ref(null)
    const barHeights = ref(Array(32).fill(0).map(() => Math.random() * 60 + 20))

    // 计算属性
    const hasAudio = computed(() => {
      return props.tracks && props.tracks.length > 0 && 
             props.tracks.some(track => track.segments && track.segments.length > 0)
    })
    
    // 播放进度百分比
    const progressPercentage = computed(() => {
      if (!duration.value || duration.value === 0) return 0
      return (currentTime.value / duration.value) * 100
    })

    // 初始化音频播放器 - 支持多轨道混音
    const initAudioPlayer = () => {
      console.log('🎵 初始化多轨道混音播放器')
      
      // 清理现有音频元素
      if (audioElement.value) {
        audioElement.value.pause()
        audioElement.value.remove()
        audioElement.value = null
      }
      
      if (!hasAudio.value) {
        return
      }
      
      // 使用项目总时长
      duration.value = props.totalDuration || 0
      console.log('🎵 项目总时长:', duration.value)
      
      // 创建混音音频
      createMixedAudio()
    }
    
    // 创建混音音频
    const createMixedAudio = async () => {
      try {
        console.log('🎛️ 创建Web Audio API多轨道混音...')
        
        // 清理现有音频资源
        if (audioContext.value) {
          await audioContext.value.close()
        }
        audioSources.value.forEach(source => {
          if (source.audio) source.audio.pause()
        })
        audioSources.value = []
        
        // 获取所有活跃的音频片段
        const activeSegments = []
        props.tracks.forEach(track => {
          if (!track.muted && track.segments) {
            track.segments.forEach(segment => {
              activeSegments.push({
                ...segment,
                trackVolume: track.volume || 1,
                trackMuted: track.muted || false
              })
            })
          }
        })
        
        console.log('🎵 活跃音频片段:', activeSegments.length)
        
        if (activeSegments.length === 0) {
          console.log('⚠️ 没有活跃的音频片段')
          return
        }
        
        // 创建Web Audio上下文
        audioContext.value = new (window.AudioContext || window.webkitAudioContext)()
        masterGainNode.value = audioContext.value.createGain()
        masterGainNode.value.connect(audioContext.value.destination)
        
        // 为每个音频片段创建音频源
        for (const segment of activeSegments) {
          try {
            console.log('🎵 加载音频片段:', segment.name, {
              startTime: segment.startTime,
              endTime: segment.endTime,
              audioUrl: segment.audioUrl,
              trackVolume: segment.trackVolume
            })
            
            const audio = new Audio()
            audio.crossOrigin = 'anonymous'
            audio.preload = 'auto'
            audio.src = segment.audioUrl
            
            // 等待音频加载
            await new Promise((resolve, reject) => {
              const timeout = setTimeout(() => {
                reject(new Error('音频加载超时'))
              }, 10000) // 10秒超时
              
              audio.addEventListener('loadedmetadata', () => {
                clearTimeout(timeout)
                resolve()
              }, { once: true })
              
              audio.addEventListener('error', (e) => {
                clearTimeout(timeout)
                reject(e)
              }, { once: true })
            })
            
            // 创建MediaElementAudioSourceNode
            const sourceNode = audioContext.value.createMediaElementSource(audio)
            const gainNode = audioContext.value.createGain()
            
            // 设置音量
            const volume = segment.trackVolume || 1
            gainNode.gain.value = volume
            
            // 连接音频图
            sourceNode.connect(gainNode)
            gainNode.connect(masterGainNode.value)
            
            // 计算片段时间范围（使用segment中定义的时间范围）
            const startTime = segment.startTime || 0
            const endTime = segment.endTime || (startTime + (audio.duration || 10))
            
            // 存储音频源信息
            audioSources.value.push({
              audio,
              sourceNode,
              gainNode,
              segment,
              startTime,
              endTime
            })
            
            console.log('✅ 音频片段加载成功:', segment.name, {
              audioUrl: segment.audioUrl,
              segmentStartTime: segment.startTime,
              segmentEndTime: segment.endTime,
              audioDuration: audio.duration,
              calculatedStartTime: startTime,
              calculatedEndTime: endTime,
              volume
            })
            
          } catch (error) {
            console.error('❌ 加载音频片段失败:', segment.name, error)
          }
        }
        
        // 设置总时长为项目时长
        duration.value = props.totalDuration || 0
        
        // 设置主音频元素为第一个片段（用于时间同步）
        if (audioSources.value.length > 0) {
          audioElement.value = audioSources.value[0].audio
          setupAudioEvents()
        }
        
        console.log('🎛️ 混音设置完成，共', audioSources.value.length, '个音频源')
        
      } catch (error) {
        console.error('🔥 创建混音失败:', error)
      }
    }
    
    // 设置音频事件监听
    const setupAudioEvents = () => {
      if (!audioElement.value) return
      
      // 清理现有事件监听器
      audioElement.value.removeEventListener('ended', handleAudioEnded)
      audioElement.value.removeEventListener('error', handleAudioError)
      
      // 只监听结束和错误事件，不监听timeupdate（避免时间循环）
      audioElement.value.addEventListener('ended', handleAudioEnded)
      audioElement.value.addEventListener('error', handleAudioError)
    }
    
    // 不再需要handleTimeUpdate，完全依赖外部时间控制
    
    // 同步所有音频源
    const syncAllAudioSources = () => {
      // 使用外部传入的时间作为主时间源
      const masterTime = props.externalCurrentTime || currentTime.value
      let activeSourcesCount = 0
      
      console.log(`🎵 同步音频源 - 主时间: ${masterTime.toFixed(2)}s, 总源数量: ${audioSources.value.length}`)
      
      audioSources.value.forEach((source, index) => {
        const { audio, startTime, endTime, segment } = source
        
        // 检查是否在播放时间范围内
        const isInTimeRange = masterTime >= startTime && masterTime <= endTime
        const shouldPlay = isInTimeRange && isPlaying.value
        
        console.log(`🎵 音频源 ${index + 1} [${segment.name}]: 时间范围 ${startTime.toFixed(2)}-${endTime.toFixed(2)}s, 当前时间 ${masterTime.toFixed(2)}s, 应播放: ${shouldPlay}`)
        
        if (shouldPlay) {
          activeSourcesCount++
          
          // 计算相对播放时间
          const relativeTime = Math.max(0, masterTime - startTime)
          
          // 如果音频暂停且应该播放
          if (audio.paused) {
            console.log(`▶️ 启动音频源 ${index + 1}: ${segment.name}, 相对时间: ${relativeTime.toFixed(2)}s`)
            try {
              audio.currentTime = relativeTime
              audio.play().catch(error => {
                console.error(`❌ 音频源 ${index + 1} 播放失败:`, error)
              })
            } catch (error) {
              console.error(`❌ 音频源 ${index + 1} 时间设置失败:`, error)
            }
          } else {
            // 已在播放，检查时间是否需要校正
            const timeDiff = Math.abs(audio.currentTime - relativeTime)
            if (timeDiff > 0.5) {
              console.log(`🔄 校正音频源 ${index + 1} 时间: ${audio.currentTime.toFixed(2)}s → ${relativeTime.toFixed(2)}s`)
              try {
                audio.currentTime = relativeTime
              } catch (error) {
                console.error(`❌ 音频源 ${index + 1} 时间校正失败:`, error)
              }
            }
          }
        } else {
          // 不在时间范围内或不应播放，暂停音频
          if (!audio.paused) {
            console.log(`⏸️ 暂停音频源 ${index + 1}: ${segment.name}`)
            audio.pause()
          }
        }
      })
      
      console.log(`🎛️ 同步完成 - 活跃音频源: ${activeSourcesCount}/${audioSources.value.length}`)
    }
    
    // 音频结束处理
    const handleAudioEnded = () => {
      isPlaying.value = false
      emit('pause')
      stopAnimation()
    }
    
    // 音频错误处理
    const handleAudioError = (e) => {
      console.error('🔥 混音音频播放错误:', e)
      isPlaying.value = false
      stopAnimation()
    }

    // 动画控制
    const startAnimation = () => {
      if (animationTimer.value) return
      animationTimer.value = setInterval(() => {
        barHeights.value = barHeights.value.map(() => Math.random() * 60 + 20)
      }, 150)
    }
    
    const stopAnimation = () => {
      if (animationTimer.value) {
        clearInterval(animationTimer.value)
        animationTimer.value = null
      }
    }

    // 播放控制
    const togglePlayback = () => {
      console.log('🎤 PreviewPanel: togglePlayback 被点击')
      emit('togglePlay')
    }

    // 进度条点击
    const handleProgressClick = (event) => {
      if (!audioElement.value || !duration.value) return
      
      const rect = event.target.getBoundingClientRect()
      const clickX = event.clientX - rect.left
      const percentage = clickX / rect.width
      const newTime = percentage * duration.value
      
      if (audioElement.value) {
        audioElement.value.currentTime = newTime
        currentTime.value = newTime
        emit('seek', newTime)
      }
    }

    // 音量控制
    const handleVolumeChange = (value) => {
      volume.value = value
      if (audioElement.value) {
        audioElement.value.volume = value / 100
      }
      emit('volumeChange', value)
    }

    // 时间格式化
    const formatTime = (seconds) => {
      if (!seconds || isNaN(seconds)) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    // 监听轨道变化
    watch(() => props.tracks, (newTracks) => {
      console.log('🔄 轨道变化，重新初始化混音:', newTracks?.length || 0)
      initAudioPlayer()
    }, { immediate: true, deep: true })

    // 监听外部播放状态变化
    watch(() => props.externalIsPlaying, async (newPlaying) => {
      console.log('🎤 外部播放状态变化:', newPlaying, '当前状态:', isPlaying.value, '音频源数量:', audioSources.value.length)
      
      if (!audioSources.value.length && hasAudio.value) {
        console.log('🔄 重新初始化音频播放器')
        initAudioPlayer()
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      if (audioSources.value.length > 0) {
        try {
          if (newPlaying && !isPlaying.value) {
            console.log('🎵 开始多轨道混音播放', {
              音频源数量: audioSources.value.length,
              当前时间: currentTime.value
            })
            
            isPlaying.value = true
            startAnimation()
            
            // 恢复Web Audio上下文
            if (audioContext.value && audioContext.value.state === 'suspended') {
              console.log('🔊 恢复Web Audio上下文')
              await audioContext.value.resume()
            }
            
            // 同步播放所有相关音频源
            console.log('🎛️ 开始同步所有音频源')
            syncAllAudioSources()
            
            // 开始主时间计时
            if (audioElement.value) {
              console.log('⏰ 启动主音频计时器')
              await audioElement.value.play()
            }
            
          } else if (!newPlaying && isPlaying.value) {
            console.log('⏸️ 暂停多轨道混音播放')
            isPlaying.value = false
            stopAnimation()
            
            // 暂停所有音频源
            let pausedCount = 0
            audioSources.value.forEach((source, index) => {
              if (!source.audio.paused) {
                console.log(`⏸️ 暂停音频源 ${index + 1}: ${source.segment.name}`)
                source.audio.pause()
                pausedCount++
              }
            })
            console.log(`⏸️ 已暂停 ${pausedCount} 个音频源`)
          }
        } catch (error) {
          console.error('❌ 多轨道播放控制错误:', error)
          isPlaying.value = false
          stopAnimation()
        }
      } else {
        console.log('⚠️ 没有音频源可播放')
      }
    })

    // 监听外部时间变化（拖拽播放头时）
    watch(() => props.externalCurrentTime, (newTime) => {
      console.log('🔄 外部时间变化:', newTime, '当前时间:', currentTime.value)
      
      if (newTime !== undefined && newTime !== currentTime.value) {
        console.log('🎯 执行时间跳转:', newTime)
        currentTime.value = newTime
        
        // 同步所有音频源到新时间
        if (audioSources.value.length > 0) {
          syncAllAudioSources()
        }
      }
    })

    // 监听轨道变化，重新初始化音频播放器
    watch(() => props.tracks, () => {
      console.log('🔄 轨道变化，重新初始化音频播放器')
      initAudioPlayer()
    }, { deep: true })

    // 生命周期
    onMounted(() => {
      if (hasAudio.value) {
        initAudioPlayer()
      }
    })

    onUnmounted(() => {
      stopAnimation()
      
      // 清理所有音频源
      audioSources.value.forEach(source => {
        if (source.audio) {
          source.audio.pause()
          source.audio.remove()
        }
      })
      
      // 清理Web Audio上下文
      if (audioContext.value) {
        audioContext.value.close()
      }
      
      // 清理主音频元素
      if (audioElement.value) {
        audioElement.value.pause()
        audioElement.value.remove()
      }
    })

    return {
      waveformContainer,
      volume,
      hasAudio,
      isPlaying,
      currentTime,
      duration,
      isLoading,
      progressPercentage,
      barHeights,
      audioSources, // 添加 audioSources 到返回值
      togglePlayback,
      handleProgressClick,
      handleVolumeChange,
      formatTime
    }
  }
}
</script>

<style scoped>
.preview-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-color-container);
  border-radius: 8px;
  overflow: hidden;
}

/* 简洁头部 */
.preview-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-color-elevated);
}

.preview-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

/* 主显示区域 */
.waveform-container {
  flex: 1;
  position: relative;
  min-height: 200px;
  background: var(--bg-color);
}

.waveform-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-color-secondary);
  text-align: center;
}

.waveform-placeholder .anticon {
  font-size: 48px;
  color: var(--text-color-disabled);
  margin-bottom: 16px;
}

.waveform-placeholder p {
  margin: 8px 0 16px 0;
  font-size: 14px;
}

/* 酷炫音频可视化动画 */
.audio-visualizer {
  position: relative;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 中央播放控制 */
.visualizer-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
}

.play-button-visual {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.play-button-visual:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.play-icon {
  font-size: 48px;
  color: white;
  z-index: 2;
}

/* 脉冲动画 */
.pulse-rings {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.pulse-ring {
  position: absolute;
  border: 2px solid rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  width: 120px;
  height: 120px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.play-button-visual.playing .pulse-ring {
  animation: pulse 2s infinite;
}

.pulse-ring-1 { animation-delay: 0s; }
.pulse-ring-2 { animation-delay: 0.7s; }
.pulse-ring-3 { animation-delay: 1.4s; }

@keyframes pulse {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.6;
  }
  50% {
    opacity: 0.3;
  }
  100% {
    transform: translate(-50%, -50%) scale(2);
    opacity: 0;
  }
}

/* 音频条形 */
.audio-bars {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
  align-items: end;
  height: 80px;
}

.audio-bar {
  width: 6px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 3px;
  transition: height 0.3s ease;
  min-height: 8px;
}

.audio-bars.animating .audio-bar {
  animation: barBounce 0.8s ease-in-out infinite;
}

@keyframes barBounce {
  0%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(1.5); }
}

/* 时间显示 */
.time-overlay {
  position: absolute;
  bottom: 20px;
  left: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.progress-line {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  position: relative;
  cursor: pointer;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #52c41a, #73d13d);
  border-radius: 2px;
  transition: width 0.1s ease;
  box-shadow: 0 0 8px rgba(82, 196, 26, 0.5);
}

/* 多轨道状态显示 */
.multi-track-status {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 15;
}

.status-badge {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  color: white;
  padding: 8px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.status-badge .anticon {
  font-size: 14px;
  color: #52c41a;
}

/* 粒子效果 */
.particles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  animation: particleRise infinite linear;
}

@keyframes particleRise {
  from {
    bottom: 0;
    opacity: 1;
  }
  to {
    bottom: 100%;
    opacity: 0;
  }
}

/* 简洁控制栏 */
.simple-controls {
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-color-elevated);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.control-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-play-btn {
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.time-display {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 13px;
  color: var(--text-color);
}

.time-separator {
  color: var(--text-color-secondary);
}

.volume-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .simple-controls {
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  }
  
  .control-left,
  .control-right {
    width: 100%;
    justify-content: center;
  }
  
  .play-button-visual {
    width: 80px;
    height: 80px;
  }
  
  .play-icon {
    font-size: 32px;
  }
  
  .pulse-ring {
    width: 80px;
    height: 80px;
  }
}

/* 暗黑主题适配 */
[data-theme='dark'] .preview-panel {
  --bg-color: #141414;
  --bg-color-container: #1f1f1f;
  --bg-color-elevated: #262626;
  --text-color: rgba(255, 255, 255, 0.85);
  --text-color-secondary: rgba(255, 255, 255, 0.65);
  --text-color-disabled: rgba(255, 255, 255, 0.25);
  --border-color: #434343;
}
</style>