<template>
  <div v-if="audioStore.currentAudio" class="global-audio-player">
    <div class="player-container">
      <!-- 音频信息 -->
      <div class="audio-info">
        <div class="audio-icon">
          <SoundOutlined />
        </div>
        <div class="audio-details">
          <div class="audio-title">{{ audioStore.currentAudio.title }}</div>
          <div class="audio-type">{{ getTypeLabel(audioStore.currentAudio.type) }}</div>
        </div>
      </div>

      <!-- 播放控制 -->
      <div class="player-controls">
        <a-button
          type="text"
          :loading="audioStore.loading"
          @click="togglePlay"
          class="control-button play-button"
          size="large"
        >
          <PlayCircleOutlined v-if="!audioStore.isPlaying" />
          <PauseCircleOutlined v-else />
        </a-button>

        <div class="progress-container">
          <span class="time-text">{{ audioStore.formattedCurrentTime }}</span>
          <a-slider
            :value="audioStore.progress"
            :min="0"
            :max="100"
            @change="onProgressChange"
            :tip-formatter="null"
            class="progress-slider"
            :disabled="audioStore.duration === 0"
          />
          <span class="time-text">{{ audioStore.formattedDuration }}</span>
        </div>

        <a-button
          type="text"
          @click="stopPlay"
          class="control-button"
          title="停止播放"
        >
          <StopOutlined />
        </a-button>
      </div>

      <!-- 扩展控制 -->
      <div class="extended-controls">
        <!-- 音量控制 -->
        <a-dropdown placement="topCenter">
          <a-button type="text" class="control-button" title="音量控制">
            <SoundOutlined v-if="audioStore.volume > 0.5" />
            <CustomerServiceOutlined v-else-if="audioStore.volume > 0" />
            <MutedOutlined v-else />
          </a-button>
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

        <!-- 播放速度 -->
        <a-dropdown placement="topCenter">
          <a-button type="text" class="control-button" title="播放速度">
            {{ audioStore.playbackRate }}x
          </a-button>
          <template #overlay>
            <a-menu @click="onSpeedChange">
              <a-menu-item key="0.5">0.5x 慢速</a-menu-item>
              <a-menu-item key="0.75">0.75x</a-menu-item>
              <a-menu-item key="1.0">1.0x 正常</a-menu-item>
              <a-menu-item key="1.25">1.25x</a-menu-item>
              <a-menu-item key="1.5">1.5x 快速</a-menu-item>
              <a-menu-item key="2.0">2.0x 超快</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

        <!-- 下载按钮 -->
        <a-button
          type="text"
          @click="downloadAudio"
          class="control-button"
          title="下载音频"
        >
          <DownloadOutlined />
        </a-button>

        <!-- 关闭按钮 -->
        <a-button
          type="text"
          @click="closePlayer"
          class="control-button close-button"
          title="关闭播放器"
        >
          <CloseOutlined />
        </a-button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="audioStore.error" class="error-banner">
      <ExclamationCircleOutlined />
      {{ audioStore.error }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SoundOutlined,
  CustomerServiceOutlined,
  MutedOutlined,
  DownloadOutlined,
  CloseOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import { useAudioPlayerStore } from '@/stores/audioPlayer'

// Store
const audioStore = useAudioPlayerStore()

// 计算属性
const getTypeLabel = (type) => {
  const labels = {
    chapter: '章节音频',
    project: '完整音频',
    segment: '段落音频',
    library: '音频文件',
    voice_preview: '声音试听',
    custom: '自定义音频'
  }
  return labels[type] || '音频'
}

// 方法
const togglePlay = () => {
  if (audioStore.isPlaying) {
    audioStore.pause()
  } else {
    audioStore.resume()
  }
}

const stopPlay = () => {
  audioStore.stop()
}

const closePlayer = () => {
  audioStore.cleanup()
}

const onProgressChange = (value) => {
  audioStore.seekTo(value)
}

const onVolumeChange = (value) => {
  audioStore.setVolume(value / 100)
}

const onSpeedChange = ({ key }) => {
  audioStore.setPlaybackRate(parseFloat(key))
}

const downloadAudio = async () => {
  if (!audioStore.currentAudio?.url) {
    message.warning('没有可下载的音频')
    return
  }

  try {
    // 如果是blob URL，直接下载
    if (audioStore.currentAudio.url.startsWith('blob:')) {
      const link = document.createElement('a')
      link.href = audioStore.currentAudio.url
      link.download = `${audioStore.currentAudio.title}.wav`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      message.success('下载开始')
      return
    }

    // 对于API URL，通过fetch下载
    const response = await fetch(audioStore.currentAudio.url)
    if (!response.ok) {
      throw new Error('下载失败')
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${audioStore.currentAudio.title}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    message.success('下载成功')
  } catch (error) {
    console.error('下载音频失败:', error)
    message.error('下载失败: ' + error.message)
  }
}
</script>

<style scoped>
.global-audio-player {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top: 1px solid #f0f0f0;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transition: all 0.3s ease;
}

.player-container {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 16px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 音频信息 */
.audio-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 200px;
  flex-shrink: 0;
}

.audio-icon {
  width: 40px;
  height: 40px;
  background: #f0f0f0;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1890ff;
  font-size: 18px;
}

.audio-details {
  flex: 1;
  min-width: 0;
}

.audio-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.audio-type {
  font-size: 12px;
  color: #666;
}

/* 播放控制 */
.player-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.control-button {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.play-button {
  width: 44px;
  height: 44px;
  font-size: 20px;
  color: #1890ff;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
}

.play-button:hover {
  background: #d9f7be;
  border-color: #95de64;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 200px;
}

.time-text {
  font-size: 11px;
  color: #666;
  font-family: monospace;
  min-width: 35px;
  text-align: center;
}

.progress-slider {
  flex: 1;
  margin: 0 !important;
}

/* 扩展控制 */
.extended-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.close-button {
  color: #ff4d4f;
}

.close-button:hover {
  background: #fff2f0;
  border-color: #ffccc7;
}

/* 音量控制 */
.volume-control {
  padding: 8px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 错误横幅 */
.error-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  background: #fff2f0;
  border-top: 1px solid #ffccc7;
  color: #ff4d4f;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .player-container {
    padding: 8px 12px;
    gap: 12px;
  }

  .audio-info {
    min-width: 150px;
  }

  .audio-title {
    font-size: 13px;
  }

  .progress-container {
    min-width: 150px;
    gap: 8px;
  }

  .extended-controls {
    gap: 4px;
  }

  .control-button {
    width: 32px;
    height: 32px;
  }

  .play-button {
    width: 40px;
    height: 40px;
    font-size: 18px;
  }
}

@media (max-width: 480px) {
  .audio-info {
    min-width: 120px;
  }

  .audio-details {
    display: none;
  }

  .progress-container {
    min-width: 120px;
  }

  .time-text {
    font-size: 10px;
    min-width: 30px;
  }
}

/* 动画效果 */
.global-audio-player {
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* 播放器激活状态 */
.global-audio-player.playing {
  border-top-color: #1890ff;
}

/* 加载状态 */
.control-button :deep(.ant-btn-loading-icon) {
  color: #1890ff;
}
</style> 