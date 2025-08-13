<template>
  <div class="tracks-selector">
    <div class="selector-header">
      <h3>环境音轨道</h3>
      <div class="selector-stats">
        <a-space>
          <a-tag color="blue">{{ tracks.length }} 个轨道</a-tag>
          <a-tag color="green">{{ needGenerationCount }} 需生成</a-tag>
          <a-tag color="orange">{{ selectedTracks.size }} 已选择</a-tag>
        </a-space>
      </div>
    </div>
    
    <div class="selector-actions">
      <a-space>
        <a-button size="small" @click="$emit('select-all')">
          全选
        </a-button>
        <a-button size="small" @click="$emit('clear-selection')">
          清除
        </a-button>
      </a-space>
    </div>

    <div class="tracks-list">
      <div 
        v-for="track in tracks" 
        :key="track.segment_id"
        class="track-item"
        :class="{ 
          'selected': selectedTracks.has(track.segment_id),
          'has-match': track.has_match,
          'need-generation': !track.has_match
        }"
        @click="$emit('track-select', track.segment_id)"
      >
        <div class="track-header">
          <a-checkbox
            :checked="selectedTracks.has(track.segment_id)"
            @click.stop
            @change="(e) => $emit('selection-change', track.segment_id, e.target.checked)"
          />
          <div class="track-status">
            <CheckCircleOutlined v-if="track.has_match" class="status-icon success" />
            <ClockCircleOutlined v-else class="status-icon warning" />
          </div>
        </div>
        
        <div class="track-info">
          <div class="track-time">
            {{ formatTime(track.start_time) }} - {{ formatTime(track.start_time + track.duration) }}
          </div>
          <div class="track-keywords">
            <a-tag 
              v-for="keyword in track.environment_keywords.slice(0, 2)" 
              :key="keyword"
              size="small"
            >
              {{ keyword }}
            </a-tag>
            <span v-if="track.environment_keywords.length > 2" class="more-keywords">
              +{{ track.environment_keywords.length - 2 }}
            </span>
          </div>
          <div class="track-confidence">
            <a-progress 
              :percent="track.confidence * 100" 
              :show-info="false"
              size="small"
            />
            <span class="confidence-text">{{ (track.confidence * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons-vue'

defineProps({
  tracks: {
    type: Array,
    default: () => []
  },
  selectedTracks: {
    type: Set,
    default: () => new Set()
  },
  needGenerationCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['selection-change', 'track-select', 'select-all', 'clear-selection'])

const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.tracks-selector {
  flex: 1;
  background-color: var(--ant-component-background);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px var(--ant-box-shadow);
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.selector-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--ant-text-color);
}

.selector-stats {
  font-size: 14px;
  color: var(--ant-text-color-secondary);
}

.selector-actions {
  margin-bottom: 16px;
}

.tracks-list {
  max-height: 400px;
  overflow-y: auto;
}

.track-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  border-radius: 6px;
  background-color: var(--ant-item-hover-bg);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.track-item:hover {
  background-color: var(--ant-item-active-bg);
}

.track-item.selected {
  background-color: var(--ant-primary-1);
  border: 1px solid var(--ant-primary-color);
}

.track-item.has-match .track-status .status-icon {
  color: var(--ant-success-color);
}

.track-item.need-generation .track-status .status-icon {
  color: var(--ant-warning-color);
}

.track-header {
  display: flex;
  align-items: center;
  margin-right: 12px;
}

.track-status {
  display: flex;
  align-items: center;
  margin-left: 8px;
}

.track-status .status-icon {
  font-size: 16px;
}

.track-info {
  flex: 1;
}

.track-time {
  font-size: 14px;
  color: var(--ant-text-color-secondary);
  margin-bottom: 4px;
}

.track-keywords {
  font-size: 14px;
  color: var(--ant-text-color);
  margin-bottom: 4px;
}

.track-keywords .more-keywords {
  color: var(--ant-text-color-secondary);
}

.track-confidence {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--ant-text-color-secondary);
}

.track-confidence .confidence-text {
  margin-left: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tracks-selector {
    padding: 16px;
  }
  
  .selector-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
