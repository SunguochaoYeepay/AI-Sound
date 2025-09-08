<template>
  <div class="progress-monitor">
    <!-- 迷你进度条 -->
    <div
      v-if="showMiniProgress"
      class="mini-progress-bar"
      @click="showDetailedProgress = true"
    >
      <div class="mini-progress-content">
        <span class="mini-progress-text">
          {{ currentStep || '准备中...' }}
        </span>
        <a-progress
          :percent="progress"
          :show-info="false"
          size="small"
          :stroke-color="progressColor"
        />
        <span class="mini-progress-tip">📊</span>
      </div>
    </div>

    <!-- 详细进度抽屉 -->
    <a-drawer
      :open="showDetailedProgress"
      title="📊 分析进度监控"
      placement="bottom"
      :height="200"
      :closable="true"
      @close="showDetailedProgress = false"
    >
      <div class="detailed-progress">
        <div class="progress-info">
          <div class="step-text">{{ currentStep || '准备中...' }}</div>
          <a-progress 
            :percent="progress" 
            :status="progressStatus"
            :stroke-color="progressColor"
            :show-info="true"
          />
        </div>
        <div class="connection-status">
          <a-tag :color="isConnected ? 'green' : 'red'">
            {{ isConnected ? '已连接' : '连接中...' }}
          </a-tag>
        </div>
        <div v-if="error" class="error-info">
          <a-tag color="error">❌ {{ error }}</a-tag>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'

const props = defineProps({
  projectId: [String, Number]
})

const emit = defineEmits(['progress-update'])

// WebSocket状态
const { isConnected, progress, currentStep, error } = useWebSocket(props.projectId)

// 显示状态
const showDetailedProgress = ref(false)

// 计算属性
const showMiniProgress = computed(() => {
  // 只有在有进度时显示，连接状态不显示
  return progress.value > 0 && progress.value < 100
})

const progressStatus = computed(() => {
  if (error.value) return 'exception'
  if (progress.value >= 100) return 'success'
  return 'active'
})

const progressColor = computed(() => {
  if (error.value) return '#ff4d4f'
  if (progress.value >= 100) return '#52c41a'
  return '#1890ff'
})

// 监听进度更新
const handleProgressUpdate = () => {
  emit('progress-update', progress.value, currentStep.value)
}

// 监听进度变化
watch([progress, currentStep], () => {
  handleProgressUpdate()
})
</script>

<style scoped>


/* 迷你进度条样式 */
.mini-progress-bar {
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 8px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.mini-progress-bar:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  border-color: var(--primary-color, #1890ff);
}

.mini-progress-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mini-progress-text {
  font-size: 14px;
  color: var(--text-color, #333);
  font-weight: 500;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-progress-tip {
  font-size: 12px;
  color: var(--text-secondary, #666);
  white-space: nowrap;
}

/* 详细进度抽屉样式 */
.detailed-progress {
  padding: 16px;
}

.progress-info {
  margin-bottom: 16px;
}

.step-text {
  margin-bottom: 12px;
  font-size: 16px;
  color: var(--text-color, #333);
  font-weight: 500;
}

.connection-status {
  margin-bottom: 12px;
}

.error-info {
  margin-top: 12px;
  padding: 8px 12px;
  background: #fff2f0;
  border-radius: 6px;
  border-left: 3px solid #ff4d4f;
}

/* 暗黑模式适配 */
[data-theme='dark'] .mini-progress-bar {
  background: var(--card-bg, #1f1f1f);
  border-color: var(--border-color, #303030);
}

[data-theme='dark'] .error-info {
  background: rgba(255, 77, 79, 0.1);
  border-left-color: #ff4d4f;
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .mini-progress-content {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .mini-progress-text {
    text-align: center;
  }
  
  .mini-progress-tip {
    text-align: center;
  }
}
</style>
