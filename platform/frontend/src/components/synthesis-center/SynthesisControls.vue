<template>
  <div class="chapter-actions">
    <!-- 手动刷新按钮 -->
    <a-button 
      v-if="showRefresh"
      @click="$emit('refresh')"
      :loading="refreshLoading"
      size="small"
      type="text"
    >
      🔄 刷新
    </a-button>
    
    <!-- 简化的章节操作按钮 -->
    <a-space size="small">
      <!-- 主要操作按钮 -->
      <template v-if="isPending">
        <a-button
          type="primary"
          size="small"
          :disabled="!canStart"
          :loading="startLoading"
          @click="$emit('startSynthesis', chapterId)"
        >
          开始合成
        </a-button>
      </template>

      <template v-if="isCompleted">
        <a-button
          type="primary"
          size="small"
          @click="$emit('playAudio', chapterId)"
          :loading="playLoading"
        >
          播放
        </a-button>
        <a-button
          size="small"
          @click="$emit('downloadAudio', chapterId)"
        >
          下载
        </a-button>
      </template>

      <template v-if="isProcessing">
        <a-button
          size="small"
          @click="$emit('pauseSynthesis')"
          :loading="pauseLoading"
        >
          暂停
        </a-button>
        <a-button
          size="small"
          @click="$emit('cancelSynthesis')"
          :loading="cancelLoading"
        >
          取消
        </a-button>
      </template>

      <template v-if="isPausedOrPartiallyFailed">
        <a-button
          type="primary"
          size="small"
          @click="$emit('resumeSynthesis', chapterId)"
          :loading="resumeLoading"
        >
          继续
        </a-button>
      </template>

      <template v-if="isFailed">
        <a-button
          type="primary"
          size="small"
          @click="$emit('retryFailedSegments', chapterId)"
          :loading="retryLoading"
        >
          重试
        </a-button>
      </template>
      
      <!-- 更多操作下拉菜单 -->
      <a-dropdown v-if="isCompleted">
        <a-button size="small">
          更多
          <DownOutlined />
        </a-button>
        <template #overlay>
          <a-menu>
            <a-menu-item @click="$emit('restartSynthesis', chapterId)">
              重新合成
            </a-menu-item>
            <a-menu-item @click="$emit('refresh')" v-if="showRefresh">
              刷新数据
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
  projectStatus: {
    type: String,
    default: 'pending'
  },
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
  'refresh'
])

// 计算状态
const isPending = computed(() => {
  return ['pending', 'failed', 'configured'].includes(props.projectStatus)
})

const isCompleted = computed(() => {
  return getDisplayStatus(props.projectStatus) === 'completed'
})

const isProcessing = computed(() => {
  return props.projectStatus === 'processing'
})

const isPausedOrPartiallyFailed = computed(() => {
  return props.projectStatus === 'paused' || 
         (props.projectStatus === 'failed' && props.statistics?.completedSegments > 0)
})

const isFailed = computed(() => {
  return getDisplayStatus(props.projectStatus) === 'failed'
})

// 智能状态显示
const getDisplayStatus = (rawStatus) => {
  if (rawStatus === 'partial_completed') {
    // 这里需要从父组件传入统计数据来判断
    // 暂时保持原状态
    return rawStatus
  }
  return rawStatus
}
</script>

<style scoped>
.chapter-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
</style> 