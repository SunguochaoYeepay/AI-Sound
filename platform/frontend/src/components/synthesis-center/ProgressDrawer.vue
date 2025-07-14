<template>
  <a-drawer
    :open="visible"
    :title="drawerTitle"
    placement="bottom"
    :height="220"
    :closable="true"
    @close="$emit('close')"
    @update:open="$emit('update:visible', $event)"
  >
    <div class="progress-container">
      <!-- 简化的进度显示 -->
      <div class="simple-progress">
         <!-- 章节进度统计 -->
         <div class="chapter-info">
          <div class="chapter-stats">
            <span class="stat-item">
              <span class="stat-label">段落进度:</span>
              <span class="stat-value completed">{{ chapterProgress.completed }}</span>
              <span class="stat-separator">/</span>
              <span class="stat-value total">{{ chapterProgress.total }}</span>
            </span>
          </div>
           <!-- 合成控制按钮 -->
        <div class="synthesis-controls" v-if="showSynthesisControls">
          <a-space size="small">
            <a-button 
              v-if="showPauseButton"
              size="small"
              @click="handlePause"
              :loading="pauseLoading"
              danger
            >
              ⏸️ 暂停
            </a-button>
            <a-button 
              size="small"
              @click="handleCancel"
              :loading="cancelLoading"
              danger
            >
              ❌ 取消
            </a-button>
          </a-space>
        </div>
        </div>
       
        
        <!-- 进度条 -->
        <a-progress 
          :percent="correctProgress" 
          :status="progressStatus"
          :stroke-color="progressColor"
          :show-info="true"
          size="default"
        />
        
       

        
        <!-- 简化的错误提示 -->
        <div class="simple-error-notice" v-if="displayStatus === 'failed'">
          <a-space>
            <a-tag color="error" size="small">
              ❌ 章节合成失败
            </a-tag>
            <a-button 
              size="small" 
              type="default" 
              @click="$emit('retryFailedSegments')" 
              :loading="retryLoading"
            >
              🔄 重试章节合成
            </a-button>
          </a-space>
        </div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  progressData: {
    type: Object,
    required: true
  },
  chapterProgress: {
    type: Object,
    default: () => ({ completed: 0, total: 0, percent: 0 })
  },
  projectStatus: {
    type: String,
    default: 'pending'
  },
  elapsedTime: {
    type: Number,
    default: 0
  },
  wsConnected: {
    type: Boolean,
    default: false
  },
  // 🔧 新增：章节信息props
  selectedChapter: {
    type: Number,
    default: null
  },
  chapters: {
    type: Array,
    default: () => []
  },
  // Loading states
  pauseLoading: {
    type: Boolean,
    default: false
  },
  cancelLoading: {
    type: Boolean,
    default: false
  },
  retryLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'pauseSynthesis', 'cancelSynthesis', 'retryFailedSegments', 'showFailureDetails'])

// 计算当前章节信息
const currentChapterInfo = computed(() => {
  if (!props.selectedChapter || !props.chapters.length) {
    return null
  }
  
  const chapter = props.chapters.find(ch => ch.id === props.selectedChapter)
  if (!chapter) {
    return null
  }
  
  return {
    id: chapter.id,
    number: chapter.chapter_number || chapter.number,
    title: `第${chapter.chapter_number || chapter.number}章 ${chapter.chapter_title || chapter.title || ''}`.trim(),
    rawTitle: chapter.chapter_title || chapter.title
  }
})

// 处理函数
const handlePause = () => {
  console.log('📌 暂停按钮被点击')
  emit('pauseSynthesis')
}

const handleCancel = () => {
  console.log('📌 取消按钮被点击')
  emit('cancelSynthesis')
}

// 计算属性
const showSynthesisControls = computed(() => {
  // 如果项目状态是processing或paused，显示控制按钮
  if (props.projectStatus === 'processing' || props.projectStatus === 'paused') {
    return true
  }
  
  // 如果进度状态显示正在运行，也显示控制按钮
  const progressStatus = props.progressData.status
  if (progressStatus === 'processing' || progressStatus === 'running') {
    return true
  }
  
  return false
})

const showPauseButton = computed(() => {
  // 只有在真正处理中时才显示暂停按钮
  return props.projectStatus === 'processing' || props.progressData.status === 'processing' || props.progressData.status === 'running'
})

const drawerTitle = computed(() => {
  // 🔥 包含章节信息的抽屉标题
  if (currentChapterInfo.value) {
    return `🎤 ${currentChapterInfo.value.title} - 语音合成监控`
  }
  return '🎤 章节语音合成监控'
})



const displayStatus = computed(() => {
  // 🔥 基于章节进度判断状态
  const chapterCompleted = props.chapterProgress.completed || 0
  const chapterTotal = props.chapterProgress.total || 0
  const chapterPercent = props.chapterProgress.percent || 0
  
  // 如果章节完全完成
  if (chapterTotal > 0 && chapterCompleted === chapterTotal) {
    return 'completed'
  }
  
  // 如果章节有进度但未完成
  if (chapterTotal > 0 && chapterCompleted > 0) {
    return 'active'
  }
  
  // 其他情况使用项目状态
  return props.progressData.status
})

const correctProgress = computed(() => {
  // 🔥 只使用章节进度数据，不再考虑项目级别数据
  const chapterPercent = props.chapterProgress.percent || 0
  
  console.log('🔍 章节进度显示:', {
    completed: props.chapterProgress.completed,
    total: props.chapterProgress.total,
    percent: chapterPercent
  })
  
  return chapterPercent
})

const progressStatus = computed(() => {
  const status = displayStatus.value
  if (status === 'failed') {
    return 'exception'
  } else if (status === 'completed') {
    return 'success'
  } else if (status === 'active' && props.chapterProgress.percent === 100) {
    return 'success'
  }
  return 'active'
})

const progressColor = computed(() => {
  const status = displayStatus.value
  if (status === 'completed' || props.chapterProgress.percent === 100) {
    return '#52c41a'
  } else if (status === 'failed') {
    return '#ff4d4f'
  } else if (status === 'active') {
    return '#1890ff'
  }
  return '#1890ff'
})
</script>

<style scoped>
.progress-container {
  padding: 16px 24px;
}

.synthesis-controls {
  justify-content: flex-end;
  margin-bottom: 12px;
  gap: 24px;

}

.chapter-info {
  margin-top: 12px;
  display: flex;
  gap:12px;


}

.chapter-stats {
  display: flex;
  gap: 12px;
  font-size: 13px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-percent {
  font-weight: 600;
  color: #1890ff;
  margin-left: 4px;
}

.stat-label {
  color: #666;
  font-weight: 500;
}

.stat-value {
  font-weight: 600;
}

.stat-value.completed {
  color: #52c41a;
}

.stat-value.total {
  color: #1890ff;
}

.stat-value.failed {
  color: #ff4d4f;
}

.stat-value.time {
  color: #1890ff;
}

.stat-separator {
  color: #d9d9d9;
  font-weight: 400;
}

.current-status {
  margin-top: 12px;
}

.status-text {
  font-size: 12px;
  color: #1890ff;
  background: #f0f7ff;
  padding: 4px 8px;
  border-radius: 4px;
  border-left: 3px solid #1890ff;
}

.simple-error-notice {
  margin-top: 12px;
  padding: 8px;
  background: #fff2f0;
  border-radius: 6px;
  border-left: 3px solid #ff4d4f;
}

.persistent-success-notice .success-notice-content .success-summary {
  font-size: 12px;
  line-height: 1.4;
  opacity: 0.9;
}

.failure-details {
  margin-top: 16px;
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.failure-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.failure-title {
  font-size: 14px;
  font-weight: 600;
  color: #dc2626;
}

.failure-reasons {
  margin-bottom: 12px;
}

.failure-reason-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
}

.reason-icon {
  margin-right: 8px;
  font-size: 14px;
}

.reason-text {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

/* 暗黑模式适配 */
[data-theme="dark"] .stat-label {
  color: #8c8c8c !important;
}

[data-theme="dark"] .status-text {
  background: rgba(var(--primary-color-rgb), 0.1) !important;
  color: var(--primary-color) !important;
  border-left-color: var(--primary-color) !important;
}

[data-theme="dark"] .simple-error-notice {
  background: rgba(255, 77, 79, 0.1) !important;
  border-left-color: #ff4d4f !important;
  color: #ff4d4f !important;
}

[data-theme="dark"] .failure-details {
  background: rgba(255, 77, 79, 0.05) !important;
  border-color: rgba(255, 77, 79, 0.2) !important;
}

[data-theme="dark"] .failure-title {
  color: #ff4d4f !important;
}

[data-theme="dark"] .reason-text {
  color: #8c8c8c !important;
}

/* 移动端响应式设计 */
@media (max-width: 768px) {
  .progress-container {
    padding: 12px 16px;
  }
  
  .simple-progress .progress-title-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
    margin-bottom: 8px;
  }
  
  .progress-title {
    font-size: 14px;
    text-align: center;
  }
  
  .synthesis-controls {
    align-self: center;
  }
  
  .synthesis-controls .ant-space {
    flex-direction: column !important;
    width: 100% !important;
  }
  
  .synthesis-controls .ant-space-item {
    width: 100% !important;
  }
  
  .synthesis-controls .ant-btn {
    width: 100% !important;
    margin: 0 !important;
  }
  
  .compact-stats {
    flex-direction: column;
    gap: 8px;
    margin-top: 8px;
    font-size: 12px;
  }
  
  .stat-item {
    justify-content: center;
  }
  
  .simple-error-notice {
    margin-top: 8px;
    padding: 6px;
  }
  
  .simple-error-notice .ant-space {
    flex-direction: column !important;
    width: 100% !important;
  }
  
  .simple-error-notice .ant-space-item {
    width: 100% !important;
  }
  
  .simple-error-notice .ant-btn {
    width: 100% !important;
  }
  
  .failure-details {
    margin-top: 12px;
    padding: 12px;
  }
  
  .failure-header {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .progress-container {
    padding: 8px 12px;
  }
  
  .progress-title {
    font-size: 13px;
  }
  
  .compact-stats {
    font-size: 11px;
  }
  
  .synthesis-controls .ant-btn {
    font-size: 12px;
    height: 28px;
  }
  
  .simple-error-notice .ant-btn {
    font-size: 12px;
    height: 28px;
  }
}
</style> 