<template>
  <div class="music-preview">
    <div class="preview-header">
      <div class="preview-info">
        <h4 class="music-title">{{ musicInfo.title || '背景音乐' }}</h4>
        <div class="music-meta">
          <span class="meta-item">时长: {{ formatDuration(musicInfo.duration) }}</span>
          <span class="meta-item">风格: {{ musicInfo.style }}</span>
          <span class="meta-item">音量: {{ musicInfo.volume }}dB</span>
        </div>
      </div>
      <div class="preview-actions">
        <a-button-group>
          <a-button @click="togglePlay" :loading="loading">
            <template #icon>
              <PlayCircleOutlined v-if="!isPlaying" />
              <PauseCircleOutlined v-else />
            </template>
            {{ isPlaying ? '暂停' : '播放' }}
          </a-button>
          <a-button @click="downloadMusic">
            <template #icon>
              <DownloadOutlined />
            </template>
            下载
          </a-button>
          <a-button @click="$emit('edit')" type="dashed">
            <template #icon>
              <EditOutlined />
            </template>
            编辑
          </a-button>
        </a-button-group>
      </div>
    </div>

    <!-- 音频波形显示 -->
    <div class="audio-player">
      <audio
        ref="audioElement"
        :src="musicInfo.audioUrl"
        @loadedmetadata="onAudioLoaded"
        @timeupdate="onTimeUpdate"
        @ended="onAudioEnded"
        @error="onAudioError"
        preload="metadata"
      />

      <!-- 自定义播放器控件 -->
      <div class="player-controls">
        <div class="progress-container">
          <div class="time-display">{{ formatTime(currentTime) }}</div>
          <div class="progress-bar" @click="seekTo">
            <div class="progress-track" ref="progressTrack">
              <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
              <div
                class="progress-handle"
                :style="{ left: progressPercentage + '%' }"
                @mousedown="startDrag"
              ></div>
            </div>
          </div>
          <div class="time-display">{{ formatTime(duration) }}</div>
        </div>

        <div class="volume-control">
          <a-slider
            v-model:value="volume"
            :min="0"
            :max="100"
            :tooltip-formatter="(val) => `${val}%`"
            @change="onVolumeChange"
            style="width: 100px"
          />
        </div>
      </div>
    </div>

    <!-- 音乐信息详情 -->
    <div class="music-details" v-if="showDetails">
      <a-collapse ghost>
        <a-collapse-panel key="scene" header="🎭 场景分析">
          <div class="scene-info">
            <div class="scene-tags">
              <a-tag color="purple">{{ sceneAnalysis.sceneType }}</a-tag>
              <a-tag color="blue">{{ sceneAnalysis.emotionTone }}</a-tag>
              <a-tag color="green">强度: {{ (sceneAnalysis.intensity * 100).toFixed(0) }}%</a-tag>
            </div>
            <div class="keywords" v-if="sceneAnalysis.keywords?.length">
              <span class="keywords-label">关键词:</span>
              <a-tag v-for="keyword in sceneAnalysis.keywords" :key="keyword" size="small">
                {{ keyword }}
              </a-tag>
            </div>
          </div>
        </a-collapse-panel>

        <a-collapse-panel key="config" header="⚙️ 音频配置">
          <div class="config-info">
            <div class="config-grid">
              <div class="config-item">
                <span class="label">采样率:</span>
                <span class="value">{{ musicConfig.sampleRate || '44.1kHz' }}</span>
              </div>
              <div class="config-item">
                <span class="label">比特率:</span>
                <span class="value">{{ musicConfig.bitRate || '320kbps' }}</span>
              </div>
              <div class="config-item">
                <span class="label">声道:</span>
                <span class="value">{{ musicConfig.channels || '立体声' }}</span>
              </div>
              <div class="config-item">
                <span class="label">格式:</span>
                <span class="value">{{ musicConfig.format || 'WAV' }}</span>
              </div>
            </div>
          </div>
        </a-collapse-panel>
      </a-collapse>
    </div>

    <!-- 快速操作 -->
    <div class="quick-actions">
      <a-space>
        <a-button size="small" @click="showDetails = !showDetails">
          {{ showDetails ? '隐藏详情' : '显示详情' }}
        </a-button>
        <a-button size="small" @click="$emit('regenerate')" type="dashed"> 重新生成 </a-button>
        <a-button size="small" @click="$emit('apply')" type="primary"> 应用到章节 </a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, onUnmounted } from 'vue'
  import { message } from 'ant-design-vue'
  import {
    PlayCircleOutlined,
    PauseCircleOutlined,
    DownloadOutlined,
    EditOutlined
  } from '@ant-design/icons-vue'

  // Props
  const props = defineProps({
    musicInfo: {
      type: Object,
      required: true,
      default: () => ({
        title: '',
        duration: 0,
        style: '',
        volume: 0,
        audioUrl: ''
      })
    },
    sceneAnalysis: {
      type: Object,
      default: () => ({
        sceneType: '',
        emotionTone: '',
        intensity: 0,
        keywords: []
      })
    },
    musicConfig: {
      type: Object,
      default: () => ({})
    }
  })

  // Emits
  const emit = defineEmits(['edit', 'regenerate', 'apply'])

  // 响应式数据
  const audioElement = ref(null)
  const progressTrack = ref(null)
  const isPlaying = ref(false)
  const loading = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const volume = ref(70)
  const showDetails = ref(false)
  const isDragging = ref(false)

  // 计算属性
  const progressPercentage = computed(() => {
    if (duration.value === 0) return 0
    return (currentTime.value / duration.value) * 100
  })

  // 方法
  const formatDuration = (seconds) => {
    if (!seconds || seconds === 0) return '00:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const formatTime = (seconds) => {
    return formatDuration(seconds)
  }

  const togglePlay = async () => {
    if (!audioElement.value) return

    loading.value = true
    try {
      if (isPlaying.value) {
        audioElement.value.pause()
      } else {
        await audioElement.value.play()
      }
    } catch (error) {
      console.error('播放失败:', error)
      message.error('音频播放失败')
    } finally {
      loading.value = false
    }
  }

  const downloadMusic = () => {
    if (props.musicInfo.audioUrl) {
      const link = document.createElement('a')
      link.href = props.musicInfo.audioUrl
      link.download = `${props.musicInfo.title || 'background_music'}.wav`
      link.click()
      message.success('开始下载音乐文件')
    } else {
      message.error('音频文件不存在')
    }
  }

  const seekTo = (event) => {
    if (!audioElement.value || !progressTrack.value) return

    const rect = progressTrack.value.getBoundingClientRect()
    const percentage = (event.clientX - rect.left) / rect.width
    const newTime = percentage * duration.value

    audioElement.value.currentTime = newTime
    currentTime.value = newTime
  }

  const startDrag = (event) => {
    isDragging.value = true

    const handleMouseMove = (e) => {
      if (!isDragging.value || !progressTrack.value || !audioElement.value) return

      const rect = progressTrack.value.getBoundingClientRect()
      const percentage = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
      const newTime = percentage * duration.value

      audioElement.value.currentTime = newTime
      currentTime.value = newTime
    }

    const handleMouseUp = () => {
      isDragging.value = false
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  const onVolumeChange = (value) => {
    if (audioElement.value) {
      audioElement.value.volume = value / 100
    }
  }

  // 音频事件处理
  const onAudioLoaded = () => {
    if (audioElement.value) {
      duration.value = audioElement.value.duration
      audioElement.value.volume = volume.value / 100
    }
  }

  const onTimeUpdate = () => {
    if (audioElement.value && !isDragging.value) {
      currentTime.value = audioElement.value.currentTime
    }
  }

  const onAudioEnded = () => {
    isPlaying.value = false
    currentTime.value = 0
  }

  const onAudioError = (error) => {
    console.error('音频加载错误:', error)
    message.error('音频文件加载失败')
    loading.value = false
  }

  // 监听播放状态
  const handlePlayStateChange = () => {
    if (audioElement.value) {
      isPlaying.value = !audioElement.value.paused
    }
  }

  // 生命周期
  onMounted(() => {
    if (audioElement.value) {
      audioElement.value.addEventListener('play', handlePlayStateChange)
      audioElement.value.addEventListener('pause', handlePlayStateChange)
    }
  })

  onUnmounted(() => {
    if (audioElement.value) {
      audioElement.value.removeEventListener('play', handlePlayStateChange)
      audioElement.value.removeEventListener('pause', handlePlayStateChange)
    }
  })
</script>

<style scoped>
  .music-preview {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    overflow: hidden;
    background: #ffffff;
  }

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 16px;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
  }

  .preview-info h4.music-title {
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
  }

  .music-meta {
    display: flex;
    gap: 16px;
    font-size: 13px;
    color: #6b7280;
  }

  .audio-player {
    padding: 16px;
  }

  .player-controls {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 12px;
  }

  .progress-container {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .time-display {
    font-size: 12px;
    color: #6b7280;
    min-width: 40px;
  }

  .progress-bar {
    flex: 1;
    cursor: pointer;
  }

  .progress-track {
    position: relative;
    height: 4px;
    background: #e5e7eb;
    border-radius: 2px;
  }

  .progress-fill {
    height: 100%;
    background: #1890ff;
    border-radius: 2px;
    transition: width 0.1s ease;
  }

  .progress-handle {
    position: absolute;
    top: -4px;
    width: 12px;
    height: 12px;
    background: #1890ff;
    border-radius: 50%;
    transform: translateX(-50%);
    cursor: pointer;
    transition: left 0.1s ease;
  }

  .progress-handle:hover {
    background: #40a9ff;
    transform: translateX(-50%) scale(1.2);
  }

  .volume-control {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .music-details {
    border-top: 1px solid #e5e7eb;
  }

  .scene-info {
    padding: 8px 0;
  }

  .scene-tags {
    margin-bottom: 12px;
  }

  .keywords {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .keywords-label {
    font-size: 13px;
    color: #6b7280;
  }

  .config-info {
    padding: 8px 0;
  }

  .config-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
  }

  .config-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 12px;
    background: #f8fafc;
    border-radius: 4px;
  }

  .config-item .label {
    font-size: 13px;
    color: #6b7280;
  }

  .config-item .value {
    font-size: 13px;
    font-weight: 500;
    color: #1f2937;
  }

  .quick-actions {
    padding: 12px 16px;
    background: #f8fafc;
    border-top: 1px solid #e5e7eb;
  }

  /* 暗黑模式适配 */
  [data-theme='dark'] .music-preview {
    background: #1f1f1f;
    border-color: #434343;
  }

  [data-theme='dark'] .preview-header {
    background: #2a2a2a;
    border-bottom-color: #434343;
  }

  [data-theme='dark'] .music-title {
    color: #ffffff !important;
  }

  [data-theme='dark'] .music-meta {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .time-display {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .progress-track {
    background: #434343;
  }

  [data-theme='dark'] .config-item {
    background: #2a2a2a;
  }

  [data-theme='dark'] .config-item .value {
    color: #ffffff;
  }

  [data-theme='dark'] .quick-actions {
    background: #2a2a2a;
    border-top-color: #434343;
  }

  [data-theme='dark'] .music-details {
    border-top-color: #434343;
  }
</style>
