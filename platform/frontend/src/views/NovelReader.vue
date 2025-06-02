<template>
  <div class="novel-reader-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 700;">
          智能多角色朗读
        </h1>
        <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
          上传小说文本，自动识别角色对话，分配声音并生成多角色朗读音频
        </p>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <div class="stat-number">{{ processedChapters }}</div>
          <div class="stat-label">已处理章节</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ totalCharacters }}</div>
          <div class="stat-label">角色数量</div>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧：小说上传和配置 -->
      <div class="config-panel">
        <!-- 文本上传 -->
        <a-card title="小说文本上传" :bordered="false" class="upload-card">
          <div class="upload-section">
            <a-upload-dragger
              v-model:fileList="novelFiles"
              :multiple="false"
              :before-upload="beforeNovelUpload"
              @change="handleNovelChange"
              accept=".txt,.doc,.docx"
              class="novel-upload"
            >
              <div class="upload-content">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="#06b6d4" style="margin-bottom: 16px;">
                  <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
                </svg>
                <p style="font-size: 16px; color: #374151; margin: 0;">点击或拖拽小说文件到此区域</p>
                <p style="font-size: 14px; color: #9ca3af; margin: 8px 0 0 0;">支持 TXT, DOC, DOCX 格式</p>
              </div>
            </a-upload-dragger>

            <!-- 或者直接粘贴文本 -->
            <a-divider>或</a-divider>
            
            <a-textarea
              v-model:value="directText"
              placeholder="直接粘贴小说文本内容..."
              :rows="8"
              :maxlength="50000"
              show-count
              class="direct-input"
            />
          </div>
        </a-card>

        <!-- 角色声音分配 -->
        <a-card title="角色声音分配" :bordered="false" class="character-assign-card">
          <template #extra>
            <a-button type="text" @click="autoAssignVoices" :loading="autoAssigning">
              <template #icon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </template>
              智能分配
            </a-button>
          </template>

          <div class="character-list">
            <div v-if="detectedCharacters.length === 0" class="empty-characters">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="#d1d5db" style="margin-bottom: 16px;">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
              <p style="color: #6b7280; margin: 0;">上传小说后将自动识别角色</p>
            </div>

            <div v-else class="character-items">
              <div 
                v-for="character in detectedCharacters" 
                :key="character.id"
                class="character-item"
              >
                <div class="character-info">
                  <div class="character-avatar" :style="{ background: character.color }">
                    {{ character.name.charAt(0) }}
                  </div>
                  <div class="character-details">
                    <div class="character-name">{{ character.name }}</div>
                    <div class="character-lines">对话数量: {{ character.lineCount }}</div>
                  </div>
                </div>

                <div class="voice-selector">
                  <a-select
                    v-model:value="character.voiceId"
                    placeholder="选择声音"
                    style="width: 140px;"
                    size="small"
                    @change="updateCharacterVoice(character.id, $event)"
                  >
                    <a-select-option
                      v-for="voice in availableVoices"
                      :key="voice.id"
                      :value="voice.id"
                    >
                      {{ voice.name }}
                    </a-select-option>
                  </a-select>
                  
                  <a-button 
                    type="text" 
                    size="small" 
                    @click="testCharacterVoice(character)"
                    :disabled="!character.voiceId"
                  >
                    <template #icon>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
                      </svg>
                    </template>
                  </a-button>
                </div>
              </div>
            </div>
          </div>
        </a-card>

        <!-- 生成设置 -->
        <a-card title="朗读设置" :bordered="false" class="settings-card">
          <div class="setting-item">
            <label class="setting-label">分段方式</label>
            <a-radio-group v-model:value="segmentMode" size="small">
              <a-radio-button value="paragraph">按段落</a-radio-button>
              <a-radio-button value="sentence">按句子</a-radio-button>
              <a-radio-button value="chapter">按章节</a-radio-button>
            </a-radio-group>
          </div>

          <div class="setting-item">
            <label class="setting-label">朗读速度</label>
            <a-slider v-model:value="readingSpeed" :min="0.5" :max="2.0" :step="0.1" />
            <div class="setting-value">{{ readingSpeed }}x</div>
          </div>

          <div class="setting-item">
            <label class="setting-label">背景音乐</label>
            <a-switch v-model:checked="enableBgMusic" />
          </div>
        </a-card>
      </div>

      <!-- 右侧：进度和控制 -->
      <div class="control-panel">
        <!-- 处理进度 -->
        <a-card title="处理进度" :bordered="false" class="progress-card">
          <div class="progress-section">
            <div class="progress-info">
              <div class="progress-status">
                <span class="status-text">{{ progressStatus }}</span>
                <span class="progress-percent">{{ Math.round(overallProgress) }}%</span>
              </div>
              <a-progress :percent="overallProgress" :show-info="false" />
            </div>

            <div class="progress-details">
              <div class="detail-item">
                <span class="detail-label">文本分析:</span>
                <span class="detail-status" :class="{ 'completed': analysisCompleted }">
                  {{ analysisCompleted ? '完成' : '等待中' }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">角色识别:</span>
                <span class="detail-status" :class="{ 'completed': characterDetected }">
                  {{ characterDetected ? '完成' : '等待中' }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">语音生成:</span>
                <span class="detail-status" :class="{ 'completed': voiceGenerated }">
                  {{ voiceGenerated ? '完成' : '进行中' }}
                </span>
              </div>
            </div>
          </div>

          <div class="control-buttons">
            <a-button 
              type="primary" 
              size="large" 
              block
              @click="startProcessing"
              :loading="isProcessing"
              :disabled="!canProcess"
            >
              <template #icon v-if="!isProcessing">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
                </svg>
              </template>
              {{ isProcessing ? '处理中...' : '开始生成' }}
            </a-button>

            <div class="control-actions" v-if="isProcessing">
              <a-button @click="pauseProcessing" style="flex: 1;">暂停</a-button>
              <a-button @click="stopProcessing" danger style="flex: 1;">停止</a-button>
            </div>
          </div>
        </a-card>

        <!-- 音频播放器 -->
        <a-card v-if="generatedAudios.length > 0" title="生成的音频" :bordered="false" class="audio-card">
          <div class="audio-list">
            <div 
              v-for="(audio, index) in generatedAudios" 
              :key="audio.id"
              class="audio-item"
              :class="{ 'playing': currentPlaying === index }"
            >
              <div class="audio-info">
                <div class="audio-title">第{{ index + 1 }}段</div>
                <div class="audio-meta">
                  {{ audio.duration }} | {{ audio.characters.join(', ') }}
                </div>
              </div>

              <div class="audio-controls">
                <a-button 
                  type="text" 
                  size="small" 
                  @click="playAudio(index)"
                  :icon="currentPlaying === index ? 'PauseOutlined' : 'PlayOutlined'"
                />
                <a-button 
                  type="text" 
                  size="small" 
                  @click="downloadAudio(audio)"
                >
                  <template #icon>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
                    </svg>
                  </template>
                </a-button>
              </div>
            </div>
          </div>

          <div class="batch-actions">
            <a-button block @click="downloadAll">
              <template #icon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
                </svg>
              </template>
              下载全部音频
            </a-button>
          </div>
        </a-card>

        <!-- 处理队列 -->
        <a-card v-if="processingQueue.length > 0" title="处理队列" :bordered="false" class="queue-card">
          <div class="queue-list">
            <div 
              v-for="(item, index) in processingQueue" 
              :key="item.id"
              class="queue-item"
            >
              <div class="queue-info">
                <div class="queue-text">{{ item.text.substring(0, 30) }}...</div>
                <div class="queue-character">{{ item.character }}</div>
              </div>
              <div class="queue-status">
                <a-tag :color="getQueueStatusColor(item.status)">
                  {{ getQueueStatusText(item.status) }}
                </a-tag>
              </div>
            </div>
          </div>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { message } from 'ant-design-vue'

// 响应式数据
const novelFiles = ref([])
const directText = ref('')
const detectedCharacters = ref([])
const segmentMode = ref('paragraph')
const readingSpeed = ref(1.0)
const enableBgMusic = ref(false)
const isProcessing = ref(false)
const autoAssigning = ref(false)
const overallProgress = ref(0)
const progressStatus = ref('等待开始')
const currentPlaying = ref(-1)
const analysisCompleted = ref(false)
const characterDetected = ref(false)
const voiceGenerated = ref(false)

// 模拟数据
const availableVoices = ref([
  { id: 1, name: '温柔女声', type: 'female' },
  { id: 2, name: '磁性男声', type: 'male' },
  { id: 3, name: '童声', type: 'child' },
  { id: 4, name: '专业主播', type: 'female' },
  { id: 5, name: '老者声音', type: 'male' }
])

const generatedAudios = ref([])
const processingQueue = ref([])

// 计算属性
const processedChapters = computed(() => generatedAudios.value.length)
const totalCharacters = computed(() => detectedCharacters.value.length)

const canProcess = computed(() => {
  const hasText = directText.value.trim() || novelFiles.value.length > 0
  const hasAssignments = detectedCharacters.value.every(char => char.voiceId)
  return hasText && hasAssignments && !isProcessing.value
})

// 方法
const beforeNovelUpload = (file) => {
  const isValidFormat = ['text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)
  if (!isValidFormat) {
    message.error('请上传 TXT, DOC, 或 DOCX 格式的文件！')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('文件大小不能超过 10MB！')
    return false
  }
  
  return false // 阻止自动上传
}

const handleNovelChange = async (info) => {
  if (info.fileList.length > 0) {
    const file = info.fileList[0].originFileObj
    // 模拟文件读取和角色识别
    await analyzeNovel(file)
  }
}

const analyzeNovel = async (file) => {
  analysisCompleted.value = false
  characterDetected.value = false
  
  message.loading('正在分析小说内容...', 2)
  
  // 模拟分析过程
  await new Promise(resolve => setTimeout(resolve, 2000))
  analysisCompleted.value = true
  
  // 模拟角色识别
  detectedCharacters.value = [
    {
      id: 1,
      name: '林清雅',
      lineCount: 45,
      color: '#06b6d4',
      voiceId: null,
      gender: 'female'
    },
    {
      id: 2,
      name: '张浩然',
      lineCount: 38,
      color: '#06b6d4',
      voiceId: null,
      gender: 'male'
    },
    {
      id: 3,
      name: '旁白',
      lineCount: 120,
      color: '#6b7280',
      voiceId: null,
      gender: 'neutral'
    }
  ]
  
  characterDetected.value = true
  message.success('角色识别完成，发现 ' + detectedCharacters.value.length + ' 个角色')
}

const autoAssignVoices = async () => {
  autoAssigning.value = true
  
  try {
    // 智能分配逻辑
    detectedCharacters.value.forEach(character => {
      if (character.gender === 'female') {
        character.voiceId = availableVoices.value.find(v => v.type === 'female')?.id
      } else if (character.gender === 'male') {
        character.voiceId = availableVoices.value.find(v => v.type === 'male')?.id
      } else {
        character.voiceId = availableVoices.value[0]?.id
      }
    })
    
    await new Promise(resolve => setTimeout(resolve, 1000))
    message.success('智能分配完成')
  } finally {
    autoAssigning.value = false
  }
}

const updateCharacterVoice = (characterId, voiceId) => {
  const character = detectedCharacters.value.find(c => c.id === characterId)
  if (character) {
    character.voiceId = voiceId
  }
}

const testCharacterVoice = (character) => {
  const voice = availableVoices.value.find(v => v.id === character.voiceId)
  message.success(`试听 ${character.name} 的声音：${voice?.name}`)
}

const startProcessing = async () => {
  isProcessing.value = true
  voiceGenerated.value = false
  overallProgress.value = 0
  progressStatus.value = '开始处理...'
  
  try {
    // 模拟处理过程
    const segments = [
      { text: '林清雅看着远山，心中有些忧虑...', character: '旁白' },
      { text: '浩然，你真的要离开吗？', character: '林清雅' },
      { text: '清雅，我必须去完成这个任务...', character: '张浩然' }
    ]
    
    // 创建处理队列
    processingQueue.value = segments.map((seg, index) => ({
      id: index + 1,
      text: seg.text,
      character: seg.character,
      status: 'waiting'
    }))
    
    // 逐个处理
    for (let i = 0; i < segments.length; i++) {
      processingQueue.value[i].status = 'processing'
      progressStatus.value = `处理第 ${i + 1} 段...`
      
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      processingQueue.value[i].status = 'completed'
      overallProgress.value = ((i + 1) / segments.length) * 100
      
      // 添加到生成的音频列表
      generatedAudios.value.push({
        id: i + 1,
        duration: '00:' + String(15 + i * 5).padStart(2, '0'),
        characters: [segments[i].character],
        url: '/audio/generated_' + (i + 1) + '.wav'
      })
    }
    
    voiceGenerated.value = true
    progressStatus.value = '处理完成'
    message.success('多角色朗读生成完成！')
    
  } catch (error) {
    message.error('处理失败：' + error.message)
  } finally {
    isProcessing.value = false
  }
}

const pauseProcessing = () => {
  message.info('已暂停处理')
}

const stopProcessing = () => {
  isProcessing.value = false
  processingQueue.value = []
  overallProgress.value = 0
  progressStatus.value = '已停止'
  message.info('已停止处理')
}

const playAudio = (index) => {
  if (currentPlaying.value === index) {
    currentPlaying.value = -1
    message.info('已暂停播放')
  } else {
    currentPlaying.value = index
    message.success(`播放第 ${index + 1} 段音频`)
  }
}

const downloadAudio = (audio) => {
  message.success(`下载音频：第${audio.id}段`)
}

const downloadAll = () => {
  message.success('开始下载全部音频文件')
}

const getQueueStatusColor = (status) => {
  const colors = {
    'waiting': 'default',
    'processing': 'processing',
    'completed': 'success',
    'error': 'error'
  }
  return colors[status] || 'default'
}

const getQueueStatusText = (status) => {
  const texts = {
    'waiting': '等待',
    'processing': '处理中',
    'completed': '完成',
    'error': '错误'
  }
  return texts[status] || '未知'
}
</script>

<style scoped>
.novel-reader-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 32px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  border-radius: 16px;
  color: white;
}

.header-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
}

.upload-card, .character-assign-card, .settings-card, .progress-card, .audio-card, .queue-card {
  margin-bottom: 24px;
  border-radius: 12px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
  border: none !important;
}

.novel-upload {
  border-radius: 12px !important;
  border-color: #d1d5db !important;
  background: #f9fafb !important;
}

.upload-content {
  padding: 32px;
  text-align: center;
}

.direct-input {
  border-radius: 8px !important;
  border-color: #d1d5db !important;
}

.empty-characters {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.character-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.character-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.3s;
}

.character-item:hover {
  border-color: #06b6d4;
  background: #f0f9ff;
}

.character-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.character-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.character-details {
  display: flex;
  flex-direction: column;
}

.character-name {
  font-weight: 500;
  color: #374151;
}

.character-lines {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.voice-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.setting-item {
  margin-bottom: 24px;
}

.setting-label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.setting-value {
  text-align: center;
  font-weight: 600;
  color: #06b6d4;
  font-size: 14px;
  margin-top: 8px;
}

.progress-section {
  margin-bottom: 24px;
}

.progress-info {
  margin-bottom: 16px;
}

.progress-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.status-text {
  color: #374151;
  font-weight: 500;
}

.progress-percent {
  color: #06b6d4;
  font-weight: 600;
}

.progress-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.detail-label {
  color: #6b7280;
}

.detail-status {
  color: #9ca3af;
}

.detail-status.completed {
  color: #10b981;
  font-weight: 500;
}

.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-actions {
  display: flex;
  gap: 12px;
}

.audio-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.audio-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.3s;
}

.audio-item:hover {
  border-color: #06b6d4;
  background: #f0f9ff;
}

.audio-item.playing {
  border-color: #10b981;
  background: #f0fdf4;
}

.audio-info {
  flex: 1;
}

.audio-title {
  font-weight: 500;
  color: #374151;
}

.audio-meta {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.audio-controls {
  display: flex;
  gap: 8px;
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  background: #f8fafc;
}

.queue-info {
  flex: 1;
}

.queue-text {
  font-size: 12px;
  color: #374151;
  margin-bottom: 2px;
}

.queue-character {
  font-size: 11px;
  color: #6b7280;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .header-stats {
    gap: 16px;
  }
  
  .stat-number {
    font-size: 24px;
  }
}
</style>