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
  }
})

defineEmits(['playSegment'])

// 获取角色样式类
const getCharacterClass = (speaker) => {
  const colors = ['primary', 'warning', 'success', 'info', 'error']
  const hash = speaker.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return `character-${colors[hash % colors.length]}`
}

// 获取段落状态文本
const statusText = computed(() => {
  if (props.isCompleted) {
    return '已完成'
  }
  
  if (props.projectStatus === 'processing') {
    if (props.segmentIndex === props.currentSegment) {
      return '合成中'
    } else if (props.segmentIndex < props.currentSegment) {
      return '已完成'
    } else {
      return '等待中'
    }
  }
  
  return '未开始'
})

// 获取段落状态颜色
const statusColor = computed(() => {
  const colors = {
    '已完成': 'green',
    '合成中': 'blue',
    '等待中': 'orange',
    '未开始': 'default'
  }
  return colors[statusText.value] || 'default'
})
</script>

<style scoped>
.dialogue-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.dialogue-bubble:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.dialogue-bubble.narrator {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-color: #0ea5e9;
}

.dialogue-bubble.character {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: #f59e0b;
}

.bubble-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.speaker-name {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.segment-index {
  font-size: 11px;
  color: #666;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 10px;
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

.dialogue-bubble.has-audio {
  border-left: 3px solid #52c41a;
}

.dialogue-bubble.has-audio:hover {
  box-shadow: 0 2px 8px rgba(82, 196, 26, 0.1);
}

.bubble-content {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
}

/* 角色样式类 */
.character-primary .speaker-name {
  color: #1890ff !important;
}

.character-warning .speaker-name {
  color: #fa8c16 !important;
}

.character-success .speaker-name {
  color: #52c41a !important;
}

.character-info .speaker-name {
  color: #13c2c2 !important;
}

.character-error .speaker-name {
  color: #f5222d !important;
}
</style> 