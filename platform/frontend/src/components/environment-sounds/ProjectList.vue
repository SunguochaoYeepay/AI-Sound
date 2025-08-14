<template>
  <div class="project-list">
    <a-card :bordered="false">
      <!-- 项目列表 -->
      <div v-if="projects.length > 0" class="projects-grid">
        <div
          v-for="project in projects"
          :key="project.id"
          class="project-card"
          :class="getProjectStatusClass(project.status)"
          @click="$emit('project-click', project)"
        >
          <!-- 项目头部 -->
          <div class="project-header">
            <div class="project-title">
              <h3>{{ project.name }}</h3>
              <a-tag :color="getStatusColor(project.status)">
                {{ getStatusText(project.status) }}
              </a-tag>
            </div>
            <div class="project-actions">
              <a-dropdown>
                <a-button type="text" size="small">
                  <EllipsisOutlined />
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="$emit('view-sounds', project)">
                      <SoundOutlined />
                      查看环境音
                    </a-menu-item>
                    <a-menu-item @click="$emit('delete', project)">
                      <DeleteOutlined />
                      删除项目
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
          </div>

          <!-- 项目描述 -->
          <div class="project-description">
            {{ project.description || '暂无描述' }}
          </div>

          <!-- 项目统计 -->
          <div class="project-stats">
            <div class="stat-item">
              <span class="stat-label">轨道数:</span>
              <span class="stat-value">{{ project.total_tracks || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">已生成:</span>
              <span class="stat-value">{{ project.generated_tracks || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">创建时间:</span>
              <span class="stat-value">{{ formatDate(project.created_at) }}</span>
            </div>
          </div>

          <!-- 项目操作 -->
          <div class="project-actions-bottom">
            <a-space>
              <a-button
                size="small"
                type="primary"
                @click.stop="$emit('project-click', project)"
              >
                查看详情
              </a-button>
              <a-button
                v-if="project.status === 'completed'"
                size="small"
                @click.stop="$emit('view-sounds', project)"
              >
                查看环境音
              </a-button>
            </a-space>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-state">
        <a-empty description="暂无环境音分析项目">
          <template #image>
            <SoundOutlined style="font-size: 64px; color: #d9d9d9;" />
          </template>
        </a-empty>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <a-spin size="large" />
        <p>加载中...</p>
      </div>

      <!-- 分页 -->
      <div v-if="projects.length > 0" class="pagination-wrapper">
        <a-pagination
          v-model:current="pagination.current"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :show-size-changer="true"
          :show-quick-jumper="true"
          :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
          @change="$emit('page-change', $event)"
          @show-size-change="$emit('size-change', $event)"
        />
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  EllipsisOutlined, 
  SoundOutlined, 
  DeleteOutlined 
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  projects: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  pagination: {
    type: Object,
    default: () => ({
      current: 1,
      pageSize: 20,
      total: 0
    })
  }
})

// Emits
const emit = defineEmits([
  'project-click',
  'delete',
  'view-sounds',
  'page-change',
  'size-change'
])

// 方法
const getStatusColor = (status) => {
  const colors = {
    pending: 'orange',
    processing: 'blue',
    completed: 'green',
    failed: 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || '未知'
}

const getProjectStatusClass = (status) => {
  return {
    'project-pending': status === 'pending',
    'project-processing': status === 'processing',
    'project-completed': status === 'completed',
    'project-failed': status === 'failed'
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.project-list {
  margin-bottom: 24px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.project-card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.project-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
  transform: translateY(-2px);
}

.project-card.project-completed {
  border-color: #52c41a;
}

.project-card.project-completed:hover {
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.15);
}

.project-card.project-processing {
  border-color: #1890ff;
}

.project-card.project-processing:hover {
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.project-card.project-failed {
  border-color: #ff4d4f;
}

.project-card.project-failed:hover {
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.15);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.project-title h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  line-height: 1.4;
}

.project-description {
  margin: 0 0 12px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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

.stat-label {
  font-weight: 500;
}

.stat-value {
  color: #333;
}

.project-actions-bottom {
  display: flex;
  justify-content: flex-end;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.loading-state {
  text-align: center;
  padding: 60px 20px;
}

.loading-state p {
  margin-top: 16px;
  color: #666;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 暗黑模式适配 */
[data-theme='dark'] .project-card {
  background: #1f1f1f;
  border-color: #434343;
}

[data-theme='dark'] .project-card:hover {
  border-color: #4a9eff;
}

[data-theme='dark'] .project-title h3 {
  color: #fff;
}

[data-theme='dark'] .project-description {
  color: #d1d5db;
}

[data-theme='dark'] .stat-item {
  color: #8c8c8c;
}

[data-theme='dark'] .stat-value {
  color: #d1d5db;
}

[data-theme='dark'] .project-stats {
  border-top-color: #434343;
}
</style>
