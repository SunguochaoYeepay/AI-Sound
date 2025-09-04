<template>
  <div class="script-segment" :class="{ 'highlighted': script.highlighted }" @click="handleSegmentClick">
    <div class="script-header">
      <div class="script-time">{{ script.startTime }}-{{ script.endTime }}s</div>
      <div class="script-type">
        <a-tag :color="script.type === 'dialogue' ? 'blue' : 'green'">
          {{ script.type === 'dialogue' ? '对话' : '旁白' }}
        </a-tag>
      </div>
      <div class="script-actions">
        <a-button
          size="small"
          type="primary"
          @click.stop="analyzeSegment"
          :loading="analyzing"
        >
          <template #icon>
            <AppstoreOutlined />
          </template>
                      段落分析
        </a-button>
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
      <RelatedCards 
        :cards="relatedCards" 
        @card-click="handleCardClick"
      />
      
      <!-- 问题标记 -->
      <div v-if="script.issues && script.issues.length > 0" class="script-issues">
        <a-tag v-for="issue in script.issues" :key="issue.type" :color="getIssueColor(issue.type)" size="small">
          {{ issue.message }}
        </a-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import RelatedCards from './RelatedCards.vue'
import { AppstoreOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  script: {
    type: Object,
    required: true
  },
  relatedCards: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['segment-click', 'card-click', 'six-card-analysis'])

const analyzing = ref(false)

// Methods
const handleSegmentClick = () => {
  emit('segment-click')
}

const handleCardClick = (card) => {
  emit('card-click', card)
}

const analyzeSegment = async () => {
  if (analyzing.value) return

  analyzing.value = true
  try {
          console.log('开始对段落进行段落分析:', props.script.id || props.script.segment_id)

          // 发送段落分析事件，包含段落信息
    emit('six-card-analysis', {
      segment: props.script,
      segmentIndex: props.script.id || props.script.segment_id
    })

    // 模拟分析过程
    setTimeout(() => {
              console.log('单个段落段落分析完成')
      analyzing.value = false
    }, 2000)

  } catch (error) {
          console.error('段落分析失败:', error)
    analyzing.value = false
  }
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

.script-actions {
  display: flex;
  gap: 8px;
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

.script-issues {
  margin-top: 12px;
}

/* 深色主题下的特殊样式覆盖 */
[data-theme="dark"] .script-segment {
  background: var(--item-bg, #1a1a1a) !important;
  border-color: var(--border-color, #333333) !important;
  color: var(--text-color, #e0e0e0) !important;
}

[data-theme="dark"] .script-segment.highlighted {
  border-color: var(--primary-color, #4a9eff) !important;
  background: rgba(74, 158, 255, 0.1) !important;
  box-shadow: 0 2px 8px rgba(74, 158, 255, 0.2) !important;
  border-left: 3px solid var(--primary-color, #4a9eff) !important;
}

[data-theme="dark"] .text-content {
  background: var(--segment-bg, #262626) !important;
  color: var(--text-color, #e0e0e0) !important;
  border-left-color: var(--primary-color, #4a9eff) !important;
}
</style>
