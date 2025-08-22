<template>
  <div class="environment-project-header">
    <div class="header-content">
      

      <!-- 项目信息 -->
      <div class="project-info">
        <div class="project-title">
          <h2>{{ project?.name || '环境音分析项目' }}</h2>
          <a-tag :color="getStatusColor(project?.status)">
            {{ getStatusText(project?.status) }}
          </a-tag>
        </div>
        <div class="project-meta">
          <span class="meta-item">
            <BookOutlined />
            项目ID: {{ project?.id }}
          </span>
          <span class="meta-item" v-if="project?.created_at">
            <CalendarOutlined />
            创建时间: {{ formatDate(project.created_at) }}
          </span>
          <span class="meta-item" v-if="project?.updated_at">
            <ClockCircleOutlined />
            更新时间: {{ formatDate(project.updated_at) }}
          </span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="header-actions">
        <a-space>
          <a-button
            v-if="canEdit"
            type="default"
            @click="handleEdit"
            :loading="loading"
          >
            <template #icon>
              <EditOutlined />
            </template>
            编辑项目
          </a-button>
          <a-button
            v-if="canDelete"
            danger
            @click="handleDelete"
            :loading="loading"
          >
            <template #icon>
              <DeleteOutlined />
            </template>
            删除项目
          </a-button>
        </a-space>
      </div>
    </div>

   
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  ArrowLeftOutlined,
  BookOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  project: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  showStats: {
    type: Boolean,
    default: true
  },
  stats: {
    type: Object,
    default: () => ({
      totalChapters: 0,
      analyzedChapters: 0,
      totalTracks: 0,
      generatedTracks: 0
    })
  },
  canEdit: {
    type: Boolean,
    default: true
  },
  canDelete: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits([
  'back',
  'edit',
  'delete'
])

// 计算属性
const getStatusColor = (status) => {
  const colorMap = {
    pending: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error',
    paused: 'warning'
  }
  return colorMap[status] || 'default'
}

const getStatusText = (status) => {
  const textMap = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停'
  }
  return textMap[status] || '未知'
}

// 方法
const handleBack = () => {
  emit('back')
}

const handleEdit = () => {
  emit('edit')
}

const handleDelete = () => {
  emit('delete')
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.environment-project-header {
  background: #ffffff;
  border: 1px solid #f0f0f0;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.back-section {
  flex: 0 0 auto;
}

.back-button {
  color: #595959;
}

.back-button:hover {
  color: #1890ff;
  background: #f0f8ff;
}

.project-info {
  flex: 1;
}

.project-title {
  display: flex;
  align-items: center;
  gap: 12px;
  padding:8px 0
}

.project-title h2 {
  margin: 0;
  color: #262626;
  font-size: 20px;
  font-weight: 500;
}

.project-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #8c8c8c;
}

.header-actions {
  flex: 0 0 auto;
}

.project-stats {
  background: #fafafa;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #f0f0f0;
}

.stat-card {
  text-align: center;
  padding: 12px;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #d9d9d9;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 20px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #8c8c8c;
}

/* 暗色主题适配 */
[data-theme='dark'] .environment-project-header {
  background: #1f1f1f;
  border-color: #303030;
}

[data-theme='dark'] .project-title h2 {
  color: #ffffff;
}

[data-theme='dark'] .meta-item {
  color: #a6a6a6;
}

[data-theme='dark'] .project-stats {
  background: #262626;
  border-color: #303030;
}

[data-theme='dark'] .stat-card {
  background: #1f1f1f;
  border-color: #303030;
}

[data-theme='dark'] .stat-number {
  color: #ffffff;
}

[data-theme='dark'] .stat-label {
  color: #a6a6a6;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .environment-project-header {
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .project-info {
    margin: 0;
    text-align: center;
  }

  .project-title {
    justify-content: center;
  }

  .project-meta {
    justify-content: center;
  }

  .header-actions {
    display: flex;
    justify-content: center;
  }

  .project-stats {
    padding: 12px;
  }

  .stat-card {
    padding: 8px;
  }

  .stat-number {
    font-size: 18px;
  }

  .stat-label {
    font-size: 11px;
  }
}
</style>
