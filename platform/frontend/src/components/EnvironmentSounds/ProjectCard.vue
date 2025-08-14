<template>
  <div class="project-card" :class="project.status">
    <a-badge
      class="status-badge"
      :status="getStatusType(project.status)"
      :text="getStatusText(project.status)"
    />
    
    <div class="project-info">
      <h3 class="project-name">{{ project.name }}</h3>
      <p class="project-description">{{ project.description }}</p>
      
      <div class="project-meta">
        <div class="meta-item">
          <folder-outlined />
          <span>{{ project.bookName || '未关联书籍' }}</span>
        </div>
        <div class="meta-item">
          <clock-circle-outlined />
          <span>{{ formatDate(project.createdAt) }}</span>
        </div>
      </div>
    </div>

    <div class="project-stats">
      <div class="stat-item">
        <sound-outlined />
        <span>{{ project.soundCount || 0 }} 音效</span>
      </div>
      <div class="stat-item">
        <play-circle-outlined />
        <span>{{ project.duration || 0 }}s</span>
      </div>
      <div class="stat-item">
        <database-outlined />
        <span>{{ project.size || 0 }}MB</span>
      </div>
    </div>

    <div class="project-actions">
      <a-button type="primary" size="small" @click="$emit('edit', project)">
        编辑
      </a-button>
      <a-button size="small" @click="$emit('generate', project)">
        生成
      </a-button>
      <a-popconfirm
        title="确定要删除这个项目吗？"
        @confirm="$emit('delete', project)"
        okText="确定"
        cancelText="取消"
      >
        <a-button size="small" danger>删除</a-button>
      </a-popconfirm>
    </div>
  </div>
</template>

<script setup>
import { defineEmits } from 'vue'
import {
  FolderOutlined,
  ClockCircleOutlined,
  SoundOutlined,
  PlayCircleOutlined,
  DatabaseOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete', 'generate'])

const getStatusType = (status) => {
  const statusMap = {
    completed: 'success',
    processing: 'processing',
    failed: 'error',
    pending: 'default'
  }
  return statusMap[status] || 'default'
}

const getStatusText = (status) => {
  const statusMap = {
    completed: '已完成',
    processing: '处理中',
    failed: '失败',
    pending: '待处理'
  }
  return statusMap[status] || '未知'
}

const formatDate = (date) => {
  if (!date) return '未知'
  return new Date(date).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.project-card {
  position: relative;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: all 0.3s ease;
}

.project-card:hover {
  border-color: #1890ff;
}

.project-card.completed {
  border-color: #52c41a;
}

.project-card.processing {
  border-color: #fa8c16;
}

.project-card.failed {
  border-color: #ff4d4f;
}

.status-badge {
  position: absolute;
  top: 12px;
  right: 12px;
}

.project-info {
  margin-bottom: 12px;
}

.project-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

.project-description {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-meta {
  margin-bottom: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 12px;
}

.project-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  padding: 8px 0;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 12px;
}

.project-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 暗黑模式适配 */
[data-theme='dark'] .project-card {
  background: #1f1f1f !important;
  border-color: #434343 !important;
}

[data-theme='dark'] .project-card:hover {
  border-color: #4a9eff !important;
}

[data-theme='dark'] .project-card.completed {
  border-color: #52c41a !important;
}

[data-theme='dark'] .project-card.processing {
  border-color: #fa8c16 !important;
}

[data-theme='dark'] .project-card.failed {
  border-color: #ff4d4f !important;
}

[data-theme='dark'] .project-name {
  color: #fff !important;
}

[data-theme='dark'] .project-description {
  color: #d1d5db !important;
}

[data-theme='dark'] .stat-item {
  color: #8c8c8c !important;
}

[data-theme='dark'] .project-stats {
  border-top-color: #434343 !important;
}
</style>