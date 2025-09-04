<template>
  <div class="script-segment-list">
    <div v-if="sixCardResults && sixCardResults.length > 0" class="paragraph-scripts">
      <div class="script-list">
        <div 
          v-for="(result, index) in sortedSixCardResults" 
          :key="result._metadata?.segment_index || index"
          class="script-item"
          :class="{ 'highlighted': highlightedSegmentIndex === result._metadata?.segment_index }"
          @click="$emit('show-analysis', result)"
        >
          <div class="script-header">
            <span class="script-title">段落 {{ result._metadata?.segment_index || index + 1 }} 剧本</span>
            <span class="script-time">{{ result._metadata?.analysis_time ? new Date(result._metadata.analysis_time).toLocaleString() : '' }}</span>
            <a-button type="link" size="small" class="view-analysis-btn">
              <template #icon>
                <EyeOutlined />
              </template>
              查看6卡分析
            </a-button>
          </div>
          
          <!-- 剧本内容预览 -->
          <div class="script-preview">
            <div v-if="result.synthesis_json?.synthesis_plan" class="synthesis-plan">
              <div 
                v-for="(segment, segIndex) in result.synthesis_json.synthesis_plan" 
                :key="segIndex"
                class="synthesis-segment"
              >
                <div class="segment-info">
                  <span class="speaker">{{ segment.speaker }}</span>
                  <span class="duration">{{ segment.duration_seconds }}秒</span>
                  <span class="word-count">{{ segment.word_count }}字</span>
                </div>
                <div class="segment-text">{{ segment.text }}</div>
              </div>
            </div>
            
            <!-- 如果没有synthesis_json，显示基本信息 -->
            <div v-else class="basic-info">
              <p><strong>段落文本:</strong> {{ result._metadata?.segment_text?.substring(0, 100) }}...</p>
              <p><strong>分析状态:</strong> 已完成</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="!sixCardResults || sixCardResults.length === 0" class="empty-content">
      <p>暂无数据</p>
    </div>
  </div>
</template>

<script setup>
import { computed, watch, nextTick } from 'vue'
import { EyeOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  sixCardResults: {
    type: Array,
    default: () => []
  },
  highlightedSegmentIndex: {
    type: Number,
    default: null
  }
})

// Emits
const emit = defineEmits(['show-analysis'])

// Computed properties
const sortedSixCardResults = computed(() => {
  return props.sixCardResults || []
})

// 监听高亮段落索引变化，自动滚动到对应位置
watch(() => props.highlightedSegmentIndex, (newIndex) => {
  console.log('右侧接收到高亮索引变化:', newIndex)
  if (newIndex !== null && newIndex !== undefined) {
    // 延迟执行，确保DOM已更新
    nextTick(() => {
      const highlightedElement = document.querySelector('.script-item.highlighted')
      console.log('查找高亮元素:', highlightedElement)
      if (highlightedElement) {
        console.log('开始滚动到高亮元素')
        highlightedElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        })
      } else {
        console.log('未找到高亮元素，当前高亮索引:', newIndex)
        console.log('所有段落剧本:', props.sixCardResults)
      }
    })
  }
})
</script>

<style scoped>
@import '@/assets/styles/storyboard.css';
</style>
