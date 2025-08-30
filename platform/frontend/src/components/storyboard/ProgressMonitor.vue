<template>
  <div class="progress-monitor">
    <a-card>
      <div class="progress-content">
        <div class="progress-info">
          <div class="step-text">{{ currentStep || '准备中...' }}</div>
          <a-progress 
            :percent="progress" 
            :status="progressStatus"
            :stroke-color="progressColor"
          />
        </div>
        <div class="connection-status">
          <a-tag :color="isConnected ? 'green' : 'red'">
            {{ isConnected ? '已连接' : '连接中...' }}
          </a-tag>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'

const props = defineProps({
  sessionId: String
})

const emit = defineEmits(['progress-update'])

// WebSocket状态
const { isConnected, progress, currentStep, error } = useWebSocket(props.sessionId)

// 计算属性
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
.progress-monitor {
  margin-bottom: 16px;
}

.progress-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.progress-info {
  flex: 1;
}

.step-text {
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

.connection-status {
  flex-shrink: 0;
}
</style>
