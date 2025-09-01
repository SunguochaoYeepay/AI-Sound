<template>
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
          <ScriptSegment 
            v-for="(script, index) in scriptSegments" 
            :key="index"
            :script="script"
            :related-cards="getRelatedCards(script)"
            @segment-click="handleSegmentClick(index)"
            @card-click="handleCardClick"
          />
        </div>
        <div v-else class="empty-content">
          <p>暂无剧本数据</p>
        </div>
      </div>
    </div>

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
import { ref } from 'vue'
import { ExclamationCircleOutlined } from '@ant-design/icons-vue'
import ScriptSegment from './ScriptSegment.vue'

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
  }
})

// Emits
const emit = defineEmits(['segment-click', 'card-click'])

// Reactive data
const showIssuesDrawer = ref(false)

// Methods
const handleSegmentClick = (index) => {
  emit('segment-click', index)
}

const handleCardClick = (card) => {
  emit('card-click', card)
}

const getRelatedCards = (script) => {
  const cards = []
  
  // 检查是否有对应的卡片数据
  if (!props.reviewData?.cards) return cards
  
  // 根据剧本内容类型和内容智能关联卡片
  if (script.type === 'dialogue' && script.speaker) {
    // 对话类型：关联角色卡、事件卡、情绪卡
    if (props.reviewData.cards.character?.length > 0) {
      cards.push({ type: 'character', name: '角色卡', icon: '🎭' })
    }
    if (props.reviewData.cards.event?.length > 0) {
      cards.push({ type: 'event', name: '事件卡', icon: '📝' })
    }
    if (props.reviewData.cards.emotion?.length > 0) {
      cards.push({ type: 'emotion', name: '情绪卡', icon: '💝' })
    }
  }
  
  if (script.type === 'narration') {
    // 旁白类型：关联场景卡、故事卡
    if (props.reviewData.cards.scene?.length > 0) {
      cards.push({ type: 'scene', name: '场景卡', icon: '🎬' })
    }
    if (props.reviewData.cards.story?.length > 0) {
      cards.push({ type: 'story', name: '故事卡', icon: '📖' })
    }
  }
  
  // 如果内容较长，可能包含更多信息，添加更多关联
  if (script.text && script.text.length > 30) {
    if (props.reviewData.cards.story?.length > 0 && !cards.find(c => c.type === 'story')) {
      cards.push({ type: 'story', name: '故事卡', icon: '📖' })
    }
    if (props.reviewData.cards.event?.length > 0 && !cards.find(c => c.type === 'event')) {
      cards.push({ type: 'event', name: '事件卡', icon: '📝' })
    }
  }
  
  // 音频相关卡片：根据时间范围关联
  if (script.startTime && script.endTime) {
    if (props.reviewData.cards.audio_storyboard?.length > 0) {
      cards.push({ type: 'audio_storyboard', name: '音频分镜卡', icon: '🎵' })
    }
    if (props.reviewData.cards.audio_script?.length > 0) {
      cards.push({ type: 'audio_script', name: '音频剧本卡', icon: '📝' })
    }
  }
  
  return cards
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

.script-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--content-bg, #262626);
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

/* 滚动条样式 */
.script-content::-webkit-scrollbar {
  width: 6px;
}

.script-content::-webkit-scrollbar-track {
  background: var(--border-color, #f1f1f1);
  border-radius: 3px;
}

.script-content::-webkit-scrollbar-thumb {
  background: var(--text-secondary, #c1c1c1);
  border-radius: 3px;
}

.script-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-color, #a8a8a8);
}

/* 深色主题下的特殊样式覆盖 */
[data-theme="dark"] .panel-header {
  background: var(--header-bg, #262626) !important;
  border-color: var(--border-color, #333333) !important;
}

[data-theme="dark"] .panel-content {
  background: var(--content-bg, #1a1a1a) !important;
}
</style>
