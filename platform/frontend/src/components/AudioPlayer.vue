<template>
  <div class="audio-player" :class="{ 'small': size === 'small', 'mini': size === 'mini' }">
    <!-- 完整播放器 -->
    <template v-if="size === 'default'">
      <div class="player-header" v-if="showTitle">
        <h4>{{ displayTitle }}</h4>
    </div>
    
    <div class="player-controls">
      <a-button
        type="text"
          :loading="audioStore.loading"
        @click="togglePlay"
        class="play-button"
          size="large"
      >
          <PlayCircleOutlined v-if="!audioStore.isPlaying" />
        <PauseCircleOutlined v-else />
      </a-button>

        <div class="progress-area">
        <div class="time-display">
            {{ audioStore.formattedCurrentTime }} / {{ audioStore.formattedDuration }}
        </div>
        <a-slider
            :value="audioStore.progress"
          :min="0"
          :max="100"
          @change="onProgressChange"
          :tip-formatter="null"
          class="progress-slider"
            :disabled="audioStore.duration === 0"
        />
      </div>

      <div class="action-buttons">
          <a-tooltip title="下载音频">
        <a-button
          type="text"
          @click="handleDownload"
              :icon="h(DownloadOutlined)"
            />
          </a-tooltip>
        
          <a-dropdown>
            <a-button type="text" :icon="h(MoreOutlined)" />
          <template #overlay>
            <a-menu>
                <a-menu-item @click="() => audioStore.setPlaybackRate(0.5)">
                <span>0.5x 慢速</span>
              </a-menu-item>
                <a-menu-item @click="() => audioStore.setPlaybackRate(1.0)">
                <span>1.0x 正常</span>
              </a-menu-item>
                <a-menu-item @click="() => audioStore.setPlaybackRate(1.5)">
                <span>1.5x 快速</span>
              </a-menu-item>
                <a-menu-item @click="() => audioStore.setPlaybackRate(2.0)">
                <span>2.0x 超快</span>
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

          <a-tooltip title="音量控制">
            <a-dropdown>
              <a-button type="text" :icon="h(SoundOutlined)" />
              <template #overlay>
                <div class="volume-control">
                  <a-slider
                    :value="audioStore.volume * 100"
                    :min="0"
                    :max="100"
                    vertical
                    @change="onVolumeChange"
                    style="height: 100px; margin: 16px;"
                  />
                </div>
              </template>
            </a-dropdown>
          </a-tooltip>
        </div>
      </div>
    </template>

    <!-- 小型播放器 -->
    <template v-else-if="size === 'small'">
      <div class="small-player">
        <a-button
          type="text"
          :loading="audioStore.loading"
          @click="togglePlay"
          class="small-play-button"
        >
          <PlayCircleOutlined v-if="!audioStore.isPlaying" />
          <PauseCircleOutlined v-else />
        </a-button>
        
        <div class="small-info">
          <div class="small-title">{{ displayTitle }}</div>
          <div class="small-time">{{ audioStore.formattedCurrentTime }} / {{ audioStore.formattedDuration }}</div>
        </div>

        <div class="small-actions">
          <a-button type="text" size="small" @click="handleDownload">
            <DownloadOutlined />
          </a-button>
      </div>
    </div>

      <div class="small-progress">
        <a-slider
          :value="audioStore.progress"
          :min="0"
          :max="100"
          @change="onProgressChange"
          :tip-formatter="null"
          size="small"
          :disabled="audioStore.duration === 0"
        />
      </div>
    </template>

    <!-- 迷你播放器 -->
    <template v-else-if="size === 'mini'">
      <div class="mini-player">
        <a-button
          type="text"
          :loading="audioStore.loading"
          @click="togglePlay"
          size="small"
          class="mini-play-button"
        >
          <PlayCircleOutlined v-if="!audioStore.isPlaying" />
          <PauseCircleOutlined v-else />
        </a-button>
        
        <span class="mini-title">{{ displayTitle }}</span>
        
        <a-button type="text" size="small" @click="handleDownload">
          <DownloadOutlined />
        </a-button>
      </div>
    </template>

    <!-- 错误提示 -->
    <div v-if="audioStore.error" class="error-message">
      <ExclamationCircleOutlined />
      {{ audioStore.error }}
    </div>
  </div>
</template>

<script setup>
import { computed, h, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  DownloadOutlined,
  MoreOutlined,
  SoundOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import { useAudioPlayerStore } from '@/stores/audioPlayer'

// Props
const props = defineProps({
  audioInfo: {
    type: Object,
    default: () => null
  },
  size: {
    type: String,
    default: 'default', // 'default' | 'small' | 'mini'
    validator: (value) => ['default', 'small', 'mini'].includes(value)
  },
  showTitle: {
    type: Boolean,
    default: true
  },
  autoPlay: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['download', 'play', 'pause', 'ended'])

// Store
const audioStore = useAudioPlayerStore()

// 计算属性
const displayTitle = computed(() => {
  if (props.audioInfo) {
    return props.audioInfo.title || props.audioInfo.name || '音频播放器'
  }
  return audioStore.currentAudio?.title || '音频播放器'
})

const isCurrentAudio = computed(() => {
  return props.audioInfo && audioStore.isCurrentAudio(props.audioInfo.id)
})

// 监听器
watch(() => props.audioInfo, (newAudioInfo) => {
  if (newAudioInfo && props.autoPlay) {
    playCurrentAudio()
  }
}, { immediate: true })

watch(() => audioStore.isPlaying, (playing) => {
  if (isCurrentAudio.value) {
    emit(playing ? 'play' : 'pause')
  }
})

// 方法
const togglePlay = async () => {
  if (!props.audioInfo) {
    message.warning('没有可播放的音频')
    return
  }

  await audioStore.playAudio(props.audioInfo)
}

const playCurrentAudio = async () => {
  if (props.audioInfo) {
    await audioStore.playAudio(props.audioInfo)
  }
}

const onProgressChange = (value) => {
  audioStore.seekTo(value)
}

const onVolumeChange = (value) => {
  audioStore.setVolume(value / 100)
}

const handleDownload = () => {
  if (props.audioInfo?.url) {
    emit('download', props.audioInfo.url, props.audioInfo.title)
  } else {
    message.warning('没有可下载的音频')
  }
}

// 对外暴露的方法
defineExpose({
  play: playCurrentAudio,
  pause: audioStore.pause,
  stop: audioStore.stop,
  isPlaying: computed(() => isCurrentAudio.value && audioStore.isPlaying)
})
</script>

<style scoped>
.audio-player {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
  transition: all 0.3s ease;
}

.audio-player:hover {
  border-color: #d9d9d9;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.audio-player.small {
  padding: 12px;
  border-radius: 6px;
}

.audio-player.mini {
  padding: 8px 12px;
  border-radius: 4px;
  border: none;
  background: transparent;
}

/* 完整播放器样式 */
.player-header h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.play-button {
  font-size: 24px;
  color: #1890ff;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.play-button:hover {
  background-color: #e6f7ff;
  color: #0050b3;
}

.progress-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.time-display {
  font-size: 12px;
  color: #666;
  text-align: center;
  font-family: monospace;
}

.progress-slider {
  margin: 0 !important;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

/* 小型播放器样式 */
.small-player {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.small-play-button {
  font-size: 20px;
  color: #1890ff;
  flex-shrink: 0;
}

.small-info {
  flex: 1;
  min-width: 0;
}

.small-title {
  font-size: 13px;
  color: #333;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.small-time {
  font-size: 11px;
  color: #666;
  font-family: monospace;
}

.small-actions {
  flex-shrink: 0;
}

.small-progress {
  margin-top: 8px;
}

/* 迷你播放器样式 */
.mini-player {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mini-play-button {
  font-size: 16px;
  color: #1890ff;
  flex-shrink: 0;
}

.mini-title {
  flex: 1;
  font-size: 12px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

/* 音量控制 */
.volume-control {
  padding: 8px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 错误提示 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ff4d4f;
  font-size: 12px;
  margin-top: 8px;
  padding: 8px;
  background: #fff2f0;
  border-radius: 4px;
  border: 1px solid #ffccc7;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .player-controls {
    gap: 12px;
  }

  .action-buttons {
    gap: 2px;
  }
  
  .time-display {
    font-size: 11px;
  }
}

/* 加载状态样式 */
.play-button :deep(.ant-btn-loading-icon) {
  color: #1890ff;
}

/* 播放器激活状态 */
.audio-player.active {
  border-color: #1890ff;
  background: #f6ffed;
}
</style>