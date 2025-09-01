<template>
  <div class="content-review-container">
    <!-- 进度监控 -->
    <ProgressMonitor :session-id="sessionId" @progress-update="handleProgressUpdate" />

    <!-- 章节选择器 -->
    <ChapterSelector 
      :chapters="chapters"
      :chapters-loading="chaptersLoading"
      :selected-chapter="selectedChapter"
      :current-chapter-status="currentChapterStatus"
      :analyzing-chapter="analyzingChapter"
      @chapter-change="handleChapterChange"
      @analyze-chapter="analyzeCurrentChapter"
    />

    <!-- 主要内容区域 -->
    <div class="content-review-layout">
      <!-- 左侧：原始文本 -->
      <OriginalTextPanel 
        :loading="loading"
        :chapter-content="chapterContent"
        :text-segments="textSegments"
        :timeline-details="timelineDetails"
        @segment-click="handleTextSegmentClick"
      />

      <!-- 右侧：剧本详情 -->
      <ScriptDetailPanel 
        :loading="loading"
        :script-segments="scriptSegments"
        :detected-issues="detectedIssues"
        :review-data="reviewData"
        @segment-click="handleScriptSegmentClick"
        @card-click="openCardDrawer"
      />
    </div>

    <!-- 卡片详情抽屉 -->
    <CardDetailDrawer 
      :open="cardDrawerVisible"
      :card="selectedCard"
      @update:visible="cardDrawerVisible = $event"
      @update="handleCardUpdate"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { LoadingOutlined } from '@ant-design/icons-vue'
import CardDetailDrawer from './CardDetailDrawer.vue'
import ProgressMonitor from './ProgressMonitor.vue'
import ChapterSelector from './ChapterSelector.vue'
import OriginalTextPanel from './OriginalTextPanel.vue'
import ScriptDetailPanel from './ScriptDetailPanel.vue'
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

// 章节分析状态
const analyzingChapter = ref(false)
const currentChapterStatus = ref('pending')

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

// 处理文本段落点击
const handleTextSegmentClick = (index) => {
  // 这里可以添加文本段落点击的处理逻辑
  console.log('点击文本段落:', index)
}

// 处理剧本段落点击
const handleScriptSegmentClick = (index) => {
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

// 处理章节选择变化
const handleChapterChange = (chapterId) => {
  selectedChapter.value = chapterId
  if (chapterId) {
    loadChapterData(parseInt(chapterId))
    updateChapterStatus()
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



// 进度更新处理
const handleProgressUpdate = (progress, step) => {
  console.log('进度更新:', progress, step)
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

.content-review-layout {
  display: flex;
  gap: 12px;
  height: calc(100vh - 200px);
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
</style>
