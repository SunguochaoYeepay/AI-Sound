<template>
  <div class="novel-projects-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>小说朗读项目</h1>
        <p>管理您的多角色朗读项目，创建新项目或继续编辑现有项目</p>
      </div>
      <div class="header-actions">
        <a-button type="primary" size="large" @click="createNewProject">
          <template #icon>
            <PlusOutlined />
          </template>
          新建项目
        </a-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <div class="filter-left">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索项目名称或描述..."
          style="width: 300px;"
          @search="onSearch"
          allow-clear
        />
        <a-select
          v-model:value="statusFilter"
          placeholder="项目状态"
          style="width: 120px;"
          allow-clear
          @change="onFilterChange"
        >
          <a-select-option value="pending">待处理</a-select-option>
          <a-select-option value="processing">处理中</a-select-option>
          <a-select-option value="completed">已完成</a-select-option>
          <a-select-option value="failed">失败</a-select-option>
        </a-select>
      </div>
      <div class="filter-right">
        <a-button @click="refreshProjects" :loading="loading">
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新
        </a-button>
      </div>
    </div>

    <!-- 项目统计 -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-number">{{ projectStats.total }}</div>
        <div class="stat-label">总项目</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ projectStats.completed }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ projectStats.processing }}</div>
        <div class="stat-label">处理中</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ projectStats.pending }}</div>
        <div class="stat-label">待处理</div>
      </div>
    </div>

    <!-- 项目列表 -->
    <div class="projects-section">
      <a-spin :spinning="loading" tip="加载项目中...">
        <div v-if="filteredProjects.length === 0 && !loading" class="empty-state">
          <div class="empty-content">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="#d1d5db">
              <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
            </svg>
            <h3>暂无项目</h3>
            <p>创建您的第一个多角色朗读项目</p>
            <a-button type="primary" @click="createNewProject">
              立即创建
            </a-button>
          </div>
        </div>

        <div v-else class="projects-grid">
          <div
            v-for="project in filteredProjects"
            :key="project.id"
            class="project-card"
            @click="openProject(project)"
          >
            <div class="project-header">
              <div class="project-title">{{ project.name }}</div>
              <a-dropdown :trigger="['click']" @click.stop>
                <a-button type="text" size="small">⋮</a-button>
                <template #overlay>
                  <a-menu @click="onProjectAction($event, project)">
                    <a-menu-item key="edit">编辑项目</a-menu-item>
                    <a-menu-item key="duplicate">复制项目</a-menu-item>
                    <a-menu-item key="export">导出项目</a-menu-item>
                    <a-menu-divider />
                    <a-menu-item key="delete" class="danger-item">删除项目</a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>

            <div class="project-description">
              {{ project.description || '暂无描述' }}
            </div>

            <div class="project-meta">
              <div class="meta-item">
                <span>📅 {{ formatDate(project.created_at) }}</span>
              </div>
              <div class="meta-item">
                <span>👥 {{ getCharacterCount(project) }} 个角色</span>
              </div>
              <div class="meta-item">
                <span>📝 {{ getSegmentCount(project) }} 个段落</span>
              </div>
            </div>

            <div class="project-progress">
              <div class="progress-info">
                <span class="progress-text">完成度</span>
                <span class="progress-percent">{{ getProgress(project) }}%</span>
              </div>
              <a-progress 
                :percent="getProgress(project)" 
                :show-info="false" 
                size="small"
                :stroke-color="getProgressColor(project.status)"
              />
            </div>

            <div class="project-footer">
              <a-tag :color="getStatusColor(project.status)" size="small">
                {{ getStatusText(project.status) }}
              </a-tag>
              <div class="project-actions">
                <a-button 
                  type="text" 
                  size="small" 
                  @click.stop="configureProject(project)"
                >
                  配置
                </a-button>
                <a-button 
                  type="primary" 
                  size="small"
                  @click.stop="openProject(project)"
                  :disabled="project.status === 'failed'"
                >
                  {{ project.status === 'completed' ? '查看' : '继续' }}
                </a-button>
              </div>
            </div>
          </div>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { readerAPI } from '@/api'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const projects = ref([])
const searchKeyword = ref('')
const statusFilter = ref(null)
const sortBy = ref('created_at')
const sortOrder = ref('desc')

// 项目统计
const projectStats = computed(() => {
  const stats = { total: 0, completed: 0, processing: 0, pending: 0 }
  
  projects.value.forEach(project => {
    stats.total++
    if (project.status === 'completed') stats.completed++
    else if (project.status === 'processing') stats.processing++
    else if (project.status === 'pending') stats.pending++
  })
  
  return stats
})

// 过滤后的项目列表
const filteredProjects = computed(() => {
  let filtered = [...projects.value]
  
  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(project => 
      project.name.toLowerCase().includes(keyword) ||
      (project.description && project.description.toLowerCase().includes(keyword))
    )
  }
  
  // 状态过滤
  if (statusFilter.value) {
    filtered = filtered.filter(project => project.status === statusFilter.value)
  }
  
  return filtered
})

// 方法
const loadProjects = async () => {
  loading.value = true
  try {
    const response = await readerAPI.getProjects({
      page: 1,
      page_size: 100,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    })
    
    if (response.data.success) {
      projects.value = response.data.data || []
    } else {
      message.error('获取项目列表失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
    message.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

const refreshProjects = () => {
  loadProjects()
}

const onSearch = () => {
  // 搜索功能已在computed中处理
}

const onFilterChange = () => {
  // 过滤功能已在computed中处理
}

const createNewProject = () => {
  router.push('/novel-reader/create')
}

const openProject = (project) => {
  router.push(`/novel-reader/detail/${project.id}`)
}

const configureProject = (project) => {
  router.push(`/novel-reader/edit/${project.id}`)
}

const onProjectAction = async ({ key }, project) => {
  switch (key) {
    case 'edit':
      configureProject(project)
      break
    case 'duplicate':
      await duplicateProject(project)
      break
    case 'export':
      exportProject(project)
      break
    case 'delete':
      confirmDeleteProject(project)
      break
  }
}

const duplicateProject = async (project) => {
  try {
    const newProject = {
      name: `${project.name}_副本`,
      description: project.description,
      text_content: project.original_text || '',
      character_mapping: project.character_mapping || {}
    }
    
    const response = await readerAPI.createProject(newProject)
    if (response.data.success) {
      message.success('项目复制成功')
      loadProjects()
    } else {
      message.error('复制失败: ' + response.data.message)
    }
  } catch (error) {
    message.error('复制失败')
  }
}

const exportProject = (project) => {
  const projectData = {
    ...project,
    export_time: new Date().toISOString(),
    version: '1.0'
  }
  
  const blob = new Blob([JSON.stringify(projectData, null, 2)], {
    type: 'application/json'
  })
  
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${project.name}_export.json`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
  
  message.success('项目导出成功')
}

const confirmDeleteProject = (project) => {
  Modal.confirm({
    title: '删除项目',
    content: `确定要删除项目"${project.name}"吗？此操作不可恢复。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => deleteProject(project)
  })
}

const deleteProject = async (project) => {
  try {
    const response = await readerAPI.deleteProject(project.id)
    if (response.data.success) {
      message.success('项目删除成功')
      loadProjects()
    } else {
      message.error('删除失败: ' + response.data.message)
    }
  } catch (error) {
    message.error('删除失败')
  }
}

// 辅助函数
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const getCharacterCount = (project) => {
  const mapping = project.character_mapping || {}
  return Object.keys(mapping).length
}

const getSegmentCount = (project) => {
  return project.segments?.length || 0
}

const getProgress = (project) => {
  if (project.status === 'completed') return 100
  if (project.status === 'failed') return 0
  if (project.status === 'processing') {
    const segments = project.segments || []
    if (segments.length === 0) return 0
    
    const completedSegments = segments.filter(s => s.audio_file_path).length
    return Math.round((completedSegments / segments.length) * 100)
  }
  return 0
}

const getProgressColor = (status) => {
  const colors = {
    'pending': '#faad14',
    'processing': '#1890ff',
    'completed': '#52c41a',
    'failed': '#ff4d4f'
  }
  return colors[status] || '#d9d9d9'
}

const getStatusColor = (status) => {
  const colors = {
    'pending': 'orange',
    'processing': 'blue',
    'completed': 'green',
    'failed': 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return texts[status] || '未知'
}

// 生命周期
onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.novel-projects-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 32px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  border-radius: 16px;
  color: white;
}

.header-content h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
}

.header-content p {
  margin: 8px 0 0 0;
  font-size: 16px;
  opacity: 0.9;
}

.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-left {
  display: flex;
  gap: 16px;
  align-items: center;
}

.filter-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #06b6d4;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 8px;
}

.projects-section {
  margin-bottom: 32px;
}

.empty-state {
  padding: 80px 20px;
  text-align: center;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.empty-content h3 {
  margin: 16px 0 8px 0;
  color: #374151;
}

.empty-content p {
  color: #6b7280;
  margin-bottom: 24px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.project-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.project-card:hover {
  border-color: #06b6d4;
  box-shadow: 0 8px 25px rgba(6, 182, 212, 0.15);
  transform: translateY(-2px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.project-title {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  line-height: 1.4;
  flex: 1;
  margin-right: 12px;
}

.project-description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 16px;
  line-height: 1.5;
  min-height: 40px;
}

.project-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #9ca3af;
}

.project-progress {
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-text {
  font-size: 12px;
  color: #6b7280;
}

.progress-percent {
  font-size: 12px;
  font-weight: 600;
  color: #06b6d4;
}

.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-actions {
  display: flex;
  gap: 8px;
}

.danger-item {
  color: #ff4d4f !important;
}

@media (max-width: 768px) {
  .novel-projects-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-section {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-left {
    flex-direction: column;
    align-items: stretch;
  }
  
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .projects-grid {
    grid-template-columns: 1fr;
  }
}
</style> 