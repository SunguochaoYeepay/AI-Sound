<template>
  <div class="script-panel">
    <div class="panel-header">
      <h3>📝 剧本详情</h3>
    </div>

    <div class="script-content">
      <!-- 剧本详情 -->
      <div class="script-details">
        <div v-if="loading" class="loading-container">
          <a-spin size="large" />
          <p>加载中...</p>
        </div>
        
        <div v-else-if="scriptSegments.length > 0" class="script-segment-list">
          <ScriptSegment
            v-for="(script, index) in scriptSegments"
            :key="index"
            :script="script"
            :related-cards="getRelatedCards(script)"
            @segment-click="handleSegmentClick(index)"
            @card-click="handleCardClick"
            @six-card-analysis="handleSegmentAnalysis"
          />
        </div>
        
        <!-- 段落剧本展示 -->
        <ScriptSegmentList
          v-if="sixCardResults && sixCardResults.length > 0"
          :six-card-results="sixCardResults"
          :highlighted-segment-index="highlightedSegmentIndex"
          @show-analysis="showSixCardAnalysis"
        />
        
        <div v-else-if="!sixCardResults || sixCardResults.length === 0" class="empty-content">
          <p>暂无数据</p>
        </div>
      </div>
    </div>

    <!-- 6卡分析抽屉 -->
    <SixCardAnalysisDrawer
      :open="showSixCardDrawer"
      :selected-result="selectedResult"
      @close="showSixCardDrawer = false"
    />

    <!-- 问题抽屉 -->
    <IssuesDrawer
      :open="showIssuesDrawer"
      :loading="loading"
      :detected-issues="detectedIssues"
      @close="showIssuesDrawer = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { storyboardAPI } from '@/api/storyboard'
import ScriptSegment from './ScriptSegment.vue'
import ScriptSegmentList from './ScriptSegmentList.vue'
import SixCardAnalysisDrawer from './SixCardAnalysisDrawer.vue'
import IssuesDrawer from './IssuesDrawer.vue'

// Props
const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  scriptSegments: {
    type: Array,
    default: () => []
  },
  detectedIssues: {
    type: Array,
    default: () => []
  },
  reviewData: {
    type: Object,
    default: () => ({})
  },
  chapter: {
    type: Object,
    default: () => ({})
  },
  sixCardResults: {
    type: Array,
    default: () => []
  },
  selectedSegmentIndex: {
    type: Number,
    default: null
  },
  highlightedSegmentIndex: {
    type: Number,
    default: null
  }
})

// Emits
const emit = defineEmits(['segment-click', 'card-click'])

// Reactive data
const showIssuesDrawer = ref(false)
const analyzingAll = ref(false)
const showSixCardDrawer = ref(false)
const selectedResult = ref(null)

// Computed properties
const sortedSixCardResults = computed(() => {
  return props.sixCardResults || []
})

// Methods
const handleSegmentClick = (index) => {
  emit('segment-click', index)
}

const handleCardClick = (card) => {
  emit('card-click', card)
}

const handleSegmentAnalysis = async (segmentIndex) => {
  try {
    analyzingAll.value = true
    const response = await storyboardAPI.analyzeSegment(
      props.chapter.id,
      [segmentIndex]
    )
    
    if (response.success) {
      message.success('段落分析完成')
      emit('segment-analysis-complete')
    } else {
      message.error('段落分析失败')
    }
  } catch (error) {
    console.error('段落分析失败:', error)
    message.error('段落分析失败')
  } finally {
    analyzingAll.value = false
  }
}

const analyzeAllSegments = async () => {
  try {
    analyzingAll.value = true
    
    const segmentIndices = []
    if (props.reviewData?.segmentation_data?.segments) {
      for (let i = 0; i < props.reviewData.segmentation_data.segments.length; i++) {
        segmentIndices.push(i + 1)
      }
    }
    
    if (segmentIndices.length === 0) {
      message.warning('没有可分析的段落')
      return
    }
    
    const response = await storyboardAPI.analyzeSegment(
      props.chapter.id,
      segmentIndices
    )
    
    if (response.success) {
      message.success(`成功分析 ${segmentIndices.length} 个段落`)
      emit('segment-analysis-complete')
    } else {
      message.error('批量分析失败')
    }
  } catch (error) {
    console.error('批量分析失败:', error)
    message.error('批量分析失败')
  } finally {
    analyzingAll.value = false
  }
}

const showSixCardAnalysis = (result) => {
  selectedResult.value = result
  showSixCardDrawer.value = true
}

const getRelatedCards = (script) => {
  const cards = []
  
  if (script.type === 'dialogue') {
    cards.push({ type: 'character', name: '角色卡' })
    cards.push({ type: 'event', name: '事件卡' })
    cards.push({ type: 'emotion', name: '情绪卡' })
  } else if (script.type === 'narration') {
    cards.push({ type: 'scene', name: '场景卡' })
    cards.push({ type: 'story', name: '故事卡' })
  }
  
  if (script.content && script.content.length > 100) {
    cards.push({ type: 'story', name: '故事卡' })
  }
  
  if (script.audio_related) {
    cards.push({ type: 'audio_storyboard', name: '音频分镜卡' })
    cards.push({ type: 'audio_script', name: '音频剧本卡' })
  }
  
  return cards
}
</script>

<style scoped>
@import '@/assets/styles/storyboard.css';

.script-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--panel-bg, #ffffff);
  border-left: 1px solid var(--border-color, #e8e8e8);
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow-color, rgba(0, 0, 0, 0.1));
  overflow: hidden;
}

.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #e8e8e8);
  background: var(--header-bg, #fafafa);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 12px 12px 0 0;
}

.panel-header h3 {
  margin: 0;
  color: var(--text-color, #333);
  font-size: 18px;
  font-weight: 600;
}

.script-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.script-details {
  height: 100%;
}

/* 深色主题适配 */
[data-theme="dark"] .script-panel {
  background: var(--card-bg, #1a1a1a);
  border-left-color: var(--border-color, #333333);
}

[data-theme="dark"] .panel-header {
  background: var(--header-bg, #262626) !important;
  border-color: var(--border-color, #333333) !important;
}

[data-theme="dark"] .panel-header h3 {
  color: var(--text-color, #e0e0e0);
}

[data-theme="dark"] .script-content {
  background: var(--content-bg, #1a1a1a);
}
</style>
