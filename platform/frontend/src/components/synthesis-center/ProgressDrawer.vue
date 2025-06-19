<template>
  <a-drawer
    :open="visible"
    title="🎵 合成进度监控"
    placement="bottom"
    :height="220"
    :closable="true"
    @close="$emit('close')"
    @update:open="$emit('update:visible', $event)"
  >
    <div class="progress-container">
      <!-- 简化的进度显示 -->
      <div class="simple-progress">
        <!-- 标题和控制按钮在一行 -->
        <div class="progress-title-row">
          <span class="progress-title">{{ progressTitle }}</span>
          
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
        
        <!-- 紧凑的统计信息 -->
        <div class="compact-stats">
          <span class="stat-item">
            <span class="stat-label">进度:</span>
            <span class="stat-value completed">{{ progressData.completed_segments }}</span>
            <span class="stat-separator">/</span>
            <span class="stat-value total">{{ progressData.total_segments }}</span>
          </span>
          
          <span class="stat-item" v-if="progressData.failed_segments > 0">
            <span class="stat-label">失败:</span>
            <span class="stat-value failed">{{ progressData.failed_segments }}</span>
          </span>
          
        </div>

        
        <!-- 简化的错误提示 -->
        <div class="simple-error-notice" v-if="displayStatus === 'failed'">
          <a-space>
            <a-tag color="error" size="small">
              ❌ {{ progressData.failed_segments }} 个段落合成失败
            </a-tag>
            <a-button 
              size="small" 
              type="primary" 
              @click="$emit('showFailureDetails')"
            >
              查看详情
            </a-button>
            <a-button 
              size="small" 
              type="default" 
              @click="$emit('retryFailedSegments')" 
              :loading="retryLoading"
            >
              🔄 重试失败段落
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

const progressTitle = computed(() => {
  const status = props.progressData.status
  const current = props.progressData.current_processing
  const completed = props.progressData.completed_segments
  const total = props.progressData.total_segments
  
  // 🔧 获取当前章节信息
  const getChapterInfo = () => {
    if (props.selectedChapter && props.chapters.length > 0) {
      const chapter = props.chapters.find(ch => ch.id === props.selectedChapter)
      if (chapter) {
        return `第${chapter.chapter_number || chapter.id}章：${chapter.title || '未命名章节'}`
      }
    }
    return '当前章节'
  }
  
  const chapterInfo = getChapterInfo()
  
  // 🔧 处理正在合成状态 - 显示当前段落详情和章节信息
  if (status === 'processing' || status === 'running') {
    if (current && current.trim()) {
      // 如果有具体的当前处理段落信息
      const currentText = current.length > 50 ? current.substring(0, 50) + '...' : current
      return `🎤 正在合成第${completed + 1}段: "${currentText}"`
    } else {
      // 没有具体段落信息时的回退显示
      return `🎤 合成进行中 - 第${completed + 1}/${total}段 - ${chapterInfo}`
    }
  }
  
  if (status === 'completed') {
    return `✅ 合成完成 - 共${total}个段落 - ${chapterInfo}`
  }
  
  if (status === 'failed') {
    return `❌ 合成失败 - 已完成${completed}/${total}段 - ${chapterInfo}`
  }
  
  if (status === 'paused') {
    return `⏸️ 合成已暂停 - 已完成${completed}/${total}段 - ${chapterInfo}`
  }
  
  if (total > 0) {
    return `📊 合成监控 - ${completed}/${total}段 - ${chapterInfo}`
  }
  
  return `📊 合成进度监控 - ${chapterInfo}`
})

const displayStatus = computed(() => {
  const status = props.progressData.status
  if (status === 'partial_completed') {
    const completed = props.progressData.completed_segments || 0
    const total = props.progressData.total_segments || 0
    const failed = props.progressData.failed_segments || 0
    
    if (total > 0 && completed === total && failed === 0) {
      return 'completed'
    }
    if (failed > 0) {
      return 'failed'
    }
  }
  return status
})

const correctProgress = computed(() => {
  const completed = props.progressData.completed_segments || 0
  const total = props.progressData.total_segments || 0
  const status = props.progressData.status
  
  console.log('🔍 correctProgress计算:', {
    status,
    completed,
    total,
    原始progress: props.progressData.progress
  })
  
  // 如果没有总段落数，返回0
  if (total === 0) {
    return 0
  }
  
  // 对于失败或部分完成状态，基于完成段落数计算进度
  if (status === 'failed' || status === 'partial_completed') {
    const calculatedProgress = Math.round((completed / total) * 100)
    console.log('🔍 计算结果:', calculatedProgress)
    return calculatedProgress
  }
  
  // 其他状态使用原始进度值
  return props.progressData.progress || 0
})

const progressStatus = computed(() => {
  if (props.progressData.status === 'failed') {
    return 'exception'
  } else if (props.progressData.status === 'completed') {
    return 'success'
  } else if (props.progressData.status === 'partial_completed') {
    return 'exception'
  }
  return 'active'
})

const progressColor = computed(() => {
  if (props.progressData.status === 'completed') {
    return '#52c41a'
  } else if (props.progressData.status === 'failed') {
    return '#ff4d4f'
  } else if (props.progressData.status === 'partial_completed') {
    return '#faad14'
  }
  return '#1890ff'
})
</script>

<style scoped>
.progress-container {
  padding: 16px 24px;
}

.simple-progress .progress-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.websocket-status {
  display: flex;
  align-items: center;
}

.progress-title {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
}

.synthesis-controls {
  flex-shrink: 0;
}

.compact-stats {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  font-size: 13px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
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
</style> 