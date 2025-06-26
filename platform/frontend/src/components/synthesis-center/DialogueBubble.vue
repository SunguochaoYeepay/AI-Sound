<template>
  <div 
    class="dialogue-bubble"
    :class="[getCharacterClass(segment.speaker), { 'has-audio': isCompleted }]"
  >
    <div class="bubble-header">
      <span class="speaker-name">{{ segment.speaker }}</span>
      <span class="segment-index">#{{ segmentIndex }}</span>
      
      <!-- 段落状态和播放按钮 -->
      <div class="segment-controls">
        <!-- 状态标签 -->
        <a-tag 
          :color="statusColor" 
          size="small"
          class="segment-status-tag"
        >
          {{ statusText }}
        </a-tag>
        
        <!-- 播放按钮 - 只在已完成时显示 -->
        <a-button
          v-if="isCompleted"
          type="text"
          size="small"
          @click="$emit('playSegment', segmentIndex, segment)"
          :loading="isPlaying"
          class="play-segment-btn"
          title="播放此段落"
        >
          <template v-if="isPlaying">
            ⏸️
          </template>
          <template v-else>
            ▶️
          </template>
        </a-button>
      </div>
    </div>
    
    <div class="bubble-content">{{ segment.text }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  segment: {
    type: Object,
    required: true
  },
  segmentIndex: {
    type: Number,
    required: true
  },
  isCompleted: {
    type: Boolean,
    default: false
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  projectStatus: {
    type: String,
    default: 'pending'
  },
  currentSegment: {
    type: Number,
    default: 0
  },
  projectId: {
    type: Number,
    required: false
  }
})

defineEmits(['playSegment'])

// 获取角色样式类
const getCharacterClass = (speaker) => {
  const speakerClasses = {
    '旁白': 'narrator',
    '叙述者': 'narrator',
    '作者': 'narrator'
  }
  
  return speakerClasses[speaker] || 'character'
}

// 计算状态颜色
const statusColor = computed(() => {
  if (props.isCompleted) return 'success'
  if (props.currentSegment === props.segmentIndex) return 'processing'
  return 'default'
})

// 计算状态文本
const statusText = computed(() => {
  if (props.isCompleted) return '已完成'
  if (props.currentSegment === props.segmentIndex) return '处理中'
  return '待处理'
})
</script>

<style scoped>
.dialogue-bubble {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  position: relative;
  transition: all 0.2s ease;
}

.dialogue-bubble:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.bubble-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.speaker-name {
  font-weight: 600;
  color: #334155;
  margin-right: 8px;
}

.segment-index {
  color: #64748b;
  font-size: 11px;
  background: #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 8px;
}

.segment-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.segment-status-tag {
  font-size: 11px;
  padding: 2px 6px;
}

.play-segment-btn {
  font-size: 12px;
  padding: 2px 6px;
  height: auto;
  min-width: auto;
  border: none;
  background: rgba(24, 144, 255, 0.1);
  color: #1890ff;
  border-radius: 4px;
}

.play-segment-btn:hover {
  background: rgba(24, 144, 255, 0.2);
  color: #1890ff;
}

.play-segment-btn:active {
  background: rgba(24, 144, 255, 0.3);
}

.bubble-content {
  line-height: 1.6;
  color: #1e293b;
  font-size: 14px;
  word-break: break-word;
}

.dialogue-bubble.has-audio {
  border-left: 3px solid #52c41a;
}

.dialogue-bubble.has-audio:hover {
  box-shadow: 0 2px 8px rgba(82, 196, 26, 0.1);
}

/* 角色样式 */
.dialogue-bubble.narrator {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-left: 3px solid #64748b;
}

.dialogue-bubble.character {
  background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
  border-left: 3px solid #f59e0b;
}

.environment-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

.environment-sounds {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.environment-tag {
  font-size: 10px !important;
  padding: 1px 6px !important;
  margin: 0 !important;
  cursor: help;
}

/* 环境音缺失提示样式 */
.environment-missing {
  margin: 8px 0 4px 0;
  padding: 6px 8px;
  border-top: 1px dashed #e2e8f0;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 6px;
  border: 1px solid #bae6fd;
}

.environment-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #0369a1;
}

.hint-icon {
  font-size: 12px;
  opacity: 0.8;
}

.hint-text {
  color: #0369a1;
  font-weight: 500;
}

.hint-button {
  font-size: 10px !important;
  padding: 2px 8px !important;
  height: 22px !important;
  color: #0284c7 !important;
  background: rgba(14, 165, 233, 0.1) !important;
  border: 1px solid #0ea5e9 !important;
  border-radius: 4px !important;
  transition: all 0.2s ease;
}

.hint-button:hover {
  color: #0369a1 !important;
  background: rgba(14, 165, 233, 0.2) !important;
  border-color: #0369a1 !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(14, 165, 233, 0.2);
}

/* 环境音详细信息样式 */
.environment-details {
  margin-top: 8px;
  border-top: 1px solid #e2e8f0;
  padding-top: 8px;
}

.env-detail-item {
  margin-bottom: 8px;
  padding: 6px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 3px solid #06b6d4;
}

.env-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.env-name {
  font-weight: 500;
  color: #0f172a;
  font-size: 12px;
}

.env-confidence {
  font-size: 10px;
  color: #64748b;
  background: #e2e8f0;
  padding: 1px 4px;
  border-radius: 3px;
}

.env-description {
  font-size: 11px;
  color: #475569;
  margin-bottom: 4px;
  line-height: 1.4;
}

.env-config {
  font-size: 10px;
  color: #64748b;
  font-style: italic;
}

.bubble-content {
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
  margin-top: 8px;
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .dialogue-bubble {
    padding: 10px 12px;
  }
  
/* 深色模式适配 */
[data-theme="dark"] .dialogue-bubble {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .dialogue-bubble:hover {
  background: #3a3a3a !important;
  border-color: #525252 !important;
}

[data-theme="dark"] .dialogue-bubble.narrator {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] .dialogue-bubble.character {
  background: linear-gradient(135deg, #451a03 0%, #78350f 100%) !important;
  border-color: #f59e0b !important;
}

[data-theme="dark"] .speaker-name {
  color: #fff !important;
}

[data-theme="dark"] .segment-index {
  color: #8c8c8c !important;
  background: #434343 !important;
}

[data-theme="dark"] .play-segment-btn {
  background: rgba(var(--primary-color-rgb), 0.2) !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] .play-segment-btn:hover {
  background: rgba(var(--primary-color-rgb), 0.3) !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] .play-segment-btn:active {
  background: rgba(var(--primary-color-rgb), 0.4) !important;
}

[data-theme="dark"] .dialogue-bubble.has-audio {
  border-left-color: #52c41a !important;
}

[data-theme="dark"] .dialogue-bubble.has-audio:hover {
  box-shadow: 0 2px 8px rgba(82, 196, 26, 0.2) !important;
}

[data-theme="dark"] .environment-tags {
  border-top-color: #434343 !important;
}

[data-theme="dark"] .environment-label {
  color: #8c8c8c !important;
}

[data-theme="dark"] .environment-missing {
  border-top-color: #434343 !important;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
  border-color: #0ea5e9 !important;
}

[data-theme="dark"] .environment-hint {
  color: var(--primary-color) !important;
}

[data-theme="dark"] .hint-text {
  color: var(--primary-color) !important;
}

[data-theme="dark"] .hint-button {
  color: var(--primary-color) !important;
  background: rgba(var(--primary-color-rgb), 0.2) !important;
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] .hint-button:hover {
  color: var(--secondary-color) !important;
  background: rgba(var(--primary-color-rgb), 0.3) !important;
  border-color: var(--secondary-color) !important;
}

[data-theme="dark"] .environment-details {
  border-top-color: #434343 !important;
}

[data-theme="dark"] .env-detail-item {
  background: #1f1f1f !important;
  border-left-color: var(--primary-color) !important;
}

[data-theme="dark"] .env-name {
  color: #fff !important;
}

[data-theme="dark"] .env-confidence {
  color: #8c8c8c !important;
  background: #434343 !important;
}

[data-theme="dark"] .env-description {
  color: #d1d5db !important;
}

[data-theme="dark"] .env-config {
  color: #8c8c8c !important;
}

[data-theme="dark"] .bubble-content {
  color: #d1d5db !important;
}

  .environment-tags {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .environment-sounds {
    width: 100%;
  }
}
</style> 