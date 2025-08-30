<template>
  <div class="analysis-header">
    <a-card>
      <div class="header-content">
        <div class="header-left">
          <h2>分析会话 #{{ session?.id }}</h2>
          <div class="session-info">
            <span class="book-title">{{ session?.book?.title || '未知书籍' }}</span>
            <span class="separator">·</span>
            <span class="author">{{ session?.book?.author || '未知作者' }}</span>
          </div>
          <div class="status-info">
            <a-tag :color="getStatusColor(session?.status)">
              {{ getStatusText(session?.status) }}
            </a-tag>
            <span v-if="session?.progress !== undefined" class="progress-text">
              进度: {{ session.progress }}%
            </span>
          </div>
        </div>
        
        <div class="header-right">
          <a-space>
            <a-button
              v-if="session?.status === 'pending'"
              type="primary"
              @click="$emit('start-analysis')"
              :loading="loading"
            >
              开始分析
            </a-button>
            <a-button
              v-if="session?.status === 'ready_for_review'"
              type="success"
              @click="$emit('confirm-session')"
              :loading="loading"
            >
              确认通过
            </a-button>
            <a-button
              v-if="['completed', 'ready_for_review', 'confirmed'].includes(session?.status)"
              @click="$emit('reanalyze-session')"
              :loading="loading"
            >
              重新分析
            </a-button>
          </a-space>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { STATUS_CONFIG } from '@/api/storyboard'

defineProps({
  session: Object,
  loading: Boolean
})

defineEmits(['start-analysis', 'confirm-session', 'reanalyze-session'])

const getStatusColor = (status) => {
  return STATUS_CONFIG[status]?.color || '#d9d9d9'
}

const getStatusText = (status) => {
  return STATUS_CONFIG[status]?.name || '未知状态'
}
</script>

<style scoped>
.analysis-header {
  margin-bottom: 16px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.session-info {
  margin-bottom: 8px;
  color: #666;
}

.book-title {
  font-weight: 500;
  color: #262626;
}

.separator {
  margin: 0 8px;
  color: #d9d9d9;
}

.author {
  color: #666;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-text {
  font-size: 14px;
  color: #666;
}
</style>
