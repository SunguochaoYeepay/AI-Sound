<template>
  <div class="music-generation-panel">
    <!-- 面板头部 -->
    <div class="panel-header">
      <div class="header-left">
        <h3 class="panel-title">
          🎵 背景音乐生成
        </h3>
        <p class="panel-description">
          为当前章节生成背景音乐 (基于简单设置)
        </p>
      </div>
      <div class="header-right">
        <a-button 
          type="text" 
          size="small"
          @click="refreshServiceStatus"
          :loading="statusLoading"
        >
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新状态
        </a-button>
      </div>
    </div>

    <!-- 服务状态指示器 -->
    <div class="service-status" :class="serviceStatusClass">
      <div class="status-indicator">
        <span class="status-dot" :class="serviceStatusClass"></span>
        <span class="status-text">{{ serviceStatusText }}</span>
      </div>
      <div class="status-details" v-if="serviceInfo">
        <span class="detail-item">SongGeneration {{ serviceInfo.version || 'v1.0' }}</span>
        <span class="detail-item">{{ serviceInfo.uptime || '运行中' }}</span>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="panel-content" v-if="serviceStatus === 'healthy'">
      <!-- 章节信息 -->
      <div class="chapter-info" v-if="selectedChapter && chapterContent">
        <h4>当前章节</h4>
        <div class="chapter-details">
          <div class="chapter-title">
            第{{ getSelectedChapterInfo()?.chapter_number }}章 {{ getSelectedChapterInfo()?.chapter_title || getSelectedChapterInfo()?.title }}
          </div>
          <div class="chapter-stats">
            <span>字数: {{ formatNumber(chapterContent.length) }}</span>
            <span>预计时长: {{ estimatedDuration }}分钟</span>
          </div>
        </div>
      </div>

      <!-- 音乐生成控制 -->
      <div class="generation-controls">
        <!-- 简单生成 -->
        <div class="quick-generation">
          <h4>生成背景音乐</h4>
          <p class="section-desc">根据基本设置生成背景音乐（不进行复杂分析）</p>
          
          <!-- 生成耗时警告 -->
          <a-alert 
            message="⏰ 重要提示" 
            description="音乐生成需要消耗大量计算资源，单次生成可能需要5-15分钟，请耐心等待。现已集成WebSocket实时进度监控。"
            type="warning" 
            show-icon 
            style="margin-bottom: 16px;"
          />
          
          <div class="quick-options">
            <div class="option-group">
              <label>音量等级</label>
              <a-slider
                v-model:value="quickOptions.volumeLevel"
                :min="-30"
                :max="0"
                :step="1"
                :tooltip-formatter="(val) => `${val}dB`"
                style="flex: 1; margin: 0 12px;"
              />
              <span class="value-display">{{ quickOptions.volumeLevel }}dB</span>
            </div>

            <div class="option-group">
              <label>目标时长</label>
              <a-input-number
                v-model:value="quickOptions.targetDuration"
                :min="10"
                :max="180"
                :step="10"
                addon-after="秒"
                style="width: 120px;"
              />
            </div>

            <div class="option-group">
              <label>音乐风格</label>
              <a-select v-model:value="quickOptions.genre" style="width: 200px;">
                <a-select-option value="Auto">自动选择</a-select-option>
                <a-select-option value="Pop">流行</a-select-option>
                <a-select-option value="R&B">R&B</a-select-option>
                <a-select-option value="Dance">舞曲</a-select-option>
                <a-select-option value="Rock">摇滚</a-select-option>
                <a-select-option value="Jazz">爵士</a-select-option>
              </a-select>
            </div>
          </div>

          <a-button
            type="primary"
            size="large"
            :loading="generating"
            :disabled="!canGenerate"
            @click="handleQuickGenerate"
            block
          >
            <template #icon>
              <SoundOutlined />
            </template>
            {{ generating ? '正在生成音乐...' : '生成背景音乐' }}
          </a-button>
        </div>
      </div>

      <!-- 实时进度显示 -->
      <div v-if="generating" class="progress-section">
        <a-divider />
        <div class="progress-info">
          <div class="progress-header">
            <span class="progress-title">🎵 音乐生成进度</span>
            <span class="progress-percent">{{ Math.round(generationProgress) }}%</span>
          </div>
          <a-progress
            :percent="generationProgress"
            :status="progressStatus"
            :stroke-color="progressColor"
            size="small"
          />
          <div class="progress-details">
            <div class="current-stage">{{ currentStage }}</div>
            <div class="task-info" v-if="currentTaskId">
              <a-tag color="blue">任务ID: {{ currentTaskId.slice(0, 8) }}...</a-tag>
              <a-tag v-if="elapsedTime" color="green">已用时: {{ formatTime(elapsedTime) }}</a-tag>
              <a-tag :color="connectionStatus === 'connected' ? 'green' : 'red'">
                {{ getConnectionStatusText() }}
              </a-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 生成结果 -->
      <div v-if="generationResult" class="generation-result">
        <h4>生成结果</h4>
        <div class="result-card">
          <div class="result-header">
            <div class="result-info">
              <h5>{{ generationResult.music_info?.title || '背景音乐' }}</h5>
              <div class="result-meta">
                <span>时长: {{ generationResult.music_info?.duration || quickOptions.targetDuration }}秒</span>
                <span>风格: {{ generationResult.final_style || quickOptions.genre }}</span>
                <span>音量: {{ quickOptions.volumeLevel }}dB</span>
              </div>
            </div>
            <div class="result-actions">
              <a-button-group>
                <a-button @click="playGeneratedMusic" :loading="playing">
                  <template #icon>
                    <PlayCircleOutlined v-if="!playing" />
                    <PauseCircleOutlined v-else />
                  </template>
                  {{ playing ? '暂停' : '播放' }}
                </a-button>
                <a-button @click="downloadGeneratedMusic">
                  <template #icon>
                    <DownloadOutlined />
                  </template>
                  下载
                </a-button>
              </a-button-group>
            </div>
          </div>

          <!-- 音频播放器 -->
          <div class="audio-waveform" v-if="audioUrl">
            <audio
              ref="audioPlayer"
              :src="audioUrl"
              @loadedmetadata="onAudioLoaded"
              @timeupdate="onTimeUpdate"
              @ended="onAudioEnded"
              style="width: 100%; margin-top: 8px;"
              controls
            />
          </div>

          <!-- 生成信息 -->
          <div v-if="generationResult.music_description" class="generation-info">
            <a-descriptions title="生成信息" bordered size="small">
              <a-descriptions-item label="音乐描述">
                {{ generationResult.music_description }}
              </a-descriptions-item>
              <a-descriptions-item label="使用风格">
                {{ generationResult.final_style || quickOptions.genre }}
              </a-descriptions-item>
              <a-descriptions-item label="生成耗时">
                {{ formatTime(generationResult.generation_time || 0) }}
              </a-descriptions-item>
            </a-descriptions>
          </div>
        </div>
      </div>
    </div>

    <!-- 服务不可用状态 -->
    <div v-else class="service-unavailable">
      <div class="unavailable-content">
        <div class="unavailable-icon">⚠️</div>
        <h4>音乐生成服务不可用</h4>
        <p>{{ serviceStatusText }}</p>
        <a-button type="primary" @click="refreshServiceStatus" :loading="statusLoading">
          重新检查
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  SoundOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'
import { musicGenerationAPI } from '@/api'
import { useWebSocket } from '@/composables/useWebSocketSimple'

// Props
const props = defineProps({
  selectedChapter: {
    type: [Number, String],
    default: null
  },
  chapterContent: {
    type: String,
    default: ''
  },
  chapters: {
    type: Array,
    default: () => []
  },
  project: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['musicGenerated', 'generationStarted', 'generationCompleted'])

// 响应式数据
const serviceStatus = ref('unknown') // healthy, degraded, unhealthy, unknown
const serviceInfo = ref(null)
const statusLoading = ref(false)

// 生成相关状态
const generating = ref(false)
const generationResult = ref(null)
const currentTaskId = ref(null)

// 音频播放状态
const playing = ref(false)
const audioPlayer = ref(null)

// 进度相关
const generationProgress = ref(0)
const currentStage = ref('')
const elapsedTime = ref(0)

// WebSocket连接
const { connect, disconnect, isConnected } = useWebSocket()
const connectionStatus = ref('disconnected')

// 生成选项
const quickOptions = ref({
  volumeLevel: -12,
  targetDuration: 30,
  genre: 'Auto'
})

let startTime = 0

// 计算属性
const serviceStatusClass = computed(() => {
  const statusMap = {
    'healthy': 'status-healthy',
    'degraded': 'status-degraded',
    'unhealthy': 'status-unhealthy',
    'unknown': 'status-unknown'
  }
  return statusMap[serviceStatus.value] || 'status-unknown'
})

const serviceStatusText = computed(() => {
  const textMap = {
    'healthy': '服务正常',
    'degraded': '服务降级',
    'unhealthy': '服务异常',
    'unknown': '状态未知'
  }
  return textMap[serviceStatus.value] || '检查中...'
})

const canGenerate = computed(() => {
  return serviceStatus.value === 'healthy' && 
         props.selectedChapter && 
         props.chapterContent && 
         !generating.value
})

const estimatedDuration = computed(() => {
  if (!props.chapterContent) return 0
  return Math.ceil(props.chapterContent.length / 300)
})

const progressStatus = computed(() => {
  if (generationProgress.value >= 100) return 'success'
  if (generationProgress.value < 0) return 'exception'
  return 'active'
})

const progressColor = computed(() => {
  if (progressStatus.value === 'success') return '#52c41a'
  if (progressStatus.value === 'exception') return '#ff4d4f'
  return '#1890ff'
})

const audioUrl = computed(() => {
  if (!generationResult.value?.result?.audio_url) return null
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return `${baseUrl}${generationResult.value.result.audio_url}`
})

// 方法
const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const getSelectedChapterInfo = () => {
  return props.chapters.find(c => c.id === props.selectedChapter)
}

const getConnectionStatusText = () => {
  const statusMap = {
    'connected': 'WebSocket已连接',
    'connecting': '正在连接...',
    'disconnected': '未连接',
    'error': '连接异常'
  }
  return statusMap[connectionStatus.value] || '未知状态'
}

const refreshServiceStatus = async () => {
  statusLoading.value = true
  try {
    const response = await musicGenerationAPI.healthCheck()
    if (response.data.status === 'healthy') {
      serviceStatus.value = 'healthy'
      serviceInfo.value = response.data.info || {}
    } else {
      serviceStatus.value = 'unhealthy'
      serviceInfo.value = null
    }
  } catch (error) {
    console.error('检查服务状态失败:', error)
    serviceStatus.value = 'unhealthy'
    serviceInfo.value = null
  } finally {
    statusLoading.value = false
  }
}

// 生成音乐主函数
const handleQuickGenerate = async () => {
  if (!canGenerate.value) {
    message.warning('请先选择章节并确保服务正常')
    return
  }

  try {
    generating.value = true
    generationProgress.value = 0
    currentStage.value = '正在启动音乐生成...'
    generationResult.value = null
    startTime = Date.now() / 1000
    
    // 连接WebSocket
    if (!isConnected.value) {
      connectionStatus.value = 'connecting'
      await connect()
      connectionStatus.value = isConnected.value ? 'connected' : 'error'
    }

    // 准备歌词（简化处理）
    const lyrics = generateLyricsFromContent(props.chapterContent)

    // 启动异步音乐生成任务
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const response = await fetch(`${baseUrl}/api/v1/music-generation-async/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        lyrics: lyrics,
        genre: quickOptions.value.genre,
        description: `为章节"${getSelectedChapterInfo()?.chapter_title || getSelectedChapterInfo()?.title}"生成的背景音乐`,
        cfg_coef: 1.5,
        temperature: 0.9,
        top_k: 50,
        volume_level: quickOptions.value.volumeLevel,
        target_duration: quickOptions.value.targetDuration
      })
    })

    if (!response.ok) {
      throw new Error(`启动任务失败: ${response.status}`)
    }

    const result = await response.json()
    currentTaskId.value = result.task_id
    
    console.log('🎵 异步音乐生成任务已启动:', result.task_id)
    message.info('音乐生成任务已启动，正在监控进度...')
    
    // 🔧 关键修复：任务启动后立即进入WebSocket监控模式，不再等待HTTP响应
    currentStage.value = '等待WebSocket进度更新...'
    generationProgress.value = 5
    
    emit('generationStarted', {
      taskId: result.task_id,
      chapter: getSelectedChapterInfo()
    })

  } catch (error) {
    console.error('启动音乐生成失败:', error)
    message.error(`启动失败: ${error.message}`)
    generating.value = false
  }
}

// 🔧 修复：符合SongGeneration格式要求的歌词生成
const generateLyricsFromContent = (content) => {
  // 简单提取内容的前几句作为歌词基础
  const sentences = content.split(/[。！？]/).filter(s => s.trim().length > 0)
  const selectedSentences = sentences.slice(0, 3) // 取前3句，避免过长
  
  // 🎵 修复歌词格式：必须使用小写标签且符合SongGeneration规范
  return `[verse]
${selectedSentences.join('\n')}

[chorus]
这是一段美妙的旋律
承载着故事的情感

[outro-short]`
}

// WebSocket消息处理
const handleWebSocketMessage = (message) => {
  try {
    const data = JSON.parse(message)
    
    if (data.type === 'music_generation_progress' && data.data.task_id === currentTaskId.value) {
      const progressData = data.data
      
      generationProgress.value = Math.round(progressData.progress * 100)
      currentStage.value = progressData.message || '处理中...'
      elapsedTime.value = Date.now() / 1000 - startTime
      
      console.log(`📊 进度更新: ${generationProgress.value}% - ${currentStage.value}`)
      
      if (progressData.status === 'completed' && progressData.result) {
        // 生成成功
        generationResult.value = progressData
        
        emit('musicGenerated', progressData)
        emit('generationCompleted', progressData)
        
        message.success('🎵 背景音乐生成完成！')
        generating.value = false
        
      } else if (progressData.status === 'failed') {
        // 生成失败
        console.error('音乐生成失败:', progressData.error)
        message.error(`生成失败: ${progressData.error || '未知错误'}`)
        generating.value = false
      }
    }
  } catch (error) {
    console.error('处理WebSocket消息失败:', error)
  }
}

// 音频控制
const playGeneratedMusic = () => {
  if (audioPlayer.value) {
    if (playing.value) {
      audioPlayer.value.pause()
    } else {
      audioPlayer.value.play()
    }
  }
}

const downloadGeneratedMusic = () => {
  if (audioUrl.value) {
    const link = document.createElement('a')
    link.href = audioUrl.value
    link.download = `generated_music_${Date.now()}.wav`
    link.click()
  }
}

const onAudioLoaded = () => {
  console.log('音频加载完成')
}

const onTimeUpdate = () => {
  // 时间更新处理
}

const onAudioEnded = () => {
  playing.value = false
}

// 生命周期
onMounted(async () => {
  try {
    // 检查服务状态
    await refreshServiceStatus()
    
    // 连接WebSocket
    connectionStatus.value = 'connecting'
    await connect()
    connectionStatus.value = isConnected.value ? 'connected' : 'error'
    
    // 监听WebSocket消息
    window.addEventListener('websocket_message', (event) => {
      handleWebSocketMessage(event.detail)
    })
    
  } catch (error) {
    console.error('初始化失败:', error)
    connectionStatus.value = 'error'
  }
})

onUnmounted(() => {
  disconnect()
  window.removeEventListener('websocket_message', handleWebSocketMessage)
})
</script>

<style scoped>
.music-generation-panel {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-left {
  flex: 1;
}

.panel-title {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.panel-description {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.header-right {
  margin-left: 16px;
}

.service-status {
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
}

.status-dot.status-healthy {
  background: #10b981;
}

.status-dot.status-degraded {
  background: #f59e0b;
}

.status-dot.status-unhealthy {
  background: #ef4444;
}

.status-text {
  font-size: 14px;
  font-weight: 500;
}

.status-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #6b7280;
}

.panel-content {
  padding: 24px;
}

.chapter-info {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 4px solid #667eea;
}

.chapter-info h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.chapter-title {
  font-size: 15px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.chapter-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
}

.generation-controls {
  margin-bottom: 24px;
}

.quick-generation h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.section-desc {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #6b7280;
}

.quick-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 6px;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.option-group label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  min-width: 80px;
}

.value-display {
  font-size: 13px;
  color: #6b7280;
  min-width: 50px;
}

.progress-section {
  margin-top: 16px;
}

.progress-info {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-title {
  font-weight: 500;
  color: #1890ff;
}

.progress-percent {
  font-weight: bold;
  font-size: 16px;
}

.progress-details {
  margin-top: 8px;
}

.current-stage {
  color: #666;
  margin-bottom: 8px;
}

.task-info {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.generation-result {
  border-top: 1px solid #f0f0f0;
  padding-top: 24px;
}

.generation-result h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.result-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.result-info h5 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.result-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
}

.audio-waveform {
  padding: 16px;
}

.generation-info {
  margin-top: 16px;
}

.service-unavailable {
  padding: 48px 24px;
  text-align: center;
}

.unavailable-content {
  max-width: 300px;
  margin: 0 auto;
}

.unavailable-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.unavailable-content h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #374151;
}

.unavailable-content p {
  margin: 0 0 16px 0;
  color: #6b7280;
}
</style>