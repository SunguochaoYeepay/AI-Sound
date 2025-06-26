<template>
  <div class="editor-projects">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" class="title-icon">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
            <path d="M14 8v8h2V8h-2zm4 0v8h2V8h-2z"/>
          </svg>
          音视频编辑器
        </h1>
        <p class="page-description">专业级音视频后期制作工具，支持对话音频与环境音混合</p>
      </div>
      
      <div class="header-actions">
        <a-button type="primary" size="large" @click="createNewProject">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
          </template>
          新建项目
        </a-button>
        
        <a-button size="large" @click="importFromSynthesis">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
          </template>
          导入合成结果
        </a-button>
      </div>
    </div>

    <!-- 过滤器和搜索 -->
    <div class="filters-section">
      <div class="filters-left">
        <a-input-search
          v-model:value="searchTerm"
          placeholder="搜索项目名称..."
          style="width: 300px"
          allow-clear
          @search="loadProjects"
        />
        
        <a-select
          v-model:value="statusFilter"
          placeholder="项目状态"
          style="width: 150px"
          allow-clear
          @change="loadProjects"
        >
          <a-select-option value="draft">草稿</a-select-option>
          <a-select-option value="processing">处理中</a-select-option>
          <a-select-option value="completed">已完成</a-select-option>
          <a-select-option value="error">错误</a-select-option>
        </a-select>
        
        <a-select
          v-model:value="typeFilter"
          placeholder="项目类型"
          style="width: 150px"
          allow-clear
          @change="loadProjects"
        >
          <a-select-option value="audio_only">纯音频</a-select-option>
          <a-select-option value="video">音视频</a-select-option>
          <a-select-option value="synthesis_import">合成导入</a-select-option>
        </a-select>
      </div>
      
      <div class="filters-right">
        <a-tooltip title="刷新项目列表">
          <a-button @click="loadProjects" :loading="loading">
            <template #icon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
              </svg>
            </template>
          </a-button>
        </a-tooltip>
        
        <a-dropdown>
          <a-button>
            <template #icon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"/>
              </svg>
            </template>
            视图
          </a-button>
          <template #overlay>
            <a-menu @click="handleViewChange">
              <a-menu-item key="grid">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3,11H11V3H3M3,21H11V13H3M13,21H21V13H13M13,3V11H21V3"/>
                </svg>
                网格视图
              </a-menu-item>
              <a-menu-item key="list">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3,5H21V7H3V5M3,13V11H21V13H3M3,19V17H21V19H3Z"/>
                </svg>
                列表视图
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 项目列表 -->
    <div class="projects-container">
      <a-spin :spinning="loading" tip="加载项目中...">
        <div v-if="!loading && projects.length === 0" class="empty-state">
          <div class="empty-content">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="#d9d9d9">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
            <h3>暂无编辑项目</h3>
            <p>创建您的第一个音视频编辑项目，或从合成结果导入项目开始制作。</p>
            <a-button type="primary" @click="createNewProject">
              <template #icon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
              </template>
              创建新项目
            </a-button>
          </div>
        </div>

        <!-- 网格视图 -->
        <div v-else-if="viewMode === 'grid'" class="projects-grid">
          <div
            v-for="project in projects"
            :key="project.id"
            class="project-card"
            @click="openProject(project)"
          >
            <div class="card-header">
              <div class="project-type">
                <a-tag :color="getProjectTypeColor(project.type)">
                  {{ getProjectTypeLabel(project.type) }}
                </a-tag>
              </div>
              <div class="project-status">
                <a-tag :color="getStatusColor(project.status)">
                  {{ getStatusLabel(project.status) }}
                </a-tag>
              </div>
            </div>
            
            <div class="card-content">
              <h3 class="project-name">{{ project.name }}</h3>
              <p class="project-description">{{ project.description || '暂无描述' }}</p>
              
              <div class="project-stats">
                <div class="stat-item">
                  <span class="stat-label">轨道数:</span>
                  <span class="stat-value">{{ project.track_count || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">时长:</span>
                  <span class="stat-value">{{ formatDuration(project.duration) }}</span>
                </div>
              </div>
            </div>
            
            <div class="card-footer">
              <div class="project-meta">
                <span class="create-time">{{ formatTime(project.created_at) }}</span>
                <span class="update-time">更新于 {{ formatTime(project.updated_at) }}</span>
              </div>
              
              <div class="project-actions" @click.stop>
                <a-button type="text" size="small" @click="openProject(project)">
                  编辑
                </a-button>
                <a-dropdown>
                  <a-button type="text" size="small">
                    <template #icon>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z"/>
                      </svg>
                    </template>
                  </a-button>
                  <template #overlay>
                    <a-menu @click="(e) => handleProjectAction(e, project)">
                      <a-menu-item key="duplicate">复制项目</a-menu-item>
                      <a-menu-item key="export">导出项目</a-menu-item>
                      <a-menu-divider />
                      <a-menu-item key="delete" class="danger-item">删除项目</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </div>
            </div>
          </div>
        </div>

        <!-- 列表视图 -->
        <div v-else class="projects-list">
          <a-table
            :columns="tableColumns"
            :data-source="projects"
            :pagination="pagination"
            @change="handleTableChange"
            row-key="id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <a @click="openProject(record)">{{ record.name }}</a>
              </template>
              <template v-else-if="column.key === 'type'">
                <a-tag :color="getProjectTypeColor(record.type)">
                  {{ getProjectTypeLabel(record.type) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">
                  {{ getStatusLabel(record.status) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'duration'">
                {{ formatDuration(record.duration) }}
              </template>
              <template v-else-if="column.key === 'created_at'">
                {{ formatTime(record.created_at) }}
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-space>
                  <a-button type="link" @click="openProject(record)">编辑</a-button>
                  <a-dropdown>
                    <a-button type="link">
                      更多
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M7,10L12,15L17,10H7Z"/>
                      </svg>
                    </a-button>
                    <template #overlay>
                      <a-menu @click="(e) => handleProjectAction(e, record)">
                        <a-menu-item key="duplicate">复制项目</a-menu-item>
                        <a-menu-item key="export">导出项目</a-menu-item>
                        <a-menu-divider />
                        <a-menu-item key="delete" class="danger-item">删除项目</a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </a-space>
              </template>
            </template>
          </a-table>
        </div>
      </a-spin>
    </div>

    <!-- 导入合成结果弹窗 -->
    <a-modal
      v-model:open="importModalVisible"
      title="导入合成结果"
      width="800px"
      @ok="handleImport"
      @cancel="importModalVisible = false"
    >
      <div class="import-content">
        <a-alert
          message="导入说明"
          description="从语音合成系统导入已完成的项目，自动创建音视频编辑项目并导入音频轨道。"
          type="info"
          show-icon
          style="margin-bottom: 16px"
        />
        
        <a-form :model="importForm" layout="vertical">
          <a-form-item label="选择合成项目" required>
            <a-select
              v-model:value="importForm.synthesisProjectId"
              placeholder="请选择要导入的合成项目"
              :loading="synthesisProjectsLoading"
              @dropdown-visible-change="loadSynthesisProjects"
            >
              <a-select-option
                v-for="project in synthesisProjects"
                :key="project.id"
                :value="project.id"
              >
                {{ project.name }} ({{ project.status === 'completed' ? '已完成' : '进行中' }})
              </a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="编辑项目名称" required>
            <a-input
              v-model:value="importForm.projectName"
              placeholder="输入编辑项目名称"
            />
          </a-form-item>
          
          <a-form-item label="项目描述">
            <a-textarea
              v-model:value="importForm.description"
              placeholder="输入项目描述（可选）"
              :rows="3"
            />
          </a-form-item>
        </a-form>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import api from '@/api'

const router = useRouter()

// 数据状态
const projects = ref([])
const loading = ref(false)
const viewMode = ref('grid') // 'grid' | 'list'

// 过滤器状态
const searchTerm = ref('')
const statusFilter = ref(undefined)
const typeFilter = ref(undefined)

// 分页状态
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

// 导入弹窗状态
const importModalVisible = ref(false)
const synthesisProjects = ref([])
const synthesisProjectsLoading = ref(false)
const importForm = ref({
  synthesisProjectId: undefined,
  projectName: '',
  description: ''
})

// 表格列配置
const tableColumns = [
  { title: '项目名称', dataIndex: 'name', key: 'name', width: 200 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '轨道数', dataIndex: 'track_count', key: 'track_count', width: 80 },
  { title: '时长', dataIndex: 'duration', key: 'duration', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 150 },
  { title: '操作', key: 'actions', width: 120 }
]

// 页面加载
onMounted(() => {
  loadProjects()
})

// 加载项目列表
const loadProjects = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      search: searchTerm.value || undefined,
      status: statusFilter.value,
      type: typeFilter.value
    }
    
    const response = await api.audioEditor.getProjects(params)
    console.log('项目列表API响应:', response)
    
    // 处理axios响应格式：response.data包含实际的API响应
    const apiResponse = response.data
    
    if (apiResponse && apiResponse.success) {
      projects.value = apiResponse.data.items || []
      pagination.value.total = apiResponse.data.total || 0
    } else {
      const errorMsg = apiResponse?.message || '未知错误'
      message.error('加载项目列表失败: ' + errorMsg)
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
    message.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

// 创建新项目
const createNewProject = () => {
  router.push('/editor/new')
}

// 打开项目编辑器
const openProject = (project) => {
  router.push(`/editor/project/${project.id}`)
}

// 导入合成结果
const importFromSynthesis = () => {
  importModalVisible.value = true
  importForm.value = {
    synthesisProjectId: undefined,
    projectName: '',
    description: ''
  }
}

// 加载合成项目列表
const loadSynthesisProjects = async (visible) => {
  if (!visible) return
  
  synthesisProjectsLoading.value = true
  try {
    const response = await api.getProjects({ status: 'completed' })
    console.log('合成项目API响应:', response)
    
    if (response.data && response.data.success) {
      // API返回格式: {success: true, data: [...]}
      // 其中 data 是项目数组
      synthesisProjects.value = response.data.data || []
    } else {
      synthesisProjects.value = []
    }
  } catch (error) {
    console.error('加载合成项目失败:', error)
    message.error('加载合成项目列表失败')
    synthesisProjects.value = []
  } finally {
    synthesisProjectsLoading.value = false
  }
}

// 处理导入
const handleImport = async () => {
  if (!importForm.value.synthesisProjectId || !importForm.value.projectName) {
    message.error('请填写必填字段')
    return
  }
  
  try {
    const response = await api.audioEditor.importFromSynthesis({
      source_project_id: importForm.value.synthesisProjectId,
      project_name: importForm.value.projectName,
      description: importForm.value.description
    })
    
    if (response.success) {
      message.success('导入成功')
      importModalVisible.value = false
      router.push(`/editor/project/${response.data.project_id}`)
    } else {
      message.error('导入失败: ' + response.message)
    }
  } catch (error) {
    console.error('导入失败:', error)
    message.error('导入失败')
  }
}

// 视图模式切换
const handleViewChange = ({ key }) => {
  viewMode.value = key
}

// 表格变化处理
const handleTableChange = (pag) => {
  pagination.value.current = pag.current
  pagination.value.pageSize = pag.pageSize
  loadProjects()
}

// 项目操作处理
const handleProjectAction = async ({ key }, project) => {
  switch (key) {
    case 'duplicate':
      await duplicateProject(project)
      break
    case 'export':
      await exportProject(project)
      break
    case 'delete':
      await deleteProject(project)
      break
  }
}

// 复制项目
const duplicateProject = async (project) => {
  try {
    const response = await api.audioEditor.duplicateProject(project.id)
    if (response.success) {
      message.success('项目复制成功')
      loadProjects()
    } else {
      message.error('复制失败: ' + response.message)
    }
  } catch (error) {
    console.error('复制项目失败:', error)
    message.error('复制项目失败')
  }
}

// 导出项目
const exportProject = async (project) => {
  try {
    const response = await api.audioEditor.exportProject(project.id)
    if (response.success) {
      message.success('导出成功')
      // 下载文件
      const link = document.createElement('a')
      link.href = response.data.download_url
      link.download = `${project.name}.zip`
      link.click()
    } else {
      message.error('导出失败: ' + response.message)
    }
  } catch (error) {
    console.error('导出项目失败:', error)
    message.error('导出项目失败')
  }
}

// 删除项目
const deleteProject = (project) => {
  // 实现删除确认逻辑
  message.warning('删除功能暂未实现')
}

// 工具函数
const getProjectTypeColor = (type) => {
  const colors = {
    audio_only: 'blue',
    video: 'green',
    synthesis_import: 'orange'
  }
  return colors[type] || 'default'
}

const getProjectTypeLabel = (type) => {
  const labels = {
    audio_only: '纯音频',
    video: '音视频',
    synthesis_import: '合成导入'
  }
  return labels[type] || type
}

const getStatusColor = (status) => {
  const colors = {
    draft: 'default',
    processing: 'processing',
    completed: 'success',
    error: 'error'
  }
  return colors[status] || 'default'
}

const getStatusLabel = (status) => {
  const labels = {
    draft: '草稿',
    processing: '处理中',
    completed: '已完成',
    error: '错误'
  }
  return labels[status] || status
}

const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const formatTime = (timestamp) => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm')
}
</script>

<style scoped>
.editor-projects {
  padding: 24px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-content {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.title-icon {
  color: #1890ff;
}

.page-description {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filters-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filters-left {
  display: flex;
  gap: 16px;
  align-items: center;
}

.filters-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.projects-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  min-height: 400px;
}

.empty-state {
  padding: 80px 40px;
  text-align: center;
}

.empty-content h3 {
  margin: 16px 0 8px 0;
  color: #374151;
  font-size: 18px;
}

.empty-content p {
  margin: 0 0 24px 0;
  color: #6b7280;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  padding: 24px;
}

.project-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.project-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.1);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-content {
  margin-bottom: 16px;
}

.project-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.project-description {
  margin: 0 0 16px 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
}

.project-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 12px;
}

.stat-label {
  color: #9ca3af;
  margin-right: 4px;
}

.stat-value {
  color: #374151;
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.project-meta {
  font-size: 12px;
  color: #9ca3af;
}

.update-time {
  display: block;
  margin-top: 2px;
}

.project-actions {
  display: flex;
  gap: 8px;
}

.projects-list {
  padding: 24px;
}

.import-content {
  padding: 16px 0;
}

.danger-item {
  color: #ff4d4f !important;
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .editor-projects {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: stretch;
  }
  
  .filters-section {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filters-left {
    flex-direction: column;
    gap: 12px;
  }
  
  .projects-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .card-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .project-actions {
    justify-content: center;
  }
}

/* 深色模式适配 */
[data-theme="dark"] .editor-projects {
  background: #141414 !important;
}

[data-theme="dark"] .page-header {
  background: #1f1f1f !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .page-title {
  color: #fff !important;
}

[data-theme="dark"] .title-icon {
  color: var(--primary-color) !important;
}

[data-theme="dark"] .page-description {
  color: #8c8c8c !important;
}

[data-theme="dark"] .filters-section {
  background: #1f1f1f !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .projects-container {
  background: #1f1f1f !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .empty-content h3 {
  color: #fff !important;
}

[data-theme="dark"] .empty-content p {
  color: #8c8c8c !important;
}

[data-theme="dark"] .empty-content svg {
  fill: #434343 !important;
}

[data-theme="dark"] .project-card {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .project-card:hover {
  border-color: var(--primary-color) !important;
  box-shadow: 0 4px 12px rgba(var(--primary-color-rgb), 0.2) !important;
}

[data-theme="dark"] .project-name {
  color: #fff !important;
}

[data-theme="dark"] .project-description {
  color: #8c8c8c !important;
}

[data-theme="dark"] .stat-label {
  color: #8c8c8c !important;
}

[data-theme="dark"] .stat-value {
  color: #d1d5db !important;
}

[data-theme="dark"] .card-footer {
  border-top-color: #434343 !important;
}

[data-theme="dark"] .project-meta {
  color: #8c8c8c !important;
}

[data-theme="dark"] .danger-item {
  color: #ff4d4f !important;
}

/* 深色模式下的表单组件适配 */
[data-theme="dark"] :deep(.ant-input) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-input:hover) {
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-input:focus) {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
}

[data-theme="dark"] :deep(.ant-input::placeholder) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-input-search .ant-input) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-input-search .ant-input-search-button) {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-select) {
  background-color: #2d2d2d !important;
}

[data-theme="dark"] :deep(.ant-select-selector) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-select-selection-item) {
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-select-arrow) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-select:hover .ant-select-selector) {
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-select-dropdown) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] :deep(.ant-select-item) {
  color: #d1d5db !important;
}

[data-theme="dark"] :deep(.ant-select-item-option-selected) {
  background-color: rgba(var(--primary-color-rgb), 0.2) !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-select-item:hover) {
  background-color: #3a3a3a !important;
}

[data-theme="dark"] :deep(.ant-btn-default) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-btn-default:hover) {
  background-color: #3a3a3a !important;
  border-color: var(--primary-color) !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-btn-text) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-btn-text:hover) {
  background-color: #2d2d2d !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-tag) {
  background: #2d2d2d !important;
  border-color: #434343 !important;
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-dropdown-menu) {
  background: #2d2d2d !important;
  border-color: #434343 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] :deep(.ant-dropdown-menu-item) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-dropdown-menu-item:hover) {
  background: #3a3a3a !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-spin-nested-loading) {
  background: transparent !important;
}

[data-theme="dark"] :deep(.ant-spin-container) {
  background: transparent !important;
}

[data-theme="dark"] :deep(.ant-spin-tip) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-modal-content) {
  background: #1f1f1f !important;
  border: 1px solid #434343 !important;
}

[data-theme="dark"] :deep(.ant-modal-header) {
  background: #1f1f1f !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-modal-title) {
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-modal-body) {
  background: #1f1f1f !important;
  color: #d1d5db !important;
}

[data-theme="dark"] :deep(.ant-modal-footer) {
  background: #1f1f1f !important;
  border-top-color: #434343 !important;
}
</style> 