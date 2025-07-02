<template>
  <div class="project-list">
    <a-table
      :columns="columns"
      :data-source="projects"
      :loading="loading"
      :pagination="false"
      row-key="id"
      @row-click="handleRowClick"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'title'">
          <div class="project-title">
            <strong>{{ record.title }}</strong>
            <div class="project-description">{{ record.description || '暂无描述' }}</div>
          </div>
        </template>
        
        <template v-else-if="column.key === 'duration'">
          {{ formatTime(record.totalDuration) }}
        </template>
        
        <template v-else-if="column.key === 'tracks'">
          <a-tag v-for="track in record.tracks" :key="track.id" :color="getTrackColor(track.type)">
            {{ getTrackTypeLabel(track.type) }}
          </a-tag>
        </template>
        
        <template v-else-if="column.key === 'createdAt'">
          {{ formatDate(record.createdAt) }}
        </template>
        
        <template v-else-if="column.key === 'actions'">
          <a-space>
            <a-button size="small" @click.stop="selectProject(record)">
              <template #icon><FolderOpenOutlined /></template>
              打开
            </a-button>
            <a-dropdown>
              <a-button size="small">
                <template #icon><MoreOutlined /></template>
              </a-button>
              <template #overlay>
                <a-menu @click="(e) => handleAction(e, record)">
                  <a-menu-item key="duplicate">
                    <CopyOutlined />
                    复制项目
                  </a-menu-item>
                  <a-menu-item key="export">
                    <ExportOutlined />
                    导出JSON
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="delete" danger>
                    <DeleteOutlined />
                    删除项目
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </template>
    </a-table>
    
    <!-- 空状态 -->
    <a-empty v-if="!loading && projects.length === 0" description="暂无项目">
      <a-button type="primary" @click="$emit('create')">创建第一个项目</a-button>
    </a-empty>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  FolderOpenOutlined,
  MoreOutlined,
  CopyOutlined,
  ExportOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'

import { listProjects, deleteProject } from '../../../api/sound-editor/multitrackProject'

const emit = defineEmits(['select', 'delete', 'create'])

const loading = ref(false)
const projects = ref([])

// 表格列定义
const columns = [
  {
    title: '项目名称',
    key: 'title',
    width: '30%'
  },
  {
    title: '时长',
    key: 'duration',
    width: '10%'
  },
  {
    title: '音轨',
    key: 'tracks',
    width: '25%'
  },
  {
    title: '创建时间',
    key: 'createdAt',
    width: '15%'
  },
  {
    title: '操作',
    key: 'actions',
    width: '20%'
  }
]

// 音轨类型映射
const trackTypeLabels = {
  dialogue: '对话',
  environment: '环境音',
  background: '背景音乐'
}

const trackColors = {
  dialogue: 'blue',
  environment: 'green',
  background: 'orange'
}

function getTrackTypeLabel(type) {
  return trackTypeLabels[type] || type
}

function getTrackColor(type) {
  return trackColors[type] || 'default'
}

// 时间格式化
function formatTime(seconds) {
  if (!seconds) return '0:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

// 日期格式化
function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载项目列表
async function loadProjects() {
  loading.value = true
  try {
    const result = await listProjects()
    if (result.success) {
      projects.value = result.data || []
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
    message.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

// 选择项目
function selectProject(project) {
  emit('select', project.id)
}

function handleRowClick(record) {
  selectProject(record)
}

// 项目操作
async function handleAction({ key }, project) {
  switch (key) {
    case 'duplicate':
      await duplicateProject(project)
      break
    case 'export':
      await exportProjectJson(project)
      break
    case 'delete':
      await confirmDeleteProject(project)
      break
  }
}

async function duplicateProject(project) {
  // TODO: 实现项目复制功能
  message.info('复制功能开发中...')
}

async function exportProjectJson(project) {
  try {
    // 创建下载链接
    const dataStr = JSON.stringify(project, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.title}.json`
    link.click()
    
    URL.revokeObjectURL(url)
    message.success('项目已导出')
  } catch (error) {
    console.error('导出失败:', error)
    message.error('导出失败')
  }
}

function confirmDeleteProject(project) {
  Modal.confirm({
    title: '确认删除',
    icon: h(ExclamationCircleOutlined),
    content: `确定要删除项目"${project.title}"吗？此操作不可撤销。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => handleDeleteProject(project)
  })
}

async function handleDeleteProject(project) {
  try {
    const result = await deleteProject(project.id)
    if (result.success) {
      message.success('项目删除成功')
      emit('delete', project.id)
      // 重新加载项目列表
      await loadProjects()
    }
  } catch (error) {
    console.error('删除项目失败:', error)
    message.error('删除项目失败')
  }
}

// 生命周期
onMounted(() => {
  loadProjects()
})

// 暴露刷新方法
defineExpose({
  refresh: loadProjects
})
</script>

<style scoped>
.project-list {
  height: 500px;
  overflow-y: auto;
}

.project-title {
  line-height: 1.4;
}

.project-description {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

:deep(.ant-table-tbody > tr) {
  cursor: pointer;
}

:deep(.ant-table-tbody > tr:hover) {
  background-color: #f5f5f5;
}
</style> 