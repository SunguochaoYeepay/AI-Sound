<template>
  <div class="chapter-selector-container">
    <div class="chapter-controls">
      <a-select 
        :value="selectedChapter" 
        placeholder="选择章节" 
        style="width: 300px;"
        :loading="chaptersLoading"
        @change="handleChapterChange"
      >
        <a-select-option v-for="chapter in chapters" :key="chapter.id || chapter.chapter_id" :value="(chapter.id || chapter.chapter_id).toString()">
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
        
        <!-- 智能分段按钮 -->
        <a-button
          v-if="canSegmentChapter()"
          type="default"
          :loading="segmentingChapter"
          @click="handleSmartSegmentation"
          size="small"
        >
          <template #icon>
            <ScissorOutlined />
          </template>
          智能分段
        </a-button>

        <!-- 分析按钮 -->
        <a-button
          v-if="canAnalyzeChapter()"
          type="primary"
          :loading="analyzingChapter"
          @click="handleAnalyzeChapter"
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
          @click="handleAnalyzeChapter"
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
</template>

<script setup>
import { PlayCircleOutlined, ReloadOutlined, ScissorOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  chapters: {
    type: Array,
    default: () => []
  },
  chaptersLoading: {
    type: Boolean,
    default: false
  },
  selectedChapter: {
    type: String,
    default: ''
  },
  currentChapterStatus: {
    type: String,
    default: 'pending'
  },
  analyzingChapter: {
    type: Boolean,
    default: false
  },
  segmentingChapter: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['chapter-change', 'analyze-chapter', 'smart-segmentation'])

// Methods
const handleChapterChange = (value) => {
  emit('chapter-change', value)
}

const handleAnalyzeChapter = () => {
  emit('analyze-chapter')
}

const handleSmartSegmentation = () => {
  emit('smart-segmentation')
}

const getChapterAnalysisStatusColor = () => {
  const statusColors = {
    'pending': 'orange',
    'analyzing': 'blue',
    'completed': 'green',
    'failed': 'red'
  }
  return statusColors[props.currentChapterStatus] || 'default'
}

const getChapterAnalysisStatusText = () => {
  const statusTexts = {
    'pending': '待分析',
    'analyzing': '分析中',
    'completed': '已完成',
    'failed': '分析失败'
  }
  return statusTexts[props.currentChapterStatus] || '未知状态'
}

const canAnalyzeChapter = () => {
  return props.currentChapterStatus === 'pending' || props.currentChapterStatus === 'failed'
}

const canReanalyzeChapter = () => {
  return props.currentChapterStatus === 'completed'
}

const canSegmentChapter = () => {
  // 只要有章节内容就可以分段，不依赖分析状态
  return props.selectedChapter && props.selectedChapter !== ''
}
</script>

<style scoped>
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
</style>
