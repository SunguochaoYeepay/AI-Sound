<template>
  <div class="audio-player" :class="{ 'small': size === 'small' }">
    <div class="player-header" v-if="title && size !== 'small'">
      <h4>{{ title }}</h4>
    </div>
    
    <div class="player-controls">
      <a-button
        type="text"
        :icon="playing ? 'PauseCircleOutlined' : 'PlayCircleOutlined'"
        @click="togglePlay"
        :size="size === 'small' ? 'small' : 'default'"
        class="play-button"
      >
        <PlayCircleOutlined v-if="!playing" />
        <PauseCircleOutlined v-else />
      </a-button>

      <div class="progress-area" v-if="size !== 'small'">
        <div class="time-display">
          {{ formatTime(currentTime) }} / {{ duration || '0:00' }}
        </div>
        <a-slider
          v-model:value="progress"
          :min="0"
          :max="100"
          @change="onProgressChange"
          :tip-formatter="null"
          class="progress-slider"
        />
      </div>

      <div class="action-buttons">
        <a-button
          type="text"
          @click="handleDownload"
          :size="size === 'small' ? 'small' : 'default'"
          title="下载音频"
        >
          <DownloadOutlined />
        </a-button>
        
        <a-dropdown v-if="size !== 'small'">
          <a-button type="text" :size="size === 'small' ? 'small' : 'default'">
            <MoreOutlined />
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item @click="setPlaybackRate(0.5)">
                <span>0.5x 慢速</span>
              </a-menu-item>
              <a-menu-item @click="setPlaybackRate(1.0)">
                <span>1.0x 正常</span>
              </a-menu-item>
              <a-menu-item @click="setPlaybackRate(1.5)">
                <span>1.5x 快速</span>
              </a-menu-item>
              <a-menu-item @click="setPlaybackRate(2.0)">
                <span>2.0x 超快</span>
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 简化版本（small size） -->
    <div v-if="size === 'small'" class="small-info">
      <span class="small-title">{{ title }}</span>
      <span class="small-duration">{{ duration }}</span>
    </div>

    <!-- 音频元素 -->
    <audio
      ref="audioRef"
      :src="audioUrl"
      @loadedmetadata="onLoadedMetadata"
      @timeupdate="onTimeUpdate"
      @ended="onEnded"
      @error="onError"
      preload="metadata"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  DownloadOutlined,
  MoreOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  audioUrl: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: ''
  },
  duration: {
    type: String,
    default: ''
  },
  size: {
    type: String,
    default: 'default', // 'default' | 'small'
    validator: (value) => ['default', 'small'].includes(value)
  }
})

// Emits
const emit = defineEmits(['download', 'play', 'pause', 'ended'])

// 响应式数据
const audioRef = ref(null)
const playing = ref(false)
const currentTime = ref(0)
const totalDuration = ref(0)
const progress = ref(0)
const playbackRate = ref(1.0)

// 计算属性
const progressPercent = computed(() => {
  if (totalDuration.value === 0) return 0
  return (currentTime.value / totalDuration.value) * 100
})

// 监听器
watch(() => props.audioUrl, () => {
  // 当音频URL变化时重置播放状态
  resetPlayer()
})

watch(progressPercent, (newVal) => {
  progress.value = newVal
})

// 方法
const togglePlay = () => {
  if (!audioRef.value) return

  if (playing.value) {
    pause()
  } else {
    play()
  }
}

const play = () => {
  if (!audioRef.value) return

  audioRef.value.play()
    .then(() => {
      playing.value = true
      emit('play')
    })
    .catch((error) => {
      console.error('播放失败:', error)
      message.error('音频播放失败')
    })
}

const pause = () => {
  if (!audioRef.value) return

  audioRef.value.pause()
  playing.value = false
  emit('pause')
}

const resetPlayer = () => {
  pause()
  currentTime.value = 0
  progress.value = 0
  totalDuration.value = 0
}

const formatTime = (seconds) => {
  if (isNaN(seconds)) return '0:00'
  
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const onLoadedMetadata = () => {
  if (audioRef.value) {
    totalDuration.value = audioRef.value.duration
  }
}

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
  }
}

const onEnded = () => {
  playing.value = false
  currentTime.value = 0
  progress.value = 0
  emit('ended')
}

const onError = (error) => {
  console.error('音频加载错误:', error)
  message.error('音频加载失败，请检查文件是否存在')
  playing.value = false
}

const onProgressChange = (value) => {
  if (!audioRef.value || totalDuration.value === 0) return

  const newTime = (value / 100) * totalDuration.value
  audioRef.value.currentTime = newTime
  currentTime.value = newTime
}

const setPlaybackRate = (rate) => {
  if (!audioRef.value) return

  audioRef.value.playbackRate = rate
  playbackRate.value = rate
  message.success(`播放速度设置为 ${rate}x`)
}

const handleDownload = () => {
  emit('download', props.audioUrl)
}

// 清理
onUnmounted(() => {
  if (audioRef.value) {
    audioRef.value.pause()
    audioRef.value.src = ''
  }
})
</script>

<style scoped>
.audio-player {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.audio-player.small {
  padding: 8px 12px;
  border-radius: 6px;
}

.player-header h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 14px;
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.play-button {
  font-size: 20px;
  color: #1890ff;
  flex-shrink: 0;
}

.progress-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.time-display {
  font-size: 12px;
  color: #666;
  text-align: center;
}

.progress-slider {
  margin: 0 !important;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.small-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
}

.small-title {
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.small-duration {
  color: #666;
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .player-controls {
    flex-direction: column;
    gap: 8px;
  }

  .progress-area {
    width: 100%;
  }

  .action-buttons {
    align-self: flex-end;
  }
}
</style>