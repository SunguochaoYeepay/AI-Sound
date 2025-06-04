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
            
            <!-- 分析文本按钮 -->
            <div v-if="directText.trim()" style="margin-top: 16px; text-align: center;">
              <a-button 
                type="primary" 
                @click="analyzeDirectText"
                :loading="analysisCompleted === false && progressStatus !== '等待开始'"
                :disabled="!directText.trim()"
              >
                <template #icon>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                  </svg>
                </template>
                分析文本内容
              </a-button>
            </div>
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
import { ref, computed, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { readerAPI, charactersAPI } from '@/api'

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

// 项目相关数据
const currentProject = ref(null)
const projectId = ref(null)

// 声音库数据
const availableVoices = ref([])

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

// 初始化加载声音库
onMounted(async () => {
  await loadVoiceProfiles()
})

// 加载声音库列表
const loadVoiceProfiles = async () => {
  try {
    const response = await charactersAPI.getVoiceProfiles()
    if (response.data.success) {
      availableVoices.value = response.data.data.map(profile => ({
        id: profile.id,
        name: profile.name,
        type: profile.voice_type || 'neutral'
      }))
    }
  } catch (error) {
    console.error('加载声音库失败:', error)
    // 使用默认声音库作为后备
    availableVoices.value = [
      { id: 1, name: '温柔女声', type: 'female' },
      { id: 2, name: '磁性男声', type: 'male' },
      { id: 3, name: '童声', type: 'child' },
      { id: 4, name: '专业主播', type: 'female' },
      { id: 5, name: '老者声音', type: 'male' }
    ]
  }
}

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
    await analyzeNovel(file)
  }
}

const analyzeNovel = async (file) => {
  analysisCompleted.value = false
  characterDetected.value = false
  progressStatus.value = '正在分析小说内容...'
  
  try {
    message.loading('正在分析小说内容...', 2)
    
    // 创建项目 - 添加时间戳避免重复名称
    const timestamp = new Date().toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit', 
      hour: '2-digit',
      minute: '2-digit'
    }).replace(/\//g, '').replace(/:/g, '').replace(' ', '-')
    
    const baseName = file.name.replace(/\.[^/.]+$/, '') // 移除文件扩展名
    const projectName = `${baseName}_${timestamp}`
    
    const projectData = {
      name: projectName,
      description: '智能多角色朗读项目',
      text_file: file,
      character_mapping: {}
    }
    
    const response = await readerAPI.createProject(projectData)
    
    if (response.data.success) {
      currentProject.value = response.data.data
      projectId.value = response.data.data.id
      analysisCompleted.value = true
      
      // 获取项目详情，包含分段和角色信息
      await loadProjectDetail()
      
      message.success('文本分析完成')
    } else {
      throw new Error(response.data.message || '项目创建失败')
    }
    
  } catch (error) {
    console.error('分析小说失败:', error)
    
    // 改善错误处理
    let errorMessage = '未知错误'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
      
      // 特殊处理重复名称错误
      if (errorMessage.includes('项目名称已存在')) {
        errorMessage = '项目名称重复，请稍后再试或换个文件名'
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    message.error('分析失败: ' + errorMessage)
    
    // 重置状态
    analysisCompleted.value = false
    characterDetected.value = false
    progressStatus.value = '等待开始'
  }
}

const loadProjectDetail = async () => {
  if (!projectId.value) return
  
  try {
    const response = await readerAPI.getProjectDetail(projectId.value)
    
    if (response.data.success) {
      const project = response.data.data
      currentProject.value = project
      
      // 提取角色信息
      const characterMapping = project.character_mapping || {}
      const segments = project.segments || []
      
      console.log('[DEBUG] 项目段落数据:', segments)
      console.log('[DEBUG] 角色映射数据:', characterMapping)
      
      // 添加详细的段落调试信息
      console.log('[DEBUG] 段落详细信息:')
      segments.forEach((segment, index) => {
        console.log(`  段落${index + 1}:`, {
          segmentOrder: segment.segmentOrder || segment.segment_order,
          textContent: segment.textContent || segment.text_content,
          speaker: segment.speaker,
          detectedSpeaker: segment.detectedSpeaker || segment.detected_speaker,
          originalSegment: segment
        })
      })
      
      // 从文本段落中识别角色 - 兼容多种字段名
      const characterSet = new Set()
      const allSpeakers = new Set() // 记录所有说话人，包括旁白
      
      segments.forEach(segment => {
        // 兼容多种字段名格式
        const speaker = segment.speaker || segment.detectedSpeaker || segment.detected_speaker
        
        console.log(`[DEBUG] 段落${segment.segmentOrder || segment.segment_order}: speaker='${speaker}'`)
        
        if (speaker) {
          allSpeakers.add(speaker)
          // 只有非旁白角色才加入角色集合
          if (speaker !== 'narrator' && speaker !== '旁白') {
            characterSet.add(speaker)
          }
        }
      })
      
      console.log('[DEBUG] 所有说话人（包括旁白）:', Array.from(allSpeakers))
      console.log('[DEBUG] 识别出的角色（排除旁白）:', Array.from(characterSet))
      
      // 构建角色列表
      detectedCharacters.value = Array.from(characterSet).map((charName, index) => ({
        id: index + 1,
        name: charName,
        lineCount: segments.filter(s => {
          const speaker = s.speaker || s.detectedSpeaker || s.detected_speaker
          return speaker === charName
        }).length,
        color: getCharacterColor(index),
        voiceId: characterMapping[charName] || null,
        gender: inferGender(charName)
      }))
      
      // 添加旁白角色（如果存在旁白段落）
      const narratorCount = segments.filter(s => {
        const speaker = s.speaker || s.detectedSpeaker || s.detected_speaker
        return speaker === 'narrator' || speaker === '旁白'
      }).length
      
      console.log('[DEBUG] 旁白段落数量:', narratorCount)
      
      if (narratorCount > 0) {
        detectedCharacters.value.unshift({
          id: 0,
          name: '旁白',
          lineCount: narratorCount,
          color: '#6b7280',
          voiceId: characterMapping['旁白'] || characterMapping['narrator'] || null,
          gender: 'neutral'
        })
      }
      
      characterDetected.value = true
      console.log('[DEBUG] 最终角色列表:', detectedCharacters.value)
      
      // 改进提示信息
      if (detectedCharacters.value.length === 0) {
        console.warn('[DEBUG] 没有识别出任何角色')
        message.warning('未识别出任何角色。可能原因：\n1. 文本内容太简单，没有明显的对话\n2. 缺少对话标记（如：小明说："..."）\n3. 建议使用包含角色对话的文本')
      } else if (detectedCharacters.value.length === 1 && detectedCharacters.value[0].name === '旁白') {
        message.info(`只识别出旁白角色。如果文本包含对话，请确保使用以下格式：\n• 小明说："你好"\n• 小红："很高兴见到你"\n• "真不错！"张老师说`)
      } else {
        message.success(`角色识别完成，发现 ${detectedCharacters.value.length} 个角色`)
      }
    }
    
  } catch (error) {
    console.error('获取项目详情失败:', error)
    message.error('获取项目详情失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 辅助函数
const getCharacterColor = (index) => {
  const colors = ['#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#f97316']
  return colors[index % colors.length]
}

const inferGender = (name) => {
  // 简单的性别推断逻辑
  const femaleIndicators = ['雅', '柔', '婷', '娜', '丽', '美', '小姐', '女士']
  const maleIndicators = ['浩', '强', '明', '军', '刚', '先生', '男士', '少爷']
  
  const lowerName = name.toLowerCase()
  if (femaleIndicators.some(indicator => lowerName.includes(indicator))) {
    return 'female'
  }
  if (maleIndicators.some(indicator => lowerName.includes(indicator))) {
    return 'male'
  }
  return 'neutral'
}

const autoAssignVoices = async () => {
  autoAssigning.value = true
  
  try {
    // 检查是否有角色
    if (detectedCharacters.value.length === 0) {
      message.warning('没有识别出任何角色，请先上传包含对话的文本')
      return
    }
    
    // 检查是否有可用声音
    if (availableVoices.value.length === 0) {
      message.error('没有可用的声音档案，请先在声音库管理中上传声音文件')
      return
    }
    
    console.log('[DEBUG] 开始智能分配')
    console.log('[DEBUG] 检测到的角色:', detectedCharacters.value)
    console.log('[DEBUG] 可用声音:', availableVoices.value)
    
    // 智能分配逻辑
    const femaleVoices = availableVoices.value.filter(v => v.type === 'female')
    const maleVoices = availableVoices.value.filter(v => v.type === 'male')
    const neutralVoices = availableVoices.value.filter(v => v.type === 'neutral' || v.type === 'child')
    
    console.log('[DEBUG] 声音分类 - 女声:', femaleVoices.length, '男声:', maleVoices.length, '中性:', neutralVoices.length)
    
    let femaleIndex = 0, maleIndex = 0, neutralIndex = 0
    let assignedCount = 0
    
    detectedCharacters.value.forEach(character => {
      if (character.gender === 'female' && femaleVoices.length > 0) {
        character.voiceId = femaleVoices[femaleIndex % femaleVoices.length].id
        femaleIndex++
        assignedCount++
        console.log(`[DEBUG] ${character.name} (女性) -> ${femaleVoices[(femaleIndex - 1) % femaleVoices.length].name}`)
      } else if (character.gender === 'male' && maleVoices.length > 0) {
        character.voiceId = maleVoices[maleIndex % maleVoices.length].id
        maleIndex++
        assignedCount++
        console.log(`[DEBUG] ${character.name} (男性) -> ${maleVoices[(maleIndex - 1) % maleVoices.length].name}`)
      } else if (neutralVoices.length > 0) {
        character.voiceId = neutralVoices[neutralIndex % neutralVoices.length].id
        neutralIndex++
        assignedCount++
        console.log(`[DEBUG] ${character.name} (中性) -> ${neutralVoices[(neutralIndex - 1) % neutralVoices.length].name}`)
      } else if (availableVoices.value.length > 0) {
        character.voiceId = availableVoices.value[0]?.id
        assignedCount++
        console.log(`[DEBUG] ${character.name} (兜底) -> ${availableVoices.value[0]?.name}`)
      }
    })
    
    console.log(`[DEBUG] 分配完成，共分配 ${assignedCount} 个角色`)
    
    // 更新项目的角色映射
    await updateCharacterMapping()
    
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    if (assignedCount > 0) {
      message.success(`智能分配完成，已为 ${assignedCount} 个角色分配声音`)
    } else {
      message.warning('智能分配失败，请手动为角色选择声音')
    }
    
  } catch (error) {
    console.error('智能分配失败:', error)
    message.error('智能分配失败: ' + (error.message || '未知错误'))
  } finally {
    autoAssigning.value = false
  }
}

const updateCharacterMapping = async () => {
  if (!projectId.value) return
  
  try {
    const characterMapping = {}
    detectedCharacters.value.forEach(character => {
      if (character.voiceId) {
        const voiceName = character.name === '旁白' ? 'narrator' : character.name
        characterMapping[voiceName] = character.voiceId
      }
    })
    
    await readerAPI.updateProject(projectId.value, {
      name: currentProject.value.name,
      description: currentProject.value.description,
      character_mapping: characterMapping
    })
    
  } catch (error) {
    console.error('更新角色映射失败:', error)
  }
}

const updateCharacterVoice = async (characterId, voiceId) => {
  const character = detectedCharacters.value.find(c => c.id === characterId)
  if (character) {
    character.voiceId = voiceId
    await updateCharacterMapping()
  }
}

const testCharacterVoice = async (character) => {
  const voice = availableVoices.value.find(v => v.id === character.voiceId)
  if (!voice) {
    message.error('请先选择声音')
    return
  }
  
  try {
    message.loading('正在生成测试音频...')
    
    // 使用声音库进行测试合成
    const testData = {
      text: `你好，我是${character.name}，这是声音测试。`,
      time_step: 32,
      p_weight: 1.4,
      t_weight: 3.0
    }
    
    const response = await charactersAPI.testVoiceSynthesis(character.voiceId, testData)
    
    if (response.data.success) {
      // 播放测试音频 - 修复：使用blob方式
      console.log('[DEBUG] 音频URL:', response.data.audioUrl)
      
      try {
        // 尝试直接播放
        const audio = new Audio(response.data.audioUrl)
        
        // 添加错误处理
        audio.addEventListener('error', async (e) => {
          console.error('[DEBUG] 直接播放失败，尝试fetch方式:', e)
          
          // 如果直接播放失败，尝试fetch + blob方式
          try {
            const audioResponse = await fetch(response.data.audioUrl)
            if (!audioResponse.ok) {
              throw new Error(`HTTP ${audioResponse.status}: ${audioResponse.statusText}`)
            }
            
            const blob = await audioResponse.blob()
            console.log('[DEBUG] Blob信息:', blob.type, blob.size, 'bytes')
            
            const blobUrl = URL.createObjectURL(blob)
            const blobAudio = new Audio(blobUrl)
            
            blobAudio.addEventListener('error', (blobError) => {
              console.error('[DEBUG] Blob播放也失败:', blobError)
              message.error('音频格式不支持，可能是编码问题')
              URL.revokeObjectURL(blobUrl)
            })
            
            blobAudio.addEventListener('canplay', () => {
              console.log('[DEBUG] Blob音频可以播放')
              message.success(`试听 ${character.name} 的声音：${voice.name}`)
            })
            
            blobAudio.addEventListener('ended', () => {
              URL.revokeObjectURL(blobUrl)
            })
            
            await blobAudio.play()
            
          } catch (fetchError) {
            console.error('[DEBUG] Fetch失败:', fetchError)
            message.error('音频加载失败: ' + fetchError.message)
          }
        })
        
        audio.addEventListener('loadstart', () => {
          console.log('[DEBUG] 开始加载音频')
        })
        
        audio.addEventListener('canplay', () => {
          console.log('[DEBUG] 音频可以播放')
          message.success(`试听 ${character.name} 的声音：${voice.name}`)
        })
        
        // 尝试播放
        await audio.play()
        
      } catch (error) {
        console.error('[DEBUG] 播放失败:', error)
        message.error('播放失败: ' + error.message)
      }
    } else {
      throw new Error(response.data.message || '测试失败')
    }
    
  } catch (error) {
    console.error('测试声音失败:', error)
    message.error('测试失败: ' + (error.response?.data?.detail || error.message))
  }
}

const startProcessing = async () => {
  if (!projectId.value) {
    message.error('请先上传小说文件')
    return
  }
  
  if (!canProcess.value) {
    message.error('请确保已上传文件并分配所有角色声音')
    return
  }
  
  isProcessing.value = true
  voiceGenerated.value = false
  overallProgress.value = 0
  progressStatus.value = '开始处理...'
  
  try {
    // 开始音频生成 - 改为单任务处理，避免CUDA内存溢出
    const response = await readerAPI.startGeneration(projectId.value, 1)
    
    if (response.data.success) {
      message.success('开始生成多角色朗读音频')
      
      // 启动进度监控
      monitorProgress()
    } else {
      throw new Error(response.data.message || '启动失败')
    }
    
  } catch (error) {
    console.error('启动处理失败:', error)
    message.error('启动失败: ' + (error.response?.data?.detail || error.message))
    isProcessing.value = false
  }
}

const monitorProgress = async () => {
  if (!projectId.value || !isProcessing.value) return
  
  try {
    const response = await readerAPI.getProgress(projectId.value)
    
    if (response.data.success) {
      const progress = response.data.data
      console.log('[DEBUG] 进度数据:', progress) // 添加调试信息
      
      overallProgress.value = progress.progressPercent || progress.progress_percent || 0
      progressStatus.value = getProgressStatusText(progress)
      
      // 更新处理队列
      if (progress.recent_completed) {
        processingQueue.value = progress.recent_completed.map(segment => ({
          id: segment.id,
          text: segment.text.substring(0, 30) + '...',
          character: segment.speaker,
          status: 'completed'
        }))
      }
      
      // 检查是否完成
      if (progress.project_status === 'completed') {
        voiceGenerated.value = true
        progressStatus.value = '处理完成'
        isProcessing.value = false
        message.success('多角色朗读生成完成！')
        
        // 加载生成的音频列表
        await loadGeneratedAudios()
      } else if (progress.project_status === 'failed') {
        isProcessing.value = false
        progressStatus.value = '处理失败'
        message.error('处理失败，请检查日志')
      } else {
        // 继续监控
        setTimeout(monitorProgress, 2000)
      }
    }
    
  } catch (error) {
    console.error('获取进度失败:', error)
    setTimeout(monitorProgress, 5000) // 出错时延长间隔
  }
}

const getProgressStatusText = (progress) => {
  const total = progress.statistics?.total || 0
  const completed = progress.statistics?.completed || 0
  const processing = progress.statistics?.processing || 0
  
  if (processing > 0) {
    return `处理中... (${completed}/${total})`
  } else if (completed === total && total > 0) {
    return '处理完成'
  } else {
    return `等待处理... (${completed}/${total})`
  }
}

const loadGeneratedAudios = async () => {
  // 这里可以添加获取生成音频列表的逻辑
  // 暂时使用模拟数据
  generatedAudios.value = [
    {
      id: 1,
      duration: '03:45',
      characters: ['旁白', '林清雅'],
      url: '/audio/segment_1.wav'
    }
  ]
}

const pauseProcessing = async () => {
  if (!projectId.value) return
  
  try {
    await readerAPI.pauseGeneration(projectId.value)
    message.info('已暂停处理')
  } catch (error) {
    message.error('暂停失败: ' + (error.response?.data?.detail || error.message))
  }
}

const stopProcessing = async () => {
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

const downloadAll = async () => {
  if (!projectId.value) {
    message.error('没有可下载的项目')
    return
  }
  
  try {
    const response = await readerAPI.downloadAudio(projectId.value)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${currentProject.value?.name || '朗读项目'}_final.wav`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    message.success('开始下载全部音频文件')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败: ' + (error.response?.data?.detail || error.message))
  }
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

const analyzeDirectText = async () => {
  if (!directText.value.trim()) {
    message.error('请先输入文本内容')
    return
  }
  
  analysisCompleted.value = false
  characterDetected.value = false
  progressStatus.value = '正在分析小说内容...'
  
  try {
    message.loading('正在分析文本内容...', 2)
    
    // 创建项目 - 添加时间戳避免重复名称
    const timestamp = new Date().toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit', 
      hour: '2-digit',
      minute: '2-digit'
    }).replace(/\//g, '').replace(/:/g, '').replace(' ', '-')
    
    const projectName = `直接输入文本_${timestamp}`
    
    const projectData = {
      name: projectName,
      description: '智能多角色朗读项目',
      text_content: directText.value.trim(),
      character_mapping: {}
    }
    
    const response = await readerAPI.createProject(projectData)
    
    if (response.data.success) {
      currentProject.value = response.data.data
      projectId.value = response.data.data.id
      analysisCompleted.value = true
      
      // 获取项目详情，包含分段和角色信息
      await loadProjectDetail()
      
      message.success('文本分析完成')
    } else {
      throw new Error(response.data.message || '项目创建失败')
    }
    
  } catch (error) {
    console.error('分析文本失败:', error)
    
    // 改善错误处理
    let errorMessage = '未知错误'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
      
      // 特殊处理重复名称错误
      if (errorMessage.includes('项目名称已存在')) {
        errorMessage = '项目名称重复，请稍后再试'
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    message.error('分析失败: ' + errorMessage)
    
    // 重置状态
    analysisCompleted.value = false
    characterDetected.value = false
    progressStatus.value = '等待开始'
  }
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