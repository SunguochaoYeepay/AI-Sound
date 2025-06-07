<template>
  <div class="novel-projects-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>语音合成项目</h1>
        <p>管理文本转语音项目，创建和生成多角色朗读音频</p>
      </div>
      <div class="header-actions">
        <a-button type="primary" size="large" @click="showCreateModal = true">
          <template #icon>
            <PlusOutlined />
          </template>
          新建项目
        </a-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ projectStats.total }}</div>
          <div class="stat-label">总项目</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ projectStats.completed }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ projectStats.processing }}</div>
          <div class="stat-label">处理中</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ projectStats.pending }}</div>
          <div class="stat-label">待处理</div>
        </div>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <div class="filter-controls">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索项目名称..."
          style="width: 300px;"
          size="large"
          @search="onSearch"
          allow-clear
        />
        
        <a-select
          v-model:value="statusFilter"
          placeholder="项目状态"
          style="width: 120px;"
          size="large"
          @change="onFilterChange"
          allow-clear
        >
          <a-select-option value="">全部</a-select-option>
          <a-select-option value="pending">待处理</a-select-option>
          <a-select-option value="processing">处理中</a-select-option>
          <a-select-option value="completed">已完成</a-select-option>
          <a-select-option value="failed">失败</a-select-option>
        </a-select>

        <a-button @click="refreshProjects" :loading="loading" size="large">
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新
        </a-button>
      </div>

      <div class="view-controls">
        <a-radio-group v-model:value="viewMode" size="large">
          <a-radio-button value="grid">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3,11H11V3H3M3,21H11V13H3M13,21H21V13H13M13,3V11H21V3"/>
            </svg>
          </a-radio-button>
          <a-radio-button value="list">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3,5H21V7H3V5M3,13V11H21V13H3M3,19V17H21V19H3Z"/>
            </svg>
          </a-radio-button>
        </a-radio-group>
      </div>
    </div>

    <!-- 项目列表内容 -->
    <div class="projects-content">
      <a-spin :spinning="loading" tip="加载项目中...">
        <!-- 空状态 -->
        <div v-if="filteredProjects.length === 0 && !loading" class="empty-state">
          <div class="empty-content">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="#d1d5db">
              <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
            </svg>
            <h3>暂无项目</h3>
            <p>创建您的第一个语音合成项目</p>
            <a-button type="primary" @click="showCreateModal = true">
              立即创建
            </a-button>
          </div>
        </div>

        <!-- 网格视图 -->
        <div v-else-if="viewMode === 'grid'" class="grid-view">
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
                    <a-menu-item key="audio">查看音频</a-menu-item>
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
                  @click.stop="viewAudioFiles(project)"
                  title="查看音频文件"
                >
                  音频
                </a-button>
                <a-button 
                  type="primary" 
                  size="small"
                  @click.stop="openProject(project)"
                  :disabled="project.status === 'failed'"
                >
                  {{ project.status === 'completed' ? '查看' : '合成' }}
                </a-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 列表视图 -->
        <div v-else class="list-view">
          <a-table
            :columns="tableColumns"
            :data-source="filteredProjects"
            :pagination="{ pageSize: 10, showSizeChanger: true, showQuickJumper: true }"
            row-key="id"
            size="large"
            @row="(record) => ({ onClick: () => openProject(record) })"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <div style="display: flex; align-items: center; gap: 12px;">
                  <div class="table-avatar">
                    {{ record.name.charAt(0) }}
                  </div>
                  <div>
                    <div style="font-weight: 500;">{{ record.name }}</div>
                    <div style="font-size: 12px; color: #6b7280;">{{ record.description }}</div>
                  </div>
                </div>
              </template>

              <template v-if="column.key === 'progress'">
                <a-progress :percent="getProgress(record)" size="small" />
              </template>

              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>

              <template v-if="column.key === 'actions'">
                <div style="display: flex; gap: 8px;">
                  <a-button type="text" size="small" @click.stop="viewAudioFiles(record)" title="查看音频文件">
                    音频
                  </a-button>
                  <a-button type="text" size="small" @click.stop="openProject(record)">
                    {{ record.status === 'completed' ? '查看' : '合成' }}
                  </a-button>
                  <a-button type="text" size="small" danger @click.stop="deleteProject(record)">
                    删除
                  </a-button>
                </div>
              </template>
            </template>
          </a-table>
        </div>
      </a-spin>
    </div>

    <!-- 新建项目弹窗 -->
    <a-modal
      v-model:open="showCreateModal"
      title="新建语音合成项目"
      width="600"
      @ok="createProject"
      @cancel="cancelCreate"
      :confirm-loading="creating"
    >
      <a-form
        ref="createForm"
        :model="newProject"
        :rules="createRules"
        layout="vertical"
        style="margin-top: 20px;"
      >
        <a-form-item label="项目名称" name="name" required>
          <a-input v-model:value="newProject.name" placeholder="请输入项目名称" />
        </a-form-item>

        <a-form-item label="项目描述" name="description">
          <a-textarea v-model:value="newProject.description" placeholder="请输入项目描述（可选）" :rows="3" />
        </a-form-item>

        <a-form-item label="文本内容" name="text_content" required>
          <a-textarea v-model:value="newProject.text_content" placeholder="请输入要转换的文本内容" :rows="6" />
        </a-form-item>
      </a-form>
    </a-modal>
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
const creating = ref(false)
const projects = ref([])
const searchKeyword = ref('')
const statusFilter = ref('')
const viewMode = ref('grid')
const showCreateModal = ref(false)

// 新建项目表单
const newProject = ref({
  name: '',
  description: '',
  text_content: ''
})

const createRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  text_content: [{ required: true, message: '请输入文本内容', trigger: 'blur' }]
}

// 表格列定义
const tableColumns = [
  {
    title: '项目名称',
    dataIndex: 'name',
    key: 'name',
    width: 300
  },
  {
    title: '角色数量',
    dataIndex: 'character_count',
    key: 'character_count',
    width: 100,
    customRender: ({ record }) => getCharacterCount(record)
  },
  {
    title: '进度',
    dataIndex: 'progress',
    key: 'progress',
    width: 150
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 120,
    customRender: ({ record }) => formatDate(record.created_at)
  },
  {
    title: '操作',
    key: 'actions',
    width: 150
  }
]

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
      page_size: 100
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

const createProject = async () => {
  try {
    creating.value = true
    const response = await readerAPI.createProject(newProject.value)
    if (response.data.success) {
      message.success('项目创建成功')
      showCreateModal.value = false
      resetCreateForm()
      loadProjects()
    } else {
      message.error('创建失败: ' + response.data.message)
    }
  } catch (error) {
    message.error('创建失败')
  } finally {
    creating.value = false
  }
}

const cancelCreate = () => {
  showCreateModal.value = false
  resetCreateForm()
}

const resetCreateForm = () => {
  newProject.value = {
    name: '',
    description: '',
    text_content: ''
  }
}

const openProject = (project) => {
  router.push(`/novel-reader/detail/${project.id}`)
}

const viewAudioFiles = (project) => {
  // 跳转到音频库，并搜索该项目的音频文件
  router.push({
    path: '/audio-library',
    query: { search: project.name }
  })
}

const onProjectAction = async ({ key }, project) => {
  switch (key) {
    case 'edit':
      router.push(`/novel-reader/edit/${project.id}`)
      break
    case 'duplicate':
      await duplicateProject(project)
      break
    case 'audio':
      viewAudioFiles(project)
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
  background: #faf9f8;
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  padding: 40px;
  border-radius: 16px;
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 8px 32px rgba(6, 182, 212, 0.2);
}

.header-content h1 {
  margin: 0;
  color: white;
  font-size: 28px;
  font-weight: 700;
}

.header-content p {
  margin: 8px 0 0 0;
  color: rgba(255,255,255,0.9);
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 16px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

/* 筛选部分 */
.filter-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.filter-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.view-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 项目内容 */
.projects-content {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-content h3 {
  margin: 16px 0 8px 0;
  color: #374151;
  font-size: 18px;
}

.empty-content p {
  color: #6b7280;
  margin-bottom: 24px;
}

/* 网格视图 */
.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.project-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.project-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  border-color: #06b6d4;
  transform: translateY(-2px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.project-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.project-description {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 16px;
  min-height: 40px;
}

.project-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.meta-item {
  font-size: 12px;
  color: #6b7280;
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
  font-size: 14px;
  color: #374151;
}

.progress-percent {
  font-size: 14px;
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

/* 列表视图 */
.table-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .filter-section {
    flex-direction: column;
    gap: 16px;
  }

  .filter-controls {
    flex-wrap: wrap;
  }

  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }

  .grid-view {
    grid-template-columns: 1fr;
  }
}

.danger-item {
  color: #ef4444 !important;
}
</style> 