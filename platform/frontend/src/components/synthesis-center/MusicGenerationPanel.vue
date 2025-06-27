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
            description="音乐生成需要消耗大量计算资源，单次生成可能需要5-15分钟，请耐心等待。为避免系统过载，暂时不支持批量生成功能。"
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

        <!-- 高级选项已简化 - 移除复杂的智能分析功能 -->
        <!-- 只保留基本的音乐生成功能，不进行场景分析和风格推荐 -->
      </div>

      <!-- 生成结果 -->
      <div v-if="generationResult" class="generation-result">
        <h4>生成结果</h4>
        <div class="result-card">
          <div class="result-header">
            <div class="result-info">
              <h5>{{ generationResult.music_info?.title || '背景音乐' }}</h5>
              <div class="result-meta">
                <span>时长: {{ generationResult.music_info?.duration }}秒</span>
                <span>风格: {{ generationResult.scene_analysis?.scene_type }}</span>
                <span>音量: {{ generationResult.music_config?.volume_level }}dB</span>
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

          <!-- 音频波形显示 -->
          <div class="audio-waveform" v-if="generationResult.music_info?.audio_url">
            <audio
              ref="audioPlayer"
              :src="generationResult.music_info.audio_url"
              @loadedmetadata="onAudioLoaded"
              @timeupdate="onTimeUpdate"
              @ended="onAudioEnded"
              style="width: 100%; margin-top: 8px;"
              controls
            />
          </div>

          <!-- 场景分析信息 -->
          <div class="scene-analysis" v-if="generationResult.scene_analysis">
            <h6>场景分析</h6>
            <div class="analysis-tags">
              <a-tag color="purple">{{ generationResult.scene_analysis.scene_type }}</a-tag>
              <a-tag color="blue">{{ generationResult.scene_analysis.emotion_tone }}</a-tag>
              <a-tag color="green">强度: {{ (generationResult.scene_analysis.intensity * 100).toFixed(0) }}%</a-tag>
            </div>
            <div class="keywords" v-if="generationResult.scene_analysis.keywords?.length">
              <span class="keywords-label">关键词:</span>
              <a-tag
                v-for="keyword in generationResult.scene_analysis.keywords"
                :key="keyword"
                size="small"
              >
                {{ keyword }}
              </a-tag>
            </div>
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

    <!-- 生成进度模态框 -->
    <a-modal
      v-model:open="progressModalVisible"
      title="音乐生成进度"
      :closable="false"
      :maskClosable="false"
      :footer="null"
      width="500px"
    >
      <div class="generation-progress">
        <div class="progress-info">
          <h4>正在生成背景音乐...</h4>
          <p>{{ progressMessage }}</p>
        </div>
        
        <a-progress
          :percent="generationProgress"
          :status="progressStatus"
          :stroke-color="progressColor"
        />
        
        <div class="progress-details">
          <div class="detail-item">
            <span class="label">当前阶段:</span>
            <span class="value">{{ currentStage }}</span>
          </div>
          <div class="detail-item">
            <span class="label">预计剩余:</span>
            <span class="value">{{ estimatedTimeLeft }}</span>
          </div>
        </div>

        <div class="progress-actions">
          <a-button @click="cancelGeneration" :loading="cancelling">
            取消生成
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  SoundOutlined,
  EyeOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'
import { musicGenerationAPI } from '@/api'

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
// const supportedStyles = ref([])  // 移除智能风格推荐
// const stylesLoading = ref(false)

// 生成相关状态
const generating = ref(false)
const generationResult = ref(null)
const currentTaskId = ref(null)

// 音频播放状态
const playing = ref(false)
const audioPlayer = ref(null)

// 预览相关已移除 - 智能功能简化
// const previewing = ref(false)
// const stylePreview = ref(null)

// 进度相关
const progressModalVisible = ref(false)
const generationProgress = ref(0)
const progressMessage = ref('')
const currentStage = ref('')
const estimatedTimeLeft = ref('')
const cancelling = ref(false)

// 面板状态已简化
// const advancedPanelActive = ref([])  // 移除高级选项面板

// 生成选项 - 只保留基本设置
const quickOptions = ref({
  volumeLevel: -12,
  targetDuration: 30
})

// 高级选项已移除 - 简化功能
// const advancedOptions = ref({
//   customStyle: null,
//   fadeIn: 2.0,
//   fadeOut: 2.0
// })

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
  // 估算：每分钟约300字
  return Math.ceil(props.chapterContent.length / 300)
})

const progressStatus = computed(() => {
  if (generationProgress.value === 100) return 'success'
  if (cancelling.value) return 'exception'
  return 'active'
})

const progressColor = computed(() => {
  if (progressStatus.value === 'success') return '#52c41a'
  if (progressStatus.value === 'exception') return '#ff4d4f'
  return '#1890ff'
})

// 方法
const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

const getSelectedChapterInfo = () => {
  return props.chapters.find(c => c.id === props.selectedChapter)
}

const refreshServiceStatus = async () => {
  statusLoading.value = true
  try {
    const response = await musicGenerationAPI.healthCheck()
    if (response.data.status === 'healthy') {
      serviceStatus.value = 'healthy'
      serviceInfo.value = response.data.service_info || {}
    } else if (response.data.status === 'degraded') {
      serviceStatus.value = 'degraded'
      serviceInfo.value = response.data.service_info || {}
    } else {
      serviceStatus.value = 'unhealthy'
    }
  } catch (error) {
    console.error('服务状态检查失败:', error)
    serviceStatus.value = 'unhealthy'
    message.error('无法连接到音乐生成服务')
  } finally {
    statusLoading.value = false
  }
}

// 智能风格相关方法已移除 - 功能简化
// const loadSupportedStyles = async () => {
//   // 风格推荐功能已移除
// }
//
// const handleStylePreview = async () => {
//   // 风格预览功能已移除
// }
//
// const selectCustomStyle = (style) => {
//   // 自定义风格选择功能已移除
// }

const handleQuickGenerate = async () => {
  await generateMusic({
    chapter_id: props.selectedChapter,
    content: props.chapterContent,
    duration: quickOptions.value.targetDuration,  // target_duration -> duration
    volume_level: quickOptions.value.volumeLevel
  })
}

// 高级生成已移除 - 只保留基本生成功能
// const handleAdvancedGenerate = async () => {
//   // 高级生成功能已移除，只保留基本生成
// }

const generateMusic = async (requestData) => {
  generating.value = true
  progressModalVisible.value = true
  generationProgress.value = 0
  progressMessage.value = '正在初始化音乐生成...'
  currentStage.value = '准备阶段'
  estimatedTimeLeft.value = '约5-15分钟'  // 音乐生成耗时很长，增加预期时间
  
  emit('generationStarted')
  
  try {
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (generationProgress.value < 90) {
        generationProgress.value += Math.random() * 10
        updateProgressMessage()
      }
    }, 2000)
    
    const response = await musicGenerationAPI.generateChapterMusic(requestData)
    
    clearInterval(progressInterval)
    generationProgress.value = 100
    progressMessage.value = '音乐生成完成！'
    currentStage.value = '完成'
    estimatedTimeLeft.value = '0秒'
    
    setTimeout(() => {
      progressModalVisible.value = false
      generationResult.value = response.data
      emit('musicGenerated', response.data)
      emit('generationCompleted', response.data)
      message.success('背景音乐生成完成！')
    }, 1000)
    
  } catch (error) {
    console.error('音乐生成失败:', error)
    progressModalVisible.value = false
    message.error('音乐生成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generating.value = false
  }
}

const updateProgressMessage = () => {
  const messages = [
    '正在分析章节内容...',
    '正在识别情感基调...',
    '正在选择音乐风格...',
    '正在生成音乐片段... (这个过程需要较长时间，请耐心等待)',
    '正在进行音频后处理...',
    '正在优化音质... (即将完成)',
    '正在保存文件...'
  ]
  
  const stages = [
    '内容分析',
    '情感识别', 
    '风格选择',
    '音乐生成中',
    '音频处理',
    '质量优化',
    '文件保存'
  ]
  
  const index = Math.floor(generationProgress.value / 12)  // 调整进度划分，给生成阶段更多时间
  if (index < messages.length) {
    progressMessage.value = messages[index]
    currentStage.value = stages[index]
    
    // 在音乐生成阶段更新预期时间
    if (index === 3) {
      estimatedTimeLeft.value = '约10-15分钟'
    } else if (index >= 4) {
      estimatedTimeLeft.value = '约1-3分钟'
    }
  }
}

const cancelGeneration = async () => {
  cancelling.value = true
  try {
    if (currentTaskId.value) {
      // 这里可以调用取消API
      // await musicGenerationAPI.cancelTask(currentTaskId.value)
    }
    progressModalVisible.value = false
    generating.value = false
    message.info('已取消音乐生成')
  } catch (error) {
    console.error('取消生成失败:', error)
    message.error('取消失败')
  } finally {
    cancelling.value = false
  }
}

const playGeneratedMusic = () => {
  if (!audioPlayer.value) return
  
  if (playing.value) {
    audioPlayer.value.pause()
    playing.value = false
  } else {
    audioPlayer.value.play()
    playing.value = true
  }
}

const downloadGeneratedMusic = () => {
  if (generationResult.value?.music_info?.audio_url) {
    const link = document.createElement('a')
    link.href = generationResult.value.music_info.audio_url
    link.download = `background_music_chapter_${props.selectedChapter}.wav`
    link.click()
  }
}

const onAudioLoaded = () => {
  // 音频加载完成
}

const onTimeUpdate = () => {
  // 音频播放时间更新
}

const onAudioEnded = () => {
  playing.value = false
}

// 监听器 - 简化
watch(() => props.selectedChapter, () => {
  // 章节切换时清除之前的结果
  generationResult.value = null
  // stylePreview.value = null  // 风格预览功能已移除
})

// 生命周期
onMounted(() => {
  refreshServiceStatus()
})
</script>

<style scoped>
.music-generation-panel {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f6f8fa 0%, #e8f4f8 100%);
}

.header-left h3.panel-title {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.panel-description {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
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
  display: inline-block;
}

.status-dot.status-healthy {
  background: #52c41a;
}

.status-dot.status-degraded {
  background: #faad14;
}

.status-dot.status-unhealthy {
  background: #ff4d4f;
}

.status-dot.status-unknown {
  background: #d9d9d9;
}

.status-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #8c8c8c;
}

.panel-content {
  padding: 24px;
}

.chapter-info {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 4px solid #1890ff;
}

.chapter-info h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.chapter-title {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
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

.quick-generation {
  margin-bottom: 16px;
}

.quick-generation h4 {
  margin: 0 0 4px 0;
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
  margin-bottom: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.option-group:last-child {
  margin-bottom: 0;
}

.option-group label {
  width: 80px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.value-display {
  min-width: 50px;
  font-size: 13px;
  color: #6b7280;
}

.style-preview-section,
.custom-style-section,
.audio-params-section {
  margin-bottom: 16px;
}

.style-preview-section h5,
.custom-style-section h5,
.audio-params-section h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.preview-result {
  margin-top: 12px;
}

.preview-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 6px;
  margin-bottom: 12px;
}

.style-info h6 {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.style-details {
  display: flex;
  gap: 8px;
}

.confidence-score {
  text-align: center;
}

.confidence-score .score {
  display: block;
  font-size: 20px;
  font-weight: bold;
  color: #1890ff;
}

.confidence-score .label {
  font-size: 12px;
  color: #6b7280;
}

.style-recommendations h6 {
  margin: 0 0 8px 0;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.recommendation-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.param-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-item label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
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

.scene-analysis {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  background: #fafafa;
}

.scene-analysis h6 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.analysis-tags {
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

.generation-progress {
  padding: 8px 0;
}

.progress-info {
  text-align: center;
  margin-bottom: 24px;
}

.progress-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #1f2937;
}

.progress-info p {
  margin: 0;
  color: #6b7280;
}

.progress-details {
  margin: 16px 0 24px 0;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-item .label {
  font-size: 13px;
  color: #6b7280;
}

.detail-item .value {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.progress-actions {
  text-align: center;
}

/* 暗黑模式适配 */
[data-theme="dark"] .music-generation-panel {
  background: #1f1f1f;
}

[data-theme="dark"] .panel-header {
  background: linear-gradient(135deg, #2a2a2a 0%, #1a1a2e 100%);
  border-bottom-color: #434343;
}

[data-theme="dark"] .panel-title {
  color: #ffffff !important;
}

[data-theme="dark"] .panel-description {
  color: #8c8c8c !important;
}

[data-theme="dark"] .service-status {
  border-bottom-color: #434343;
}

[data-theme="dark"] .chapter-info {
  background: #2a2a2a;
  border-left-color: #1890ff;
}

[data-theme="dark"] .quick-options {
  background: #2a2a2a;
}

[data-theme="dark"] .result-card {
  border-color: #434343;
}

[data-theme="dark"] .result-header {
  background: #2a2a2a;
  border-bottom-color: #434343;
}

[data-theme="dark"] .scene-analysis {
  background: #2a2a2a;
  border-top-color: #434343;
}
</style> 