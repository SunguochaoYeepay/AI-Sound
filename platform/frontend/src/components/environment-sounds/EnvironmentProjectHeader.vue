<template>
  <div class="environment-project-header">
    <div class="header-content">
      <!-- 返回按钮 -->
      <div class="back-section">
        <a-button
          type="text"
          size="large"
          @click="handleBack"
          class="back-button"
        >
          <template #icon>
            <ArrowLeftOutlined />
          </template>
          返回
        </a-button>
      </div>

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
            type="primary"
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

    <!-- 项目统计 -->
    <div class="project-stats" v-if="showStats">
      <a-row :gutter="16">
        <a-col :span="6">
          <div class="stat-card">
            <div class="stat-number">{{ stats.totalChapters || 0 }}</div>
            <div class="stat-label">总章节数</div>
          </div>
        </a-col>
        <a-col :span="6">
          <div class="stat-card">
            <div class="stat-number">{{ stats.analyzedChapters || 0 }}</div>
            <div class="stat-label">已分析章节</div>
          </div>
        </a-col>
        <a-col :span="6">
          <div class="stat-card">
            <div class="stat-number">{{ stats.totalTracks || 0 }}</div>
            <div class="stat-label">环境音轨道</div>
          </div>
        </a-col>
        <a-col :span="6">
          <div class="stat-card">
            <div class="stat-number">{{ stats.generatedTracks || 0 }}</div>
            <div class="stat-label">已生成轨道</div>
          </div>
        </a-col>
      </a-row>
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
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(82, 196, 26, 0.3);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.back-section {
  flex: 0 0 auto;
}

.back-button {
  color: white;
  border-color: rgba(255, 255, 255, 0.3);
}

.back-button:hover {
  color: white;
  border-color: white;
  background: rgba(255, 255, 255, 0.1);
}

.project-info {
  flex: 1;
  margin: 0 24px;
}

.project-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.project-title h2 {
  margin: 0;
  color: white;
  font-size: 24px;
  font-weight: 600;
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
  font-size: 14px;
  opacity: 0.9;
}

.header-actions {
  flex: 0 0 auto;
}

.project-stats {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 16px;
}

.stat-card {
  text-align: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
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
    font-size: 20px;
  }

  .stat-label {
    font-size: 11px;
  }
}
</style>
