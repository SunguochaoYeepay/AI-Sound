<template>
  <div class="batch-operation-panel">
    <div class="batch-header">
      <h3>批量操作 ({{ selectedTracks.size }} 个轨道)</h3>
      <div class="batch-stats">
        <a-space>
          <a-tag color="green">{{ needGenerationCount }} 需生成</a-tag>
          <a-tag color="blue">{{ selectedTracks.size - needGenerationCount }} 已匹配</a-tag>
        </a-space>
      </div>
    </div>
    
    <div class="batch-actions">
      <a-space>
        <a-button 
          type="primary" 
          :disabled="needGenerationCount === 0"
          @click="$emit('generate')"
        >
          批量生成 ({{ needGenerationCount }})
        </a-button>
        <a-button @click="$emit('clear-selection')">
          清除选择
        </a-button>
      </a-space>
    </div>
    
    <div class="batch-tracks">
      <div 
        v-for="track in selectedTracks" 
        :key="track.segment_id"
        class="batch-track-item"
      >
        <div class="batch-track-info">
          <span class="track-time">{{ formatTime(track.start_time) }}</span>
          <span class="track-keywords">{{ track.environment_keywords.join(', ') }}</span>
          <span class="track-status" :class="{ 'need-generation': !track.has_match }">
            {{ track.has_match ? '已匹配' : '需生成' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  selectedTracks: {
    type: Array,
    default: () => []
  },
  needGenerationCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['generate', 'clear-selection'])

const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.batch-operation-panel {
  padding: 24px;
}

.batch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.batch-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--ant-text-color);
}

.batch-stats {
  font-size: 14px;
  color: var(--ant-text-color-secondary);
}

.batch-actions {
  margin-bottom: 16px;
}

.batch-tracks {
  max-height: 300px;
  overflow-y: auto;
}

.batch-track-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  border-radius: 6px;
  background-color: var(--ant-item-hover-bg);
}

.batch-track-info {
  flex: 1;
  font-size: 14px;
  color: var(--ant-text-color);
}

.batch-track-info .track-time {
  font-weight: 500;
  margin-right: 8px;
}

.batch-track-info .track-keywords {
  margin-right: 8px;
}

.batch-track-info .track-status {
  font-weight: 500;
  color: var(--ant-success-color);
}

.batch-track-info .track-status.need-generation {
  color: var(--ant-warning-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-operation-panel {
    padding: 16px;
  }
  
  .batch-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
