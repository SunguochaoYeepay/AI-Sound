<template>
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
        @click="handleSegmentClick(index)"
      >
        <div class="segment-header">
          <div class="segment-info">
            <span class="segment-index">段落 {{ index + 1 }}</span>
            <span class="segment-time">{{ getSegmentTimeRange(index) }}</span>
          </div>
          <a-button 
            size="small" 
            type="primary"
            @click="handleSixCardAnalysis(index)"
            :loading="analyzingSegments[index]"
          >
            <template #icon>
              <AppstoreOutlined />
            </template>
            6卡分析
          </a-button>
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
</template>

<script setup>
import { ref } from 'vue'
import { AppstoreOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { storyboardAPI } from '@/api/storyboard'

// Props
const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  chapterContent: {
    type: String,
    default: ''
  },
  textSegments: {
    type: Array,
    default: () => []
  },
  timelineDetails: {
    type: Array,
    default: () => []
  },
  chapter: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['segment-click', 'six-card-analysis'])

// Reactive data
const analyzingSegments = ref({})

// Methods
const handleSegmentClick = (index) => {
  emit('segment-click', index)
}

const handleSixCardAnalysis = async (segmentIndex) => {
  if (analyzingSegments.value[segmentIndex]) return
  
  analyzingSegments.value[segmentIndex] = true
  try {
    console.log(`开始分析段落 ${segmentIndex + 1}...`)
    
    // 显示分析提示
    message.info({
      content: `正在分析段落 ${segmentIndex + 1}，请稍候...`,
      duration: 3,
      key: `segment-${segmentIndex}`
    })
    
    // 调用6卡分析API
    const response = await storyboardAPI.sixCardAnalysis(props.chapter?.id, [segmentIndex])
    
    if (response.data?.success) {
      message.success({
        content: `✅ 段落 ${segmentIndex + 1} 6卡分析完成！`,
        duration: 3,
        key: `segment-${segmentIndex}`
      })
      
      // 触发事件，让父组件显示分析结果
      emit('six-card-analysis', {
        segmentIndex,
        results: response.data.data.results
      })
      
      console.log('6卡分析完成:', response.data)
    } else {
      throw new Error(response.data?.message || '6卡分析失败')
    }
    
  } catch (error) {
    console.error('6卡分析失败:', error)
    message.error({
      content: `❌ 段落 ${segmentIndex + 1} 6卡分析失败`,
      duration: 3,
      key: `segment-${segmentIndex}`
    })
  } finally {
    analyzingSegments.value[segmentIndex] = false
  }
}

const getSegmentTimeRange = (index) => {
  if (!props.timelineDetails.length) return `段落 ${index + 1}`
  
  // 直接使用AI分析时建立的对应关系
  const audioCard = props.timelineDetails[index]
  if (audioCard && audioCard.text_mapping) {
    const paragraphRange = audioCard.text_mapping.paragraph_range
    // 确保段落范围正确显示
    if (Array.isArray(paragraphRange) && paragraphRange.length === 2) {
      return `段落 ${paragraphRange[0] + 1}-${paragraphRange[1] + 1}`
    }
  }
  
  // 如果没有对应关系，使用默认的段落索引
  return `段落 ${index + 1}`
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
</script>

<style scoped>
.original-text-panel {
  flex: 1;
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow-color, rgba(0, 0, 0, 0.1));
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #262626);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg, #262626);
  border-radius: 12px 12px 0 0;
}

.panel-header h3 {
  margin: 0;
  color: var(--text-color, #333);
  font-size: 18px;
  font-weight: 600;
}

.text-content {
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

/* 深色主题下的特殊样式覆盖 */
[data-theme="dark"] .text-segment {
  background: var(--item-bg, #1a1a1a) !important;
  border-color: var(--border-color, #333333) !important;
  color: var(--text-color, #e0e0e0) !important;
}

[data-theme="dark"] .text-segment.highlighted {
  border-color: var(--primary-color, #4a9eff) !important;
  background: rgba(74, 158, 255, 0.1) !important;
  box-shadow: 0 2px 8px rgba(74, 158, 255, 0.2) !important;
  border-left: 3px solid var(--primary-color, #4a9eff) !important;
}

/* 滚动条样式 */
.text-content::-webkit-scrollbar {
  width: 6px;
}

.text-content::-webkit-scrollbar-track {
  background: var(--border-color, #f1f1f1);
  border-radius: 3px;
}

.text-content::-webkit-scrollbar-thumb {
  background: var(--text-secondary, #c1c1c1);
  border-radius: 3px;
}

.text-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-color, #a8a8a8);
}
</style>
