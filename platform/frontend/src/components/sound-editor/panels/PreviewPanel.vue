<template>
  <div class="preview-panel">
    <div class="panel-header">
      <h4>合成预览</h4>
    </div>
    <div class="panel-content">
      <div class="preview-area">
        <div class="waveform-display">
          <!-- 波形预览区域 -->
          <div class="waveform-container">
            <div class="waveform-placeholder">
              <div class="waveform-icon">📊</div>
              <div class="waveform-text">音频波形预览</div>
              <div class="waveform-info">
                {{ formatTime(currentTime) }} / {{ formatTime(totalDuration || 0) }}
              </div>
            </div>
          </div>
        </div>
        <div class="preview-controls">
          <a-slider
            :value="currentTime"
            :max="totalDuration || 1"
            :step="0.1"
            :disabled="!hasProject"
            style="flex: 1; margin-right: 12px"
            @change="$emit('time-change', $event)"
          />
          <a-space size="small">
            <a-button
              size="small"
              type="primary"
              @click="$emit('toggle-play')"
              :loading="isLoading"
              :disabled="!hasProject"
            >
              <template #icon>
                <PlayCircleOutlined v-if="!isPlaying && !isLoading" />
                <PauseCircleOutlined v-else-if="isPlaying" />
              </template>
              {{ isLoading ? '准备中' : isPlaying ? '播放' : '预览' }}
            </a-button>
            <a-button size="small" @click="$emit('stop')" :disabled="!hasProject">
              <template #icon><StopOutlined /></template>
              停止
            </a-button>
          </a-space>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { h } from 'vue'
  import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined } from '@ant-design/icons-vue'

  // Props
  const props = defineProps({
    currentTime: {
      type: Number,
      default: 0
    },
    totalDuration: {
      type: Number,
      default: 0
    },
    isPlaying: {
      type: Boolean,
      default: false
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    hasProject: {
      type: Boolean,
      default: false
    }
  })

  // Emits
  const emit = defineEmits(['toggle-play', 'stop', 'time-change'])

  // 格式化时间
  function formatTime(seconds) {
    if (!seconds || seconds < 0) return '00:00'
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
</script>

<style scoped>
  .preview-panel {
    background: #2a2a2a;
    display: flex;
    flex-direction: column;
    border-radius: 8px;
    border: 1px solid #333;
    flex: 4;
  }

  /* 面板头部 */
  .panel-header {
    padding: 8px;
    background: #333;
    border-bottom: 1px solid #444;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
  }

  .panel-header h4 {
    margin: 0;
    color: #fff;
    font-size: 14px;
    font-weight: 500;
  }

  /* 面板内容 */
  .panel-content {
    flex: 1;
    padding: 12px;
    overflow: auto;
  }

  /* 预览区域样式 */
  .preview-area {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .waveform-display {
    flex: 1;
    background: #1e1e1e;
    border-radius: 6px;
    margin-bottom: 16px;
  }

  .waveform-container {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .waveform-placeholder {
    text-align: center;
    color: #666;
  }

  .waveform-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }

  .waveform-text {
    font-size: 16px;
    margin-bottom: 8px;
  }

  .waveform-info {
    font-size: 14px;
    color: #999;
  }

  .preview-controls {
    display: flex;
    align-items: center;
  }

  .preview-controls :deep(.ant-slider) {
    flex: 1;
  }

  .preview-controls :deep(.ant-slider-rail) {
    background: #444;
  }

  .preview-controls :deep(.ant-slider-track) {
    background: #1890ff;
  }

  .preview-controls :deep(.ant-slider-handle) {
    border-color: #1890ff;
  }
</style>
