<template>
  <div class="chapter-actions">
    <a-space>
      <!-- 开始合成按钮 -->
      <a-button 
        type="primary"
        :disabled="!canStart"
        :loading="startLoading"
        @click="$emit('startSynthesis')"
        v-if="!synthesisRunning"
      >
        🎵 开始合成
      </a-button>

      <!-- 暂停/继续按钮 -->
      <template v-if="synthesisRunning">
        <a-button 
          type="primary" 
          danger
          :loading="pauseLoading"
          @click="$emit('pauseSynthesis')"
        >
          ⏸️ 暂停
        </a-button>
        
        <a-button 
          type="primary" 
          danger
          :loading="cancelLoading"
          @click="$emit('cancelSynthesis')"
        >
          ⏹️ 取消
        </a-button>
      </template>

      <!-- 重试按钮 -->
      <a-button 
        v-if="!synthesisRunning && isFailed"
        type="primary"
        :loading="retryLoading"
        @click="$emit('retryFailedSegments')"
      >
        🔄 重试失败段落
      </a-button>

      <!-- 重置按钮 -->
      <a-dropdown v-if="isFailed || (synthesisRunning && !synthesisRunning)">
        <a-button size="small" type="primary">
          🔄 重新合成
          <DownOutlined />
        </a-button>
        <template #overlay>
          <a-menu>
            <a-menu-item @click="$emit('restartSynthesis')" style="color: #1890ff;">
              🔄 重新开始合成
            </a-menu-item>
            <a-menu-item @click="$emit('resetProjectStatus')" style="color: #ff4d4f;">
              🔧 重置状态（高级）
            </a-menu-item>
            <a-menu-item @click="$emit('refresh')" v-if="showRefresh">
              🔄 刷新数据
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </a-space>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { DownOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  chapterId: {
    type: [Number, String],
    default: null
  },
  canStart: {
    type: Boolean,
    default: false
  },
  synthesisRunning: {
    type: Boolean,
    default: false
  },
  showRefresh: {
    type: Boolean,
    default: false
  },
  isFailed: {
    type: Boolean,
    default: false
  },
  // Loading states
  startLoading: {
    type: Boolean,
    default: false
  },
  playLoading: {
    type: Boolean,
    default: false
  },
  pauseLoading: {
    type: Boolean,
    default: false
  },
  cancelLoading: {
    type: Boolean,
    default: false
  },
  resumeLoading: {
    type: Boolean,
    default: false
  },
  retryLoading: {
    type: Boolean,
    default: false
  },
  refreshLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits([
  'startSynthesis',
  'playAudio', 
  'downloadAudio',
  'pauseSynthesis',
  'cancelSynthesis',
  'resumeSynthesis',
  'retryFailedSegments',
  'restartSynthesis',
  'refresh',
  'resetProjectStatus'
])
</script>

<style scoped>
.chapter-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
</style> 