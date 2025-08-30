<template>
  <div class="book-analysis-detail">
    <!-- 进度监控 -->
    <ProgressMonitor 
      v-if="isAnalyzing"
      :session-id="sessionId"
      @progress-update="handleProgressUpdate"
    />

    <!-- 主要内容区域 -->
    <div class="main-content">
      <ContentReviewTab 
        :session-id="sessionId"
        :session="currentSession"
        :cards="cards"
        :loading="loading"
        @start-analysis="startAnalysis"
        @confirm-session="confirmSession"
        @reanalyze-session="reanalyzeSession"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useStoryboardStore } from '@/stores/storyboard'
import { ANALYSIS_STATUS } from '@/api/storyboard'

// 导入子组件
import ProgressMonitor from '@/components/storyboard/ProgressMonitor.vue'
import ContentReviewTab from '@/components/storyboard/ContentReviewTab.vue'

const route = useRoute()
const router = useRouter()
const storyboardStore = useStoryboardStore()

// 响应式数据
const sessionId = computed(() => route.params.sessionId)
const loading = ref(false)

// 计算属性
const currentSession = computed(() => storyboardStore.currentSession)
const cards = computed(() => storyboardStore.cards)
const isAnalyzing = computed(() => 
  currentSession.value?.status === ANALYSIS_STATUS.ANALYZING
)

// 方法
const loadSessionData = async () => {
  if (!sessionId.value) return
  
  try {
    loading.value = true
    await storyboardStore.loadSessionDetail(sessionId.value)
    await storyboardStore.loadSessionCards(sessionId.value)
  } catch (error) {
    message.error('加载会话数据失败')
  } finally {
    loading.value = false
  }
}

const startAnalysis = async () => {
  try {
    await storyboardStore.startAnalysis(sessionId.value)
    message.success('分析已开始')
  } catch (error) {
    message.error('开始分析失败')
  }
}

const confirmSession = async () => {
  try {
    await storyboardStore.confirmSession(sessionId.value)
    message.success('会话已确认')
  } catch (error) {
    message.error('确认会话失败')
  }
}

const reanalyzeSession = async () => {
  try {
    await storyboardStore.reanalyzeSession(sessionId.value)
    message.success('重新分析已开始')
  } catch (error) {
    message.error('重新分析失败')
  }
}

const handleProgressUpdate = (progress, step) => {
  storyboardStore.updateProgress(progress, step)
}

const handleCardUpdate = async (cardId, data) => {
  try {
    await storyboardStore.updateCard(cardId, data)
    message.success('卡片更新成功')
  } catch (error) {
    message.error('卡片更新失败')
  }
}

const handleCardConfirm = async (cardId) => {
  try {
    await storyboardStore.confirmCard(cardId)
    message.success('卡片已确认')
  } catch (error) {
    message.error('卡片确认失败')
  }
}

const handleCardReanalyze = async (cardId) => {
  try {
    await storyboardStore.reanalyzeCard(cardId)
    message.success('卡片重新分析已开始')
  } catch (error) {
    message.error('卡片重新分析失败')
  }
}

const handleChapterAnalyze = async (chapterId) => {
  try {
    // 调用独立的章节分析API
    await storyboardStore.analyzeChapter(sessionId.value, chapterId)
    message.success('章节分析已开始')
  } catch (error) {
    message.error('章节分析失败')
  }
}

// 监听路由变化
watch(sessionId, () => {
  if (sessionId.value) {
    loadSessionData()
  }
})

// 生命周期
onMounted(() => {
  if (sessionId.value) {
    loadSessionData()
  }
})
</script>

<style scoped>
.book-analysis-detail {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  overflow: hidden;
}

:deep(.ant-tabs-content-holder) {
  height: 100%;
  overflow: auto;
}

:deep(.ant-tabs-tabpane) {
  height: 100%;
  padding: 16px 0;
}
</style>
