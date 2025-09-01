<template>
  <div class="content-review-container">
    <!-- 进度监控 -->
    <ProgressMonitor :session-id="sessionId" @progress-update="handleProgressUpdate" />

    <!-- 章节选择器和分析控制 -->
    <div class="chapter-selector-container">
      <div class="chapter-controls">
        <a-select 
          v-model:value="selectedChapter" 
          placeholder="选择章节" 
          style="width: 300px;"
          :loading="chaptersLoading"
        >
          <a-select-option v-for="chapter in chapters" :key="chapter.chapter_id" :value="chapter.chapter_id.toString()">
            {{ chapter.chapter_title }}
          </a-select-option>
        </a-select>
        
        <!-- 章节分析状态和按钮 -->
        <div class="chapter-analysis-controls" v-if="selectedChapter">
          <div class="analysis-status">
            <a-tag :color="getChapterAnalysisStatusColor()">
              {{ getChapterAnalysisStatusText() }}
            </a-tag>
          </div>
          
          <!-- 分析按钮 -->
          <a-button 
            v-if="canAnalyzeChapter()"
            type="primary" 
            :loading="analyzingChapter"
            @click="analyzeCurrentChapter"
            size="small"
          >
            <template #icon>
              <PlayCircleOutlined />
            </template>
            分析此章节
          </a-button>
          
          <!-- 重新分析按钮 -->
          <a-button 
            v-if="canReanalyzeChapter()"
            type="default" 
            :loading="analyzingChapter"
            @click="analyzeCurrentChapter"
            size="small"
          >
            <template #icon>
              <ReloadOutlined />
            </template>
            重新分析
          </a-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-review-layout">
      <!-- 左侧：原始文本 -->
      <div class="original-text-panel">
        <div class="panel-header">
          <h3>📖 原始文本</h3>
        </div>
        
        <div v-if="loading" class="loading-container">
          <a-spin size="large" />
          <p>加载中...</p>
        </div>
        <div v-else-if="chapterContent" class="text-content">
          <div 
            v-for="(segment, index) in textSegments" 
            :key="index"
            class="text-segment"
            :class="{ 'highlighted': segment.highlighted }"
            :data-time="getSegmentTimeRange(index)"
            @click="highlightSegment(index)"
          >
            <div class="segment-header">
              <span class="segment-index">段落 {{ index + 1 }}</span>
              <span class="segment-time">{{ getSegmentTimeRange(index) }}</span>
            </div>
            <div class="segment-text">{{ segment.text }}</div>
            <div v-if="segment.issues && segment.issues.length > 0" class="segment-issues">
              <a-tag v-for="issue in segment.issues" :key="issue.type" :color="getIssueColor(issue.type)">
                {{ issue.message }}
              </a-tag>
            </div>
          </div>
        </div>
        <div v-else class="empty-content">
          <p>暂无内容</p>
        </div>
      </div>

      <!-- 右侧：剧本详情 -->
      <div class="script-panel">
        <div class="panel-header">
          <h3>📝 剧本详情</h3>
          <div class="panel-actions">
            <a-button 
              size="small" 
              @click="showIssuesDrawer = true"
              :disabled="detectedIssues.length === 0"
            >
              <template #icon>
                <ExclamationCircleOutlined />
              </template>
              问题 ({{ detectedIssues.length }})
            </a-button>
          </div>
        </div>

        <div class="script-content">
          <!-- 剧本详情 -->
          <div class="script-details">
            <div v-if="loading" class="loading-container">
              <a-spin size="large" />
              <p>加载中...</p>
            </div>
            <div v-else-if="scriptSegments.length > 0" class="script-segment-list">
              <div class="script-segment" v-for="(script, index) in scriptSegments" :key="index" :class="{ 'highlighted': script.highlighted }" @click="highlightSegment(index)">
                <div class="script-header">
                  <div class="script-time">{{ script.startTime }}-{{ script.endTime }}s</div>
                  <div class="script-type">
                    <a-tag :color="script.type === 'dialogue' ? 'blue' : 'green'">
                      {{ script.type === 'dialogue' ? '对话' : '旁白' }}
                    </a-tag>
                  </div>
                </div>
                
                <div class="script-content-main">
                  <!-- 说话者信息 -->
                  <div v-if="script.speaker && script.type === 'dialogue'" class="speaker-info">
                    <span class="speaker-label">🎭 {{ script.speaker }}</span>
                    <span v-if="script.character_id" class="character-id">(ID: {{ script.character_id }})</span>
                  </div>
                  
                  <!-- 剧本内容 -->
                  <div class="script-text">
                    <div class="text-content">{{ script.text }}</div>
                  </div>
                  
                  <!-- 关联卡片 -->
                  <div class="related-cards" v-if="getRelatedCards(script).length > 0">
                    <div class="cards-header">
                      <span class="cards-title">📋 关联卡片</span>
                      <span class="cards-count">({{ getRelatedCards(script).length }})</span>
                    </div>
                    <div class="cards-list">
                      <div 
                        v-for="card in (getRelatedCards(script) || [])" 
                        :key="card.type"
                        class="card-mini"
                        :class="`${card.type}-card`"
                        @click.stop="openCardDrawer(card.type, script)"
                      >
                        {{ card.icon }} {{ card.name }}
                      </div>
                    </div>
                  </div>
                  
                  <!-- 音频配置 -->
                  <div class="audio-config" v-if="showStoryboardView">
                    <div class="config-item">
                      <span class="config-label">🎤 语音:</span>
                      <span class="config-value">{{ script.voice_name || '未分配' }}</span>
                    </div>
                    <div class="config-item" v-if="script.audioElements?.ambient_sounds">
                      <span class="config-label">🔊 音效:</span>
                      <div class="config-tags">
                        <a-tag v-for="sound in script.audioElements.ambient_sounds" :key="sound" size="small" color="blue">
                          {{ sound }}
                        </a-tag>
                      </div>
                    </div>
                    <div class="config-item" v-if="script.audioElements?.background_music">
                      <span class="config-label">🎵 音乐:</span>
                      <span class="config-value">{{ script.audioElements.background_music }}</span>
                    </div>
                  </div>
                  
                  <!-- 问题标记 -->
                  <div v-if="script.issues && script.issues.length > 0" class="script-issues">
                    <a-tag v-for="issue in script.issues" :key="issue.type" :color="getIssueColor(issue.type)" size="small">
                      {{ issue.message }}
                    </a-tag>
                  </div>
                </div>
                

              </div>
            </div>
            <div v-else class="empty-content">
              <p>暂无剧本数据</p>
            </div>
          </div>


        </div>
      </div>
    </div>

    <!-- 卡片详情抽屉 -->
    <CardDetailDrawer 
      :open="cardDrawerVisible"
      :card="selectedCard"
      @update:visible="cardDrawerVisible = $event"
      @update="handleCardUpdate"
    />

    <!-- 问题抽屉 -->
    <a-drawer
      :open="showIssuesDrawer"
      title="🔍 检测到的问题"
      placement="right"
      width="400"
      :closable="true"
      @close="showIssuesDrawer = false"
    >
      <div class="issues-drawer-content">
        <div v-if="loading" class="loading-container">
          <a-spin size="large" />
          <p>加载中...</p>
        </div>
        <div v-else-if="detectedIssues.length > 0" class="issue-list">
          <div v-for="(issue, index) in detectedIssues" :key="index" class="issue-item">
            <div class="issue-header">
              <a-tag :color="getIssueColor(issue.type)">{{ issue.type }}</a-tag>
              <span class="issue-time">{{ issue.time }}</span>
            </div>
            <div class="issue-description">{{ issue.description }}</div>
          </div>
        </div>
        <div v-else class="empty-content">
          <p>暂无问题</p>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { 
  LoadingOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import CardDetailDrawer from './CardDetailDrawer.vue'
import ProgressMonitor from './ProgressMonitor.vue'
import { storyboardAPI } from '@/api/storyboard'

// Props
const props = defineProps({
  sessionId: {
    type: [String, Number],
    required: true
  },
  session: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['start-analysis', 'confirm-session', 'reanalyze-session'])

// 响应式数据
const cardDrawerVisible = ref(false)
const selectedCard = ref(null)
const selectedChapter = ref('1')

// 添加章节列表数据
const chapters = ref([])
const chaptersLoading = ref(false)

// 文本段落数据
const textSegments = ref([])
const chapterContent = ref('')
const reviewData = ref(null)
const loading = ref(false)

// 时间轴详情
const timelineDetails = ref([])

// 检测到的问题
const detectedIssues = ref([])

// 卡片存在状态
const hasStoryCard = ref(false)
const hasCharacterCard = ref(false)
const hasSceneCard = ref(false)
const hasEventCard = ref(false)
const hasEmotionCard = ref(false)

// 剧本详情
const scriptSegments = ref([])
const showStoryboardView = ref(false) // 控制分镜视图和剧本视图

// 章节分析状态
const analyzingChapter = ref(false)
const currentChapterStatus = ref('pending')

// 问题抽屉
const showIssuesDrawer = ref(false)

// 加载章节数据
const loadChapterData = async (chapterId) => {
  if (!props.sessionId || !chapterId) return
  
  loading.value = true
  try {
    const response = await storyboardAPI.getReviewData(props.sessionId, chapterId)
    console.log('API返回数据:', response.data)
    
    // 设置reviewData
    reviewData.value = response.data
    
    // 获取章节内容
    try {
      const chapterResponse = await storyboardAPI.getChapterDetail(chapterId)
      if (chapterResponse.data.success && chapterResponse.data.data) {
        const chapter = chapterResponse.data.data
        chapterContent.value = chapter.content || `第${chapter.chapter_number}章：${chapter.chapter_title}\n\n[章节内容加载中...]`
      } else {
        chapterContent.value = `第${chapterId}章\n\n[章节内容加载失败]`
      }
    } catch (error) {
      console.error('获取章节内容失败:', error)
      chapterContent.value = `第${chapterId}章\n\n[章节内容加载失败]`
    }
    
    // 处理音频剧本卡片数据，转换为剧本格式
    const scriptCards = response.data.cards?.audio_script || []
    if (scriptCards.length > 0) {
      const scriptCard = scriptCards[0]
      console.log('音频剧本卡内容:', scriptCard.content)
      
      // 确保script_segments是数组格式
      let segmentsData = scriptCard.content?.script_segments || []
      if (typeof segmentsData === 'string') {
        try {
          segmentsData = JSON.parse(segmentsData)
        } catch (e) {
          console.error('解析script_segments失败:', e)
          segmentsData = []
        }
      }
      
      // 转换为剧本格式
      scriptSegments.value = segmentsData.map((segment, index) => {
        // 从dialogue.content中提取对话内容
        let dialogueContent = []
        if (segment.dialogue && segment.dialogue.content) {
          if (Array.isArray(segment.dialogue.content)) {
            dialogueContent = segment.dialogue.content
          } else {
            dialogueContent = [{ content: segment.dialogue.content, speaker: segment.dialogue.speaker || '旁白' }]
          }
        }
        
        // 判断是对话还是旁白
        const isDialogue = dialogueContent.length > 0 && 
                          dialogueContent.some(item => item.content && item.content !== '对话内容')
        
        // 获取主要对话内容
        const mainDialogue = dialogueContent.find(item => item.content && item.content !== '对话内容') || 
                           dialogueContent[0] || 
                           { content: segment.original_text || '旁白内容', speaker: '旁白' }
        
        return {
          id: segment.segment_id || `script_${index}`,
          startTime: segment.start_time?.toString() || '0',
          endTime: segment.end_time?.toString() || '0',
          type: isDialogue ? 'dialogue' : 'narration',
          speaker: mainDialogue.speaker || segment.dialogue?.speaker || '旁白',
          text: mainDialogue.content || segment.original_text || '',
          originalText: segment.original_text || '', // 保存原文用于对比
          character_id: segment.character_id || null,
          voice_id: segment.dialogue?.voice_id || '',
          voice_name: segment.dialogue?.voice_id || '未分配',
          audioElements: segment.sound_effects || {},
          issues: [], // 问题标记
          highlighted: false
        }
      })
      
      console.log('处理后的剧本详情:', scriptSegments.value)
      console.log('scriptSegments.value长度:', scriptSegments.value.length)
      console.log('第一个剧本内容:', scriptSegments.value[0]?.text)
      
      // 同时保留时间轴详情用于分镜视图（从audio_storyboard获取）
      const audioCards = response.data.cards?.audio_storyboard || []
      if (audioCards.length > 0) {
        const audioCard = audioCards[0]
        let timeline = audioCard.content?.timeline || []
        if (typeof timeline === 'string') {
          try {
            timeline = JSON.parse(timeline)
          } catch (e) {
            console.error('解析timeline失败:', e)
            timeline = []
          }
        }
        
        timelineDetails.value = timeline.map((item, index) => ({
          startTime: item.start_time?.toString() || '0',
          endTime: item.end_time?.toString() || '0',
          type: item.audio_type === 'dialogue' ? '对话' : '旁白',
          text: item.content || '场景描述',
          audioElements: {},
          text_mapping: item.text_mapping || { paragraph_range: [index, index] }
        }))
      } else {
        timelineDetails.value = []
      }
    } else {
      scriptSegments.value = []
      timelineDetails.value = []
    }
    
    // 处理文本段落（基于章节内容自然分段）
    const paragraphs = chapterContent.value.split('\n').filter(p => p.trim())
    textSegments.value = paragraphs.map((paragraph, index) => ({
      text: paragraph,
      highlighted: false,
      issues: []
    }))
    
    // 设置卡片存在状态（包括书籍级卡片）
    hasStoryCard.value = !!(response.data.cards?.story && response.data.cards.story.length > 0)
    hasCharacterCard.value = !!(response.data.cards?.character && response.data.cards.character.length > 0)
    hasSceneCard.value = !!(response.data.cards?.scene && response.data.cards.scene.length > 0)
    hasEventCard.value = !!(response.data.cards?.event && response.data.cards.event.length > 0)
    hasEmotionCard.value = !!(response.data.cards?.emotion && response.data.cards.emotion.length > 0)
    
    // 处理检测到的问题（基于卡片数据）
    detectedIssues.value = []
    const allCards = Object.values(response.data.cards || {}).flat()
    allCards.forEach(card => {
      if (card.confidence_score < 0.8) {
        detectedIssues.value.push({
          type: 'quality',
          time: '00:00:00',
          description: `${card.card_type}卡片置信度较低: ${card.confidence_score}`
        })
      }
    })
    
    // 检测剧本问题
    detectScriptIssues()
    
    // 更新章节分析状态
    const hasScriptCards = (response.data.cards?.audio_script || []).length > 0
    currentChapterStatus.value = hasScriptCards ? 'completed' : 'pending'
    
  } catch (error) {
    console.error('加载章节数据失败:', error)
    message.error('加载章节数据失败')
  } finally {
    loading.value = false
  }
}

// 检测剧本问题
const detectScriptIssues = () => {
  // 检查剧本问题
  scriptSegments.value.forEach((script, index) => {
    const issues = []
    
    // 检查说话者是否为空
    if (script.type === 'dialogue' && !script.speaker) {
      issues.push({
        type: 'missing_speaker',
        message: '缺少说话者'
      })
    }
    
    // 检查语音是否分配
    if (!script.voice_name || script.voice_name === '未分配') {
      issues.push({
        type: 'missing_voice',
        message: '未分配语音'
      })
    }
    
    // 检查内容是否为空
    if (!script.text || script.text.trim() === '') {
      issues.push({
        type: 'empty_content',
        message: '内容为空'
      })
    }
    
    // 检查时间范围是否合理
    const startTime = parseInt(script.startTime)
    const endTime = parseInt(script.endTime)
    if (endTime <= startTime) {
      issues.push({
        type: 'invalid_time',
        message: '时间范围无效'
      })
    }
    
    // 将问题添加到剧本段
    script.issues = issues
    
    // 添加到检测到的问题列表
    issues.forEach(issue => {
      detectedIssues.value.push({
        type: issue.type,
        time: `${script.startTime}-${script.endTime}s`,
        description: `段落${index + 1}: ${issue.message}`,
        scriptIndex: index
      })
    })
  })
}

// 加载章节列表
const loadChapters = async () => {
  if (!props.sessionId) return
  
  try {
    chaptersLoading.value = true
    const response = await storyboardAPI.getSessionChapters(props.sessionId)
    chapters.value = response.data.chapters || []
    
    // 如果有章节数据，默认选择第一个章节
    if (chapters.value.length > 0) {
      // 确保选择第一个实际存在的章节，而不是硬编码的"1"
      selectedChapter.value = chapters.value[0].chapter_id.toString()
      console.log('默认选择章节:', selectedChapter.value, chapters.value[0].chapter_title)
    } else {
      selectedChapter.value = ''
    }
  } catch (error) {
    console.error('加载章节列表失败:', error)
    message.error('加载章节列表失败')
  } finally {
    chaptersLoading.value = false
  }
}

// 监听章节选择变化
watch(selectedChapter, (newChapterId) => {
  if (newChapterId) {
    loadChapterData(parseInt(newChapterId))
    // 更新章节状态
    updateChapterStatus()
  }
})

// 监听sessionId变化，强制刷新数据
watch(() => props.sessionId, (newSessionId) => {
  if (newSessionId) {
    loadChapters()
    if (selectedChapter.value) {
      loadChapterData(parseInt(selectedChapter.value))
    }
  }
}, { immediate: true })

// 组件挂载时加载数据
onMounted(() => {
  loadChapters()
  if (selectedChapter.value) {
    loadChapterData(parseInt(selectedChapter.value))
  }
})

const getSegmentTimeRange = (index) => {
  if (!timelineDetails.value.length) return `${index * 15}-${(index + 1) * 15}`
  
  // 直接使用AI分析时建立的对应关系
  const audioCard = timelineDetails.value[index]
  if (audioCard && audioCard.text_mapping) {
    const paragraphRange = audioCard.text_mapping.paragraph_range
    return `${paragraphRange[0]}-${paragraphRange[1]}`
  }
  
  // 如果没有对应关系，使用默认的时间范围
  return `${index * 15}-${(index + 1) * 15}`
}

const highlightSegment = (index) => {
  console.log('点击剧本段落:', index)
  
  // 清除所有高亮
  textSegments.value.forEach((segment, i) => {
    segment.highlighted = false
  })
  scriptSegments.value.forEach((script, i) => {
    script.highlighted = false
  })
  
  // 高亮当前点击的剧本段落
  if (index < scriptSegments.value.length) {
    scriptSegments.value[index].highlighted = true
    console.log('设置剧本段落高亮:', index, scriptSegments.value[index].highlighted)
  }
  
  // 根据音频分镜卡的对应关系高亮文本段落
  if (timelineDetails.value[index]) {
    const audioSegment = timelineDetails.value[index]
    
    if (audioSegment.text_mapping && audioSegment.text_mapping.paragraph_range) {
      const [startParagraph, endParagraph] = audioSegment.text_mapping.paragraph_range
      
      // 高亮对应的文本段落
      for (let i = startParagraph; i <= endParagraph && i < textSegments.value.length; i++) {
        textSegments.value[i].highlighted = true
      }
      
      // 滚动到第一个高亮的段落
      if (startParagraph < textSegments.value.length) {
        const firstHighlightedElement = document.querySelectorAll('.text-segment')[startParagraph]
        if (firstHighlightedElement) {
          firstHighlightedElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }
      
      message.info(`高亮段落 ${startParagraph + 1}-${endParagraph + 1}`)
    } else {
      // 如果没有对应关系，使用简单的索引对应
      if (index < textSegments.value.length) {
        textSegments.value[index].highlighted = true
        const element = document.querySelectorAll('.text-segment')[index]
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
        message.info(`高亮段落 ${index + 1}`)
      }
    }
  } else {
    // 如果没有timelineDetails，使用简单的索引对应
    if (index < textSegments.value.length) {
      textSegments.value[index].highlighted = true
      const element = document.querySelectorAll('.text-segment')[index]
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
      message.info(`高亮段落 ${index + 1}`)
    }
  }
}



const getCardTypeName = (cardType) => {
  const names = {
    'story': '故事',
    'character': '角色',
    'scene': '场景',
    'event': '事件',
    'emotion': '情绪',
    'audio_storyboard': '音频分镜'
  }
  return names[cardType] || cardType
}

const handleCardUpdate = (updatedCard) => {
  message.success('卡片更新成功')
  cardDrawerVisible.value = false
  // TODO: 重新加载数据
}

const getIssueColor = (type) => {
  const colors = {
    missing_speaker: 'red',
    missing_voice: 'orange',
    empty_content: 'purple',
    invalid_time: 'blue',
    timing: 'orange',
    emotion: 'red',
    background: 'blue',
    quality: 'purple'
  }
  return colors[type] || 'default'
}



// 进度更新处理
const handleProgressUpdate = (progress, step) => {
  console.log('进度更新:', progress, step)
}

// 章节分析相关方法
const getChapterAnalysisStatusColor = () => {
  const statusColors = {
    'pending': 'orange',
    'analyzing': 'blue',
    'completed': 'green',
    'failed': 'red'
  }
  return statusColors[currentChapterStatus.value] || 'default'
}

const getChapterAnalysisStatusText = () => {
  const statusTexts = {
    'pending': '待分析',
    'analyzing': '分析中',
    'completed': '已完成',
    'failed': '分析失败'
  }
  return statusTexts[currentChapterStatus.value] || '未知状态'
}

const canAnalyzeChapter = () => {
  return currentChapterStatus.value === 'pending' || currentChapterStatus.value === 'failed'
}

const canReanalyzeChapter = () => {
  return currentChapterStatus.value === 'completed'
}

const analyzeCurrentChapter = async () => {
  if (!selectedChapter.value || analyzingChapter.value) return
  
  analyzingChapter.value = true
  try {
    const response = await storyboardAPI.analyzeChapter(props.sessionId, selectedChapter.value)
    message.success('章节分析已开始')
    
    // 更新状态
    currentChapterStatus.value = 'analyzing'
    
    // 等待一段时间后刷新数据
    setTimeout(() => {
      loadChapterData(parseInt(selectedChapter.value))
      currentChapterStatus.value = 'completed'
    }, 3000)
    
  } catch (error) {
    console.error('章节分析失败:', error)
    message.error('章节分析失败: ' + (error.response?.data?.detail || error.message))
    currentChapterStatus.value = 'failed'
  } finally {
    analyzingChapter.value = false
  }
}

// 更新章节状态检查
const updateChapterStatus = async () => {
  if (!selectedChapter.value) return
  
  try {
    const response = await storyboardAPI.getReviewData(props.sessionId, selectedChapter.value)
    const hasScriptCards = response.data.cards?.audio_script?.length > 0
    
    if (hasScriptCards) {
      currentChapterStatus.value = 'completed'
    } else {
      currentChapterStatus.value = 'pending'
    }
  } catch (error) {
    console.error('获取章节状态失败:', error)
    currentChapterStatus.value = 'pending'
  }
}

// 获取关联卡片
const getRelatedCards = (script) => {
  const cards = []
  
  // 检查是否有对应的卡片数据
  if (!reviewData.value?.cards) return cards
  
  // 根据剧本内容类型和内容智能关联卡片
  if (script.type === 'dialogue' && script.speaker) {
    // 对话类型：关联角色卡、事件卡、情绪卡
    if (reviewData.value.cards.character?.length > 0) {
      cards.push({ type: 'character', name: '角色卡', icon: '🎭' })
    }
    if (reviewData.value.cards.event?.length > 0) {
      cards.push({ type: 'event', name: '事件卡', icon: '📝' })
    }
    if (reviewData.value.cards.emotion?.length > 0) {
      cards.push({ type: 'emotion', name: '情绪卡', icon: '💝' })
    }
  }
  
  if (script.type === 'narration') {
    // 旁白类型：关联场景卡、故事卡
    if (reviewData.value.cards.scene?.length > 0) {
      cards.push({ type: 'scene', name: '场景卡', icon: '🎬' })
    }
    if (reviewData.value.cards.story?.length > 0) {
      cards.push({ type: 'story', name: '故事卡', icon: '📖' })
    }
  }
  
  // 如果内容较长，可能包含更多信息，添加更多关联
  if (script.text && script.text.length > 30) {
    if (reviewData.value.cards.story?.length > 0 && !cards.find(c => c.type === 'story')) {
      cards.push({ type: 'story', name: '故事卡', icon: '📖' })
    }
    if (reviewData.value.cards.event?.length > 0 && !cards.find(c => c.type === 'event')) {
      cards.push({ type: 'event', name: '事件卡', icon: '📝' })
    }
  }
  
  // 音频相关卡片：根据时间范围关联
  if (script.startTime && script.endTime) {
    if (reviewData.value.cards.audio_storyboard?.length > 0) {
      cards.push({ type: 'audio_storyboard', name: '音频分镜卡', icon: '🎵' })
    }
    if (reviewData.value.cards.audio_script?.length > 0) {
      cards.push({ type: 'audio_script', name: '音频剧本卡', icon: '📝' })
    }
  }
  
  return cards
}

// 打开卡片抽屉
const openCardDrawer = (cardType, script) => {
  if (!reviewData.value?.cards) return
  
  // 获取对应类型的卡片
  let cards = reviewData.value.cards[cardType] || []
  if (cards.length === 0 && reviewData.value.book_cards) {
    cards = reviewData.value.book_cards[cardType] || []
  }
  
  if (cards.length > 0) {
    const card = cards[0]
    selectedCard.value = {
      id: card.id,
      type: cardType,
      title: `${getCardTypeName(cardType)}卡片`,
      content: card.content || {},
      confidence_score: card.confidence_score,
      related_script: script // 添加关联的剧本信息
    }
    cardDrawerVisible.value = true
  } else {
    message.warning(`暂无${getCardTypeName(cardType)}卡片数据`)
  }
}
</script>

<style scoped>
.content-review-container {
  min-height: 100vh;
  color: var(--text-color, #333);
}

.chapter-selector-container {
  margin-bottom: 16px;
  padding: 20px;
  background: var(--card-bg, #262626);
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow-color, rgba(0,0,0,0.1));
  border: 1px solid var(--border-color, #262626);
}

.chapter-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.chapter-analysis-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.analysis-status {
  display: flex;
  align-items: center;
}

/* 章节选择器样式（保留原有样式） */
.selector-row {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 12px;
}

.interaction-tips {
  padding: 8px 12px;
  background: var(--highlight-bg, #1a1a1a);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-color, #ffffff);
  border: 1px solid var(--border-color, #404040);
  margin-bottom: 16px;
}

.content-review-layout {
  display: flex;
  gap: 12px;
  height: calc(100vh - 200px);
}

.original-text-panel,
.script-panel {
  flex: 1;
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow-color, rgba(0, 0, 0, 0.1));
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #797979);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg, #6b6b6b);
  border-radius: 12px 12px 0 0;
}

.panel-header h3 {
  margin: 0;
  color: var(--text-color, #333);
  font-size: 18px;
  font-weight: 600;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.text-content,
.script-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--content-bg, #262626);
}

.text-segment {
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--segment-bg, transparent);
  color: var(--text-color, #333);
}

.text-segment:hover {
  border-color: var(--primary-color, #1890ff);
  background: var(--hover-bg, #f6ffed);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--shadow-color, rgba(0,0,0,0.1));
}

.text-segment.highlighted {
  border-color: var(--primary-color, #4a9eff);
  background: var(--highlight-bg, #e6f7ff);
  box-shadow: 0 2px 8px var(--shadow-color, rgba(0,0,0,0.1));
  border-left: 3px solid var(--primary-color, #4a9eff);
}

.segment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.segment-header .segment-index {
  font-weight: 500;
  color: var(--primary-color, #1890ff);
}

.segment-header .segment-time {
  font-weight: 500;
  color: var(--primary-color, #1890ff);
}

.segment-text {
  line-height: 1.6;
  color: var(--text-color, #333);
}

.segment-issues {
  margin-top: 8px;
}

.script-segment {
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--segment-bg, transparent);
  color: var(--text-color, #333);
}

.script-segment:hover {
  border-color: var(--primary-color, #1890ff);
  background: var(--hover-bg, #f6ffed);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--shadow-color, rgba(0,0,0,0.1));
}

.script-segment.highlighted {
  border-color: var(--primary-color, #4a9eff) !important;
  background: var(--highlight-bg, #e6f7ff) !important;
  box-shadow: 0 2px 8px var(--shadow-color, rgba(0,0,0,0.1)) !important;
  border-left: 3px solid var(--primary-color, #4a9eff) !important;
}

.script-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.script-header .script-time {
  font-weight: 500;
  color: var(--primary-color, #1890ff);
}

.script-header .script-type {
  font-weight: 500;
  color: var(--primary-color, #1890ff);
}

.script-content-main {
  margin-top: 8px;
}

.speaker-info {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-color, #333);
}

.speaker-label {
  font-weight: 500;
  color: var(--primary-color, #1890ff);
  margin-right: 8px;
}

.speaker-name {
  font-weight: 600;
  color: var(--text-color, #333);
}

.character-id {
  font-size: 12px;
  color: var(--text-secondary, #666);
  margin-left: 8px;
}

.script-text {
  margin-top: 12px;
}

.text-content {
  color: var(--text-color, #333);
  line-height: 1.6;
  font-size: 14px;
  padding: 12px 16px;
  background: var(--segment-bg, #f8f9fa);
  border-radius: 6px;
}



.audio-config {
  margin-top: 12px;
  padding: 12px;
  background: var(--primary-bg, #f0f8ff);
  border: 1px solid var(--primary-border, rgba(24, 144, 255, 0.2));
  border-radius: 6px;
}

.config-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  line-height: 1.5;
}

.config-item:last-child {
  margin-bottom: 0;
}

.config-label {
  font-weight: 500;
  color: var(--primary-color, #1890ff);
  min-width: 80px;
  margin-right: 8px;
}

.config-value {
  color: var(--text-color, #333);
  flex: 1;
}

.config-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
}

.config-tags .ant-tag {
  margin: 0;
  font-size: 12px;
}

.script-issues {
  margin-top: 12px;
}



.timeline-details,
.detected-issues {
  margin-bottom: 24px;
}

.timeline-details h4,
.detected-issues h4 {
  margin: 0 0 16px 0;
  color: var(--text-color, #333);
  font-size: 14px;
  font-weight: 600;
}

.timeline-detail-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--card-bg, white);
  border-radius: 6px;
  border-left: 4px solid var(--primary-color, #1890ff);
  transition: all 0.3s ease;
  cursor: pointer;
  color: var(--text-color, #333);
}

.detail-item:hover {
  background: var(--hover-bg, #f0f0f0);
  transform: translateX(2px);
}

.time-range {
  font-weight: 600;
  color: var(--primary-color, #1890ff);
  min-width: 60px;
  text-align: center;
}

.detail-content {
  flex: 1;
}

.detail-type {
  font-weight: 500;
  color: var(--text-secondary, #666);
  font-size: 14px;
  margin-bottom: 4px;
}

.detail-text {
  color: var(--text-color, #262626);
  font-size: 14px;
  margin-bottom: 8px;
}

.related-cards {
  margin-top: 12px;
  padding: 12px;
  background: var(--card-bg, #f8f9fa);
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 6px;
}

.cards-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.cards-title {
  font-weight: 500;
  margin-right: 4px;
}

.cards-count {
  color: var(--primary-color, #1890ff);
  font-weight: 500;
}

.cards-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.card-mini {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color, #e8e8e8);
  background: var(--card-bg, white);
  color: var(--text-color, #333);
}

.card-mini:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--shadow-color, rgba(0,0,0,0.1));
}

.card-mini.story-card {
  background: #fff2e8;
  color: #fa8c16;
  border-color: #fa8c16;
}

.card-mini.character-card {
  background: #e6f7ff;
  color: #1890ff;
  border-color: #1890ff;
}

.card-mini.scene-card {
  background: #f6ffed;
  color: #52c41a;
  border-color: #52c41a;
}

.card-mini.event-card {
  background: #f9f0ff;
  color: #722ed1;
  border-color: #722ed1;
}

.card-mini.emotion-card {
  background: #fff0f6;
  color: #eb2f96;
  border-color: #eb2f96;
}

.timeline-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid var(--border-color, #f0f0f0);
  border-radius: 6px;
  background: var(--item-bg, transparent);
  color: var(--text-color, #333);
}

.timeline-time {
  font-size: 12px;
  color: var(--text-secondary, #666);
  margin-bottom: 8px;
}

.timeline-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.timeline-text {
  flex: 1;
  margin-right: 12px;
  line-height: 1.5;
  color: var(--text-color, #333);
}

.timeline-actions {
  display: flex;
  gap: 8px;
}

.issue-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid var(--warning-border, #ffccc7);
  border-radius: 6px;
  background: var(--warning-bg, #fff2f0);
  color: var(--text-color, #333);
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.issue-time {
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.issue-description {
  margin-bottom: 8px;
  line-height: 1.5;
  color: var(--text-color, #333);
}



/* 深色主题变量 */
:root {
  /* 浅色主题 */
  --bg-color: #f5f5f5;
  --card-bg: white;
  --content-bg: transparent;
  --header-bg: #fafafa;
  --segment-bg: transparent;
  --item-bg: transparent;
  --text-color: #333;
  --text-secondary: #666;
  --border-color: #e8e8e8;
  --shadow-color: rgba(0, 0, 0, 0.1);
  --primary-color: #1890ff;
  --primary-bg: #f0f8ff;
  --primary-border: rgba(24, 144, 255, 0.2);
  --hover-bg: #f6ffed;
  --highlight-bg: #e6f7ff;
  --warning-bg: #fff2f0;
  --warning-border: #ffccc7;
}

/* 深色主题 */
[data-theme="dark"] {
  --bg-color: #0f0f0f;
  --card-bg: #1a1a1a;
  --content-bg: #1a1a1a;
  --header-bg: #262626;
  --segment-bg: #262626;
  --item-bg: #1a1a1a;
  --text-color: #e0e0e0;
  --text-secondary: #888888;
  --border-color: #333333;
  --shadow-color: rgba(0, 0, 0, 0.5);
  --primary-color: #4a9eff;
  --primary-bg: rgba(74, 158, 255, 0.08);
  --primary-border: rgba(74, 158, 255, 0.2);
  --hover-bg: rgba(74, 158, 255, 0.08);
  --highlight-bg: rgba(74, 158, 255, 0.15);
  --warning-bg: rgba(255, 77, 79, 0.08);
  --warning-border: rgba(255, 77, 79, 0.2);
}

/* 深色主题下的特殊样式覆盖 */
[data-theme="dark"] .text-content {
  background: var(--segment-bg, #262626) !important;
  color: var(--text-color, #e0e0e0) !important;
  border-left-color: var(--primary-color, #4a9eff) !important;
}

[data-theme="dark"] .script-segment {
  background: var(--item-bg, #1a1a1a) !important;
  border-color: var(--border-color, #333333) !important;
  color: var(--text-color, #e0e0e0) !important;
}

[data-theme="dark"] .text-segment {
  background: var(--item-bg, #1a1a1a) !important;
  border-color: var(--border-color, #333333) !important;
  color: var(--text-color, #e0e0e0) !important;
}

[data-theme="dark"] .card-mini {
  background: var(--item-bg, #1a1a1a) !important;
  border-color: var(--border-color, #333333) !important;
  color: var(--text-color, #e0e0e0) !important;
}

[data-theme="dark"] .panel-header {
  background: var(--header-bg, #262626) !important;
  border-color: var(--border-color, #333333) !important;
}

[data-theme="dark"] .panel-content {
  background: var(--content-bg, #1a1a1a) !important;
}

/* 滚动条样式 */
.text-content::-webkit-scrollbar,
.script-content::-webkit-scrollbar {
  width: 6px;
}

.text-content::-webkit-scrollbar-track,
.script-content::-webkit-scrollbar-track {
  background: var(--border-color, #f1f1f1);
  border-radius: 3px;
}

.text-content::-webkit-scrollbar-thumb,
.script-content::-webkit-scrollbar-thumb {
  background: var(--text-secondary, #c1c1c1);
  border-radius: 3px;
}

.text-content::-webkit-scrollbar-thumb:hover,
.script-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-color, #a8a8a8);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-color, #666);
}

.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-color, #999);
  font-style: italic;
}

/* 音频元素样式 */
.audio-elements {
  margin: 12px 0;
  padding: 12px;
  background: var(--primary-bg, #f0f8ff);
  border: 1px solid var(--primary-border, rgba(24, 144, 255, 0.2));
  border-radius: 6px;
}

.audio-element-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
  line-height: 1.5;
}

.audio-element-item:last-child {
  margin-bottom: 0;
}

.element-label {
  font-weight: 500;
  color: var(--primary-color, #1890ff);
  min-width: 80px;
  margin-right: 8px;
}

.element-value {
  color: var(--text-color, #333);
  flex: 1;
}

.element-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
}

.element-tags .ant-tag {
  margin: 0;
  font-size: 12px;
}

/* 关联卡片样式 */
.related-cards {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.card-mini {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color, #e8e8e8);
  background: var(--card-bg, white);
  color: var(--text-color, #333);
}

.card-mini:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--shadow-color, rgba(0,0,0,0.1));
}

.card-mini.story-card {
  background: #fff2e8;
  color: #fa8c16;
  border-color: #fa8c16;
}

.card-mini.character-card {
  background: #e6f7ff;
  color: #1890ff;
  border-color: #1890ff;
}

.card-mini.scene-card {
  background: #f6ffed;
  color: #52c41a;
  border-color: #52c41a;
}

.card-mini.event-card {
  background: #f9f0ff;
  color: #722ed1;
  border-color: #722ed1;
}

.card-mini.emotion-card {
  background: #fff0f6;
  color: #eb2f96;
  border-color: #eb2f96;
}

.card-mini.audio_storyboard-card {
  background: #e6fffb;
  color: #13c2c2;
  border-color: #13c2c2;
}

.card-mini.audio_script-card {
  background: #fffbe6;
  color: #faad14;
  border-color: #faad14;
}

/* 深色主题下的卡片颜色 */
[data-theme="dark"] .card-mini.story-card {
  background: rgba(250, 140, 22, 0.15);
  color: #ffa940;
  border-color: #ffa940;
}

[data-theme="dark"] .card-mini.character-card {
  background: rgba(24, 144, 255, 0.15);
  color: #69c0ff;
  border-color: #69c0ff;
}

[data-theme="dark"] .card-mini.scene-card {
  background: rgba(82, 196, 26, 0.15);
  color: #95de64;
  border-color: #95de64;
}

[data-theme="dark"] .card-mini.event-card {
  background: rgba(114, 46, 209, 0.15);
  color: #b37feb;
  border-color: #b37feb;
}

[data-theme="dark"] .card-mini.emotion-card {
  background: rgba(235, 47, 150, 0.15);
  color: #ff85c0;
  border-color: #ff85c0;
}

[data-theme="dark"] .card-mini.audio_storyboard-card {
  background: rgba(19, 194, 194, 0.15);
  color: #5cdbd3;
  border-color: #5cdbd3;
}

[data-theme="dark"] .card-mini.audio_script-card {
  background: rgba(250, 173, 20, 0.15);
  color: #ffd666;
  border-color: #ffd666;
}

/* 深色主题下的高亮样式 */
[data-theme="dark"] .text-segment.highlighted {
  border-color: var(--primary-color, #4a9eff) !important;
  background: rgba(74, 158, 255, 0.1) !important;
  box-shadow: 0 2px 8px rgba(74, 158, 255, 0.2) !important;
  border-left: 3px solid var(--primary-color, #4a9eff) !important;
}

[data-theme="dark"] .script-segment.highlighted {
  border-color: var(--primary-color, #4a9eff) !important;
  background: rgba(74, 158, 255, 0.1) !important;
  box-shadow: 0 2px 8px rgba(74, 158, 255, 0.2) !important;
  border-left: 3px solid var(--primary-color, #4a9eff) !important;
}

/* 深色主题下的关联卡片样式 */
[data-theme="dark"] .related-cards {
  background: var(--card-bg, #1a1a1a) !important;
  border-color: var(--border-color, #333333) !important;
}

[data-theme="dark"] .cards-header {
  color: var(--text-secondary, #999999) !important;
}

[data-theme="dark"] .cards-count {
  color: var(--primary-color, #4a9eff) !important;
}

/* 问题抽屉样式 */
.issues-drawer-content {
  padding: 16px 0;
}

.issues-drawer-content .issue-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.issues-drawer-content .issue-item {
  padding: 12px;
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 6px;
  background: var(--card-bg, #fff);
}

.issues-drawer-content .issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.issues-drawer-content .issue-time {
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.issues-drawer-content .issue-description {
  color: var(--text-color, #333);
  line-height: 1.5;
}
</style>
