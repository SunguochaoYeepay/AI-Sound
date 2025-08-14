<template>
  <div>
    <!-- 迷你进度条 (在生成进行中时显示) -->
    <div
      v-if="visible && !showDetails"
      class="mini-progress-bar"
      @click="showDetails = true"
    >
      <div class="mini-progress-content">
        <span class="mini-progress-text">
          {{ progressText }}
        </span>
        <a-progress
          :percent="progress"
          :show-info="false"
          size="small"
          :stroke-color="status === 'failed' ? '#ff4d4f' : '#52c41a'"
        />
        <span class="mini-progress-tip">点击查看详情</span>
      </div>
    </div>

    <!-- 进度详情抽屉 -->
    <a-drawer
      v-model:open="showDetails"
      title="环境音生成进度"
      placement="bottom"
      height="400px"
      :closable="true"
      @close="handleClose"
    >
      <div class="progress-details">
        <!-- 总体进度 -->
        <div class="overall-progress">
          <h4>总体进度</h4>
          <a-progress
            :percent="progress"
            :status="progressStatus"
            :format="progressFormat"
          />
          <div class="progress-stats">
            <span>已完成: {{ completedTracks }}/{{ totalTracks }}</span>
            <span>状态: {{ statusText }}</span>
          </div>
        </div>

        <!-- 轨道进度列表 -->
        <div class="tracks-progress" v-if="tracksProgress.length > 0">
          <h4>轨道进度</h4>
          <div class="track-item" v-for="track in tracksProgress" :key="track.index">
            <div class="track-header">
              <span class="track-title">轨道 {{ track.index + 1 }}</span>
              <a-tag :color="getTrackStatusColor(track.status)">
                {{ getTrackStatusText(track.status) }}
              </a-tag>
            </div>
            <div class="track-info">
              <span class="track-keyword">{{ track.keyword }}</span>
              <span class="track-description">{{ track.description }}</span>
            </div>
            <a-progress
              v-if="track.status === 'processing'"
              :percent="track.progress || 0"
              size="small"
              :show-info="false"
            />
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="progress-actions" v-if="status === 'processing'">
          <a-space>
            <a-button @click="handleCancel" danger>
              取消生成
            </a-button>
            <a-button @click="handlePause" v-if="canPause">
              暂停
            </a-button>
          </a-space>
        </div>

        <!-- 完成状态 -->
        <div class="completion-status" v-if="status === 'completed'">
          <a-result
            status="success"
            title="环境音生成完成"
            :sub-title="`成功生成 ${completedTracks} 个轨道`"
          >
            <template #extra>
              <a-button type="primary" @click="handleRefresh">
                刷新页面
              </a-button>
            </template>
          </a-result>
        </div>

        <!-- 失败状态 -->
        <div class="failure-status" v-if="status === 'failed'">
          <a-result
            status="error"
            title="环境音生成失败"
            :sub-title="errorMessage || '生成过程中发生错误'"
          >
            <template #extra>
              <a-space>
                <a-button type="primary" @click="handleRetry">
                  重试
                </a-button>
                <a-button @click="handleRefresh">
                  刷新页面
                </a-button>
              </a-space>
            </template>
          </a-result>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  },
  status: {
    type: String,
    default: 'processing' // processing, completed, failed
  },
  completedTracks: {
    type: Number,
    default: 0
  },
  totalTracks: {
    type: Number,
    default: 0
  },
  tracksProgress: {
    type: Array,
    default: () => []
  },
  errorMessage: {
    type: String,
    default: ''
  },
  canPause: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits([
  'close',
  'cancel',
  'pause',
  'retry',
  'refresh'
])

// 响应式数据
const showDetails = ref(false)

// 计算属性
const progressText = computed(() => {
  if (props.status === 'completed') {
    return '环境音生成完成'
  } else if (props.status === 'failed') {
    return '环境音生成失败'
  } else {
    return `环境音生成中... (${props.completedTracks}/${props.totalTracks})`
  }
})

const progressStatus = computed(() => {
  if (props.status === 'failed') return 'exception'
  if (props.status === 'completed') return 'success'
  return 'active'
})

const statusText = computed(() => {
  const statusMap = {
    processing: '生成中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[props.status] || '未知'
})

// 方法
const progressFormat = (percent) => `${percent}%`

const getTrackStatusColor = (status) => {
  const colorMap = {
    pending: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error'
  }
  return colorMap[status] || 'default'
}

const getTrackStatusText = (status) => {
  const textMap = {
    pending: '等待中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || '未知'
}

const handleClose = () => {
  showDetails.value = false
  emit('close')
}

const handleCancel = () => {
  message.confirm('确定要取消环境音生成吗？', '确认取消', {
    onOk: () => {
      emit('cancel')
      showDetails.value = false
    }
  })
}

const handlePause = () => {
  emit('pause')
}

const handleRetry = () => {
  emit('retry')
  showDetails.value = false
}

const handleRefresh = () => {
  emit('refresh')
  showDetails.value = false
}

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    showDetails.value = false
  }
})
</script>

<style scoped>
/* 迷你进度条样式 */
.mini-progress-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #ffffff;
  border-top: 1px solid #e8e8e8;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mini-progress-bar:hover {
  background: #f5f5f5;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15);
}

.mini-progress-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 16px;
  max-width: 600px;
  margin: 0 auto;
}

.mini-progress-text {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
}

.mini-progress-bar .ant-progress {
  flex: 1;
  margin: 0;
}

.mini-progress-tip {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

/* 主题颜色适配 */
.mini-progress-content .ant-progress .ant-progress-bg {
  background-color: #52c41a !important;
}

.mini-progress-bar:hover .ant-progress .ant-progress-bg {
  background-color: #389e0d !important;
}

/* 进度详情样式 */
.progress-details {
  padding: 16px;
}

.overall-progress {
  margin-bottom: 24px;
}

.overall-progress h4 {
  margin-bottom: 12px;
  color: #1f2937;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.tracks-progress {
  margin-bottom: 24px;
}

.tracks-progress h4 {
  margin-bottom: 16px;
  color: #1f2937;
}

.track-item {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
  background: #fafafa;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.track-title {
  font-weight: 500;
  color: #1f2937;
}

.track-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.track-keyword {
  font-weight: 500;
  color: #52c41a;
}

.track-description {
  font-size: 12px;
  color: #666;
}

.progress-actions {
  text-align: center;
  margin-top: 24px;
}

.completion-status,
.failure-status {
  text-align: center;
  margin-top: 24px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .mini-progress-content {
    flex-direction: column;
    gap: 8px;
    padding: 12px 16px;
  }

  .mini-progress-text {
    font-size: 12px;
  }

  .mini-progress-tip {
    font-size: 11px;
  }

  .progress-stats {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
