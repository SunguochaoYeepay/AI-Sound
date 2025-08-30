<template>
  <div class="content-review-container">
    <!-- 统一控制面板 -->
    <div class="unified-control-panel">
      <!-- 左侧：会话信息和进度 -->
      <div class="session-info">
        <div class="session-header">
          <h2>分析会话 #{{ sessionId }} {{ session?.book?.title || '未知书籍' }}</h2>
          <div class="session-status">
            <a-tag :color="getStatusColor(session?.status)">
              <template #icon><component :is="getStatusIcon(session?.status)" /></template>
              {{ getStatusText(session?.status) }}
            </a-tag>
          </div>
        </div>
        <div class="session-progress">
          <span>进度: {{ session?.progress || 0 }}%</span>
          <a-progress 
            :percent="session?.progress || 0" 
            :status="getProgressStatus(session?.status)"
            size="small"
            style="width: 200px; margin-left: 12px;"
          />
        </div>
      </div>

      <!-- 中间：章节选择器 -->
      <div class="chapter-selector">
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
        <div class="chapter-status">
          <a-tag color="green">
            <template #icon><CheckCircleOutlined /></template>
            AI分析完成
          </a-tag>
          <a-tag color="orange">
            <template #icon><ClockCircleOutlined /></template>
            待人工确认
          </a-tag>
        </div>
      </div>

      <!-- 右侧：操作按钮 -->
      <div class="session-actions">
        <a-button type="primary" @click="startAnalysis" :loading="session?.status === 'analyzing'">
          <template #icon><PlayCircleOutlined /></template>
          开始分析
        </a-button>
        <a-button @click="confirmSession" :disabled="session?.status !== 'ready_for_review'">
          <template #icon><CheckOutlined /></template>
          确认会话
        </a-button>
        <a-button @click="reanalyzeSession">
          <template #icon><ReloadOutlined /></template>
          重新分析
        </a-button>
      </div>
    </div>

    

    <!-- 主要内容区域 -->
    <div class="content-review-layout">
      <!-- 左侧：原始文本 -->
      <div class="original-text-panel">
        <div class="panel-header">
          <h3>原始文本</h3>
          <div class="panel-actions">
            <a-button type="primary" size="small" @click="exportTimeline">
              <template #icon><ExportOutlined /></template>
              导出时间轴
            </a-button>
          </div>
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
            @click="highlightSegment(index)"
          >
            <div class="segment-header">
              <span class="segment-time">{{ segment.time }}</span>
              <span class="segment-duration">{{ segment.duration }}</span>
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

      <!-- 右侧：音频分镜卡详情 -->
      <div class="storyboard-panel">
        <div class="panel-header">
          <h3>音频分镜卡详情</h3>
          <div class="panel-actions">
            <a-button type="primary" size="small" @click="playPreview">
              <template #icon><PlayCircleOutlined /></template>
              播放预览
            </a-button>
            <a-button size="small" @click="exportTimeline">
              <template #icon><ExportOutlined /></template>
              导出分镜
            </a-button>
          </div>
        </div>

        <div class="storyboard-content">
          <!-- 时间轴详情 -->
          <div class="timeline-details">
            <div v-if="loading" class="loading-container">
              <a-spin size="large" />
              <p>加载中...</p>
            </div>
            <div v-else-if="timelineDetails.length > 0" class="timeline-detail-list">
              <div class="detail-item" v-for="(detail, index) in timelineDetails" :key="index" @click="highlightSegment(index)">
                <div class="time-range">{{ detail.startTime }}-{{ detail.endTime }}s</div>
                <div class="detail-content">
                  <div class="detail-type">{{ detail.type }}</div>
                  <div class="detail-text">{{ detail.text }}</div>
                  
                  <!-- 相关卡片 -->
                  <div class="related-cards">
                    <div v-if="hasStoryCard" 
                         class="card-mini story-card" 
                         @click.stop="openCardDrawer('story')">
                      📖 故事卡
                    </div>
                    <div v-if="hasCharacterCard" 
                         class="card-mini character-card" 
                         @click.stop="openCardDrawer('character')">
                      🎭 角色卡
                    </div>
                    <div v-if="hasSceneCard" 
                         class="card-mini scene-card" 
                         @click.stop="openCardDrawer('scene')">
                      🎬 场景卡
                    </div>
                    <div v-if="hasEventCard" 
                         class="card-mini event-card" 
                         @click.stop="openCardDrawer('event')">
                      📝 事件卡
                    </div>
                    <div v-if="hasEmotionCard" 
                         class="card-mini emotion-card" 
                         @click.stop="openCardDrawer('emotion')">
                      💝 情绪卡
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-content">
              <p>暂无时间轴数据</p>
            </div>
          </div>

          <!-- 检测到的问题 -->
          <div class="detected-issues">
            <h4>检测到的问题</h4>
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
                <div class="issue-actions">
                  <a-button size="small" @click="requestModification(issue)">
                    <template #icon><MessageOutlined /></template>
                    请求修改
                  </a-button>
                </div>
              </div>
            </div>
            <div v-else class="empty-content">
              <p>暂无问题</p>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <a-button type="primary" @click="confirmChapter">
              <template #icon><CheckOutlined /></template>
              确认章节
            </a-button>
            <a-button @click="skipChapter">
              <template #icon><StepForwardOutlined /></template>
              跳过章节
            </a-button>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { 
  ExportOutlined, 
  EditOutlined, 
  PlayCircleOutlined, 
  ToolOutlined, 
  MessageOutlined, 
  CheckOutlined,
  StepForwardOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  LoadingOutlined,
  CheckCircleFilled,
  ExclamationCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons-vue'
import CardDetailDrawer from './CardDetailDrawer.vue'
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

// 监听章节选择变化
watch(selectedChapter, (newChapterId) => {
  if (newChapterId) {
    loadChapterData(parseInt(newChapterId))
  }
})

// 组件挂载时加载数据
onMounted(() => {
  loadChapters()
  if (selectedChapter.value) {
    loadChapterData(parseInt(selectedChapter.value))
  }
})

// 加载章节列表
const loadChapters = async () => {
  if (!props.sessionId) return
  
  try {
    chaptersLoading.value = true
    const response = await storyboardAPI.getSessionChapters(props.sessionId)
    chapters.value = response.data.chapters || []
    
    // 如果有章节数据，默认选择第一个章节
    if (chapters.value.length > 0 && !selectedChapter.value) {
      selectedChapter.value = chapters.value[0].chapter_id.toString()
    }
  } catch (error) {
    console.error('加载章节列表失败:', error)
    message.error('加载章节列表失败')
  } finally {
    chaptersLoading.value = false
  }
}

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

// 加载章节数据
const loadChapterData = async (chapterId) => {
  if (!props.sessionId || !chapterId) return
  
  loading.value = true
  try {
    const response = await storyboardAPI.getReviewData(props.sessionId, chapterId)
    reviewData.value = response.data
    
    // 设置章节内容
    chapterContent.value = response.data.chapter.content || ''
    
    // 处理音频分镜卡片数据
    const audioCards = response.data.cards.audio_storyboard || []
    if (audioCards.length > 0) {
      const audioCard = audioCards[0]
      const timeline = audioCard.content?.timeline || []
      
      // 转换为时间轴详情格式
      timelineDetails.value = timeline.map((item, index) => ({
        startTime: item.start_time?.toString() || '0',
        endTime: item.end_time?.toString() || '0',
        type: item.audio_elements?.voice_effects === '对话录音' ? '对话' : '旁白',
        text: item.scene_description || '场景描述',
        audioElements: item.audio_elements || {}
      }))
    } else {
      timelineDetails.value = []
    }
    
    // 处理文本段落（基于章节内容分段）
    const paragraphs = chapterContent.value.split('\n').filter(p => p.trim())
    textSegments.value = paragraphs.map((paragraph, index) => ({
      time: `${index * 15}:00`,
      duration: '00:00:15',
      text: paragraph,
      highlighted: false,
      issues: []
    }))
    
    // 设置卡片存在状态（包括书籍级卡片）
    hasStoryCard.value = !!(
      (response.data.cards.story && response.data.cards.story.length > 0) ||
      (response.data.book_cards && response.data.book_cards.story && response.data.book_cards.story.length > 0)
    )
    hasCharacterCard.value = !!(
      (response.data.cards.character && response.data.cards.character.length > 0) ||
      (response.data.book_cards && response.data.book_cards.character && response.data.book_cards.character.length > 0)
    )
    hasSceneCard.value = !!(response.data.cards.scene && response.data.cards.scene.length > 0)
    hasEventCard.value = !!(response.data.cards.event && response.data.cards.event.length > 0)
    hasEmotionCard.value = !!(response.data.cards.emotion && response.data.cards.emotion.length > 0)
    
    // 处理检测到的问题（基于卡片数据）
    detectedIssues.value = []
    const allCards = Object.values(response.data.cards).flat()
    allCards.forEach(card => {
      if (card.confidence_score < 0.8) {
        detectedIssues.value.push({
          type: 'quality',
          time: '00:00:00',
          description: `${card.card_type}卡片置信度较低: ${card.confidence_score}`
        })
      }
    })
    
  } catch (error) {
    console.error('加载章节数据失败:', error)
    message.error('加载章节数据失败')
  } finally {
    loading.value = false
  }
}

const highlightSegment = (index) => {
  textSegments.value.forEach((segment, i) => {
    segment.highlighted = i === index
  })
  message.info(`高亮段落 ${index + 1}`)
}

const openCardDrawer = (cardType) => {
  if (!reviewData.value?.cards) return
  
  // 优先从章节级卡片获取，如果没有则从书籍级卡片获取
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
      confidence_score: card.confidence_score
    }
    cardDrawerVisible.value = true
  } else {
    message.warning(`暂无${getCardTypeName(cardType)}卡片数据`)
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

const playPreview = (detail) => {
  message.info(`播放预览: ${detail.text}`)
}

const exportTimeline = () => {
  message.success('时间轴导出成功')
}

const showFixPanel = (detail) => {
  message.info(`显示修复面板: ${detail.text}`)
}

const requestModification = (issue) => {
  message.info(`请求修改: ${issue.description}`)
}

const skipChapter = () => {
  message.warning('跳过当前章节')
}

const confirmChapter = () => {
  message.success('章节确认成功')
}

const handleCardUpdate = (updatedCard) => {
  message.success('卡片更新成功')
  cardDrawerVisible.value = false
}



const getIssueColor = (type) => {
  const colors = {
    timing: 'orange',
    emotion: 'red',
    background: 'blue',
    quality: 'purple'
  }
  return colors[type] || 'default'
}

// 状态管理方法
const getStatusColor = (status) => {
  const colors = {
    pending: 'orange',
    analyzing: 'blue',
    completed: 'green',
    ready_for_review: 'purple',
    confirmed: 'green',
    failed: 'red'
  }
  return colors[status] || 'default'
}

const getStatusIcon = (status) => {
  const icons = {
    pending: ClockCircleOutlined,
    analyzing: LoadingOutlined,
    completed: CheckCircleFilled,
    ready_for_review: ExclamationCircleOutlined,
    confirmed: CheckCircleFilled,
    failed: CloseCircleOutlined
  }
  return icons[status] || ClockCircleOutlined
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待分析',
    analyzing: '分析中',
    completed: '分析完成',
    ready_for_review: '待确认',
    confirmed: '已确认',
    failed: '分析失败'
  }
  return texts[status] || '未知状态'
}

const getProgressStatus = (status) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed' || status === 'confirmed') return 'success'
  return 'active'
}

// 会话操作方法
const startAnalysis = () => {
  emit('start-analysis')
}

const confirmSession = () => {
  emit('confirm-session')
}

const reanalyzeSession = () => {
  emit('reanalyze-session')
}

onMounted(() => {
  console.log('ContentReviewTab mounted')
})
</script>

<style scoped>
.content-review-container {
  min-height: 100vh;
  color: var(--text-color, #333);
}

/* 统一控制面板样式 */
.unified-control-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--card-bg, rgb(0, 0, 0));
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px var(--shadow-color, rgba(0,0,0,0.1));
  border: 1px solid var(--border-color, #e8e8e8);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.session-header h2 {
  margin: 0;
  font-size: 18px;
  color: var(--text-color, #333);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-status {
  flex-shrink: 0;
}

.session-progress {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--text-secondary, #666);
}

.chapter-selector {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 300px;
}

.chapter-status {
  display: flex;
  gap: 8px;
}

.session-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
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
  gap: 24px;
  height: calc(100vh - 200px);
}

.original-text-panel,
.storyboard-panel {
  flex: 1;
  border-radius: 8px;
  box-shadow: 0 2px 8px var(--shadow-color, rgba(0, 0, 0, 0.1));
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #797979);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg, #6b6b6b);
}

.panel-header h3 {
  margin: 0;
  color: var(--text-color, #333);
  font-size: 16px;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.text-content,
.storyboard-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: var(--content-bg, transparent);
}

.text-segment {
  margin-bottom: 16px;
  padding: 12px;
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--segment-bg, transparent);
  color: var(--text-color, #333);
}

.text-segment:hover {
  border-color: var(--primary-color, #1890ff);
  background: var(--hover-bg, #f6ffed);
}

.text-segment.highlighted {
  border-color: var(--primary-color, #1890ff);
  background: var(--highlight-bg, #e6f7ff);
}

.segment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.segment-text {
  line-height: 1.6;
  color: var(--text-color, #333);
}

.segment-issues {
  margin-top: 8px;
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
  display: flex;
  gap: 8px;
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

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 20px 0;
  border-top: 1px solid #f0f0f0;
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
  --bg-color: #1f1f1f;
  --card-bg: #2d2d2d;
  --content-bg: #2d2d2d;
  --header-bg: #3a3a3a;
  --segment-bg: #3a3a3a;
  --item-bg: #2d2d2d;
  --text-color: #ffffff;
  --text-secondary: #b0b0b0;
  --border-color: #404040;
  --shadow-color: rgba(0, 0, 0, 0.3);
  --primary-color: #4a9eff;
  --primary-bg: rgba(74, 158, 255, 0.1);
  --primary-border: rgba(74, 158, 255, 0.3);
  --hover-bg: rgba(74, 158, 255, 0.1);
  --highlight-bg: rgba(74, 158, 255, 0.2);
  --warning-bg: rgba(255, 77, 79, 0.1);
  --warning-border: rgba(255, 77, 79, 0.3);
}

/* 滚动条样式 */
.text-content::-webkit-scrollbar,
.storyboard-content::-webkit-scrollbar {
  width: 6px;
}

.text-content::-webkit-scrollbar-track,
.storyboard-content::-webkit-scrollbar-track {
  background: var(--border-color, #f1f1f1);
  border-radius: 3px;
}

.text-content::-webkit-scrollbar-thumb,
.storyboard-content::-webkit-scrollbar-thumb {
  background: var(--text-secondary, #c1c1c1);
  border-radius: 3px;
}

.text-content::-webkit-scrollbar-thumb:hover,
.storyboard-content::-webkit-scrollbar-thumb:hover {
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
</style>
