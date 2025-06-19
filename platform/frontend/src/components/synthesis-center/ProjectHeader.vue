<template>
  <div class="panel-header">
    <div class="header-with-back">
      <a-button type="text" @click="$emit('back')" class="back-btn">
        <template #icon><ArrowLeftOutlined /></template>
      </a-button>
      <div class="project-info">
        <h3>📚 {{ project?.book?.title || project?.name || '加载中...' }}</h3>
        <div class="project-meta">
          <span class="project-subtitle">{{ project?.book?.author || '项目管理' }}</span>
          <a-tag :color="getStatusColor(project?.status)" size="small" class="status-tag">
            {{ getStatusText(project?.status) }}
          </a-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowLeftOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  project: {
    type: Object,
    default: () => null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['back'])

// 智能状态显示：根据实际完成情况显示状态
const getDisplayStatus = (rawStatus) => {
  if (!rawStatus || !props.project) return rawStatus
  
  if (rawStatus === 'partial_completed') {
    const completed = props.project?.statistics?.completedSegments || props.project?.processed_segments || 0
    const total = props.project?.statistics?.totalSegments || props.project?.total_segments || 0
    const failed = props.project?.statistics?.failedSegments || props.project?.failed_segments || 0
    
    if (total > 0 && completed === total && failed === 0) {
      return 'completed'
    }
    if (failed > 0) {
      return 'failed'
    }
  }
  return rawStatus
}

const getStatusText = (status) => {
  if (!status) return '未知状态'
  
  const displayStatus = getDisplayStatus(status)
  const texts = {
    pending: '待开始',
    processing: '合成中',
    paused: '已暂停',
    completed: '已完成',
    partial_completed: '部分完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[displayStatus] || displayStatus
}

const getStatusColor = (status) => {
  if (!status) return 'default'
  
  const displayStatus = getDisplayStatus(status)
  const colors = {
    pending: 'orange',
    processing: 'blue',
    paused: 'purple',
    completed: 'green',
    partial_completed: 'gold',
    failed: 'red',
    cancelled: 'default'
  }
  return colors[displayStatus] || 'default'
}
</script>

<style scoped>
.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.header-with-back {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.back-btn {
  flex-shrink: 0;
  margin-top: 2px;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f0f6ff;
  color: #1890ff;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-info h3 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.project-subtitle {
  font-size: 12px;
  color: #666;
}

.status-tag {
  font-size: 11px;
}
</style> 