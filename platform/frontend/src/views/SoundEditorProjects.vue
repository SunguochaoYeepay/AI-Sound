<template>
  <div class="sound-editor-projects">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" class="title-icon">
            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
          </svg>
          音频编辑器
        </h1>
        <p class="page-description">专业级多轨音频编辑工具，支持对话、环境音、背景音乐混合制作</p>
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
        
        <a-button size="large" @click="importFromBook">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21,5c-1.11-0.35-2.33-0.5-3.5-0.5c-1.95,0-4.05,0.4-5.5,1.5c-1.45-1.1-3.55-1.5-5.5-1.5S2.45,4.9,1,6v14.65 c0,0.25,0.25,0.5,0.5,0.5c0.1,0,0.15-0.05,0.25-0.05C3.1,20.45,5.05,20,6.5,20c1.95,0,4.05,0.4,5.5,1.5c1.35-0.85,3.8-1.5,5.5-1.5 c1.65,0,3.35,0.3,4.75,1.05c0.1,0.05,0.15,0.05,0.25,0.05c0.25,0,0.5-0.25,0.5-0.5V6C22.4,5.55,21.75,5.25,21,5z M21,18.5 c-1.1-0.35-2.3-0.5-3.5-0.5c-1.7,0-4.15,0.65-5.5,1.5V8c1.35-0.85,3.8-1.5,5.5-1.5c1.2,0,2.4,0.15,3.5,0.5V18.5z"/>
            </svg>
          </template>
          从书籍导入
        </a-button>
        
        <a-button size="large" @click="importProject">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
          </template>
          导入项目
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
          v-model:value="typeFilter"
          placeholder="项目类型"
          style="width: 150px"
          allow-clear
          @change="loadProjects"
        >
          <a-select-option value="dialogue">对话项目</a-select-option>
          <a-select-option value="environment">环境音项目</a-select-option>
          <a-select-option value="music">音乐项目</a-select-option>
          <a-select-option value="mixed">混合项目</a-select-option>
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
              <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
            <h3>暂无音频项目</h3>
            <p>创建您的第一个多轨音频编辑项目，开始专业音频制作。</p>
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
                <a-tag :color="getProjectTypeColor(project)">
                  {{ getProjectTypeLabel(project) }}
                </a-tag>
              </div>
              <div class="project-status">
                <span class="project-version">v{{ project.version || '1.0' }}</span>
              </div>
            </div>
            
            <div class="card-content">
              <h3 class="project-name">{{ project.title || project.name }}</h3>
              <p class="project-description">{{ project.description || '暂无描述' }}</p>
              
              <div class="project-stats">
                <div class="stat-item">
                  <span class="stat-label">轨道数:</span>
                  <span class="stat-value">{{ getTrackCount(project) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">时长:</span>
                  <span class="stat-value">{{ formatDuration(project.totalDuration || 0) }}</span>
                </div>
              </div>
            </div>
            
            <div class="card-footer">
              <div class="project-meta">
                <span class="create-time">{{ formatTime(project.createdAt) }}</span>
                <span class="update-time">更新于 {{ formatTime(project.updatedAt || project.createdAt) }}</span>
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
                      <a-menu-item key="export">导出音频</a-menu-item>
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
                <a @click="openProject(record)">{{ record.title || record.name }}</a>
              </template>
              <template v-else-if="column.key === 'type'">
                <a-tag :color="getProjectTypeColor(record)">
                  {{ getProjectTypeLabel(record) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'tracks'">
                {{ getTrackCount(record) }}
              </template>
              <template v-else-if="column.key === 'duration'">
                {{ formatDuration(record.totalDuration || 0) }}
              </template>
              <template v-else-if="column.key === 'created_at'">
                {{ formatTime(record.createdAt) }}
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
                        <a-menu-item key="export">导出音频</a-menu-item>
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

    <!-- 新建项目弹窗 -->
    <a-modal
      v-model:open="newProjectModalVisible"
      title="新建音频项目"
      width="600px"
      @ok="handleCreateProject"
      @cancel="newProjectModalVisible = false"
    >
      <div class="new-project-content">
        <a-form :model="newProjectForm" layout="vertical">
          <a-form-item label="项目名称" required>
            <a-input
              v-model:value="newProjectForm.title"
              placeholder="输入项目名称"
              :maxlength="50"
            />
          </a-form-item>
          
          <a-form-item label="项目描述">
            <a-textarea
              v-model:value="newProjectForm.description"
              placeholder="输入项目描述（可选）"
              :rows="3"
              :maxlength="200"
            />
          </a-form-item>
          
          <a-form-item label="项目模板">
            <a-select
              v-model:value="newProjectForm.template"
              placeholder="选择项目模板"
            >
              <a-select-option value="default">标准三轨模板</a-select-option>
              <a-select-option value="dialogue">对话专用模板</a-select-option>
              <a-select-option value="music">音乐制作模板</a-select-option>
              <a-select-option value="empty">空白项目</a-select-option>
            </a-select>
          </a-form-item>
        </a-form>
      </div>
    </a-modal>
    
    <!-- 从书籍导入资源弹窗 -->
    <a-modal
      v-model:open="bookImportModalVisible"
      title="从书籍导入资源"
      width="900px"
      :footer="null"
      :destroyOnClose="true"
    >
      <BookChapterSelector @created="onProjectCreatedFromBook" />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import dayjs from 'dayjs'
import { listProjects, createProject, deleteProject, createEmptyProject } from '@/api/sound-editor/multitrackProject'
import BookChapterSelector from '@/components/sound-editor/BookChapterSelector.vue'

const router = useRouter()

// 数据状态
const projects = ref([])
const loading = ref(false)
const viewMode = ref('grid') // 'grid' | 'list'

// 过滤器状态
const searchTerm = ref('')
const typeFilter = ref(undefined)

// 分页状态
const pagination = ref({
  current: 1,
  pageSize: 12,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

// 新建项目弹窗状态
const newProjectModalVisible = ref(false)
const newProjectForm = ref({
  title: '',
  description: '',
  template: 'default'
})

// 从书籍导入弹窗状态
const bookImportModalVisible = ref(false)

// 表格列配置
const tableColumns = [
  { title: '项目名称', dataIndex: 'title', key: 'name', width: 200 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 120 },
  { title: '轨道数', dataIndex: 'tracks', key: 'tracks', width: 80 },
  { title: '时长', dataIndex: 'totalDuration', key: 'duration', width: 100 },
  { title: '创建时间', dataIndex: 'createdAt', key: 'created_at', width: 150 },
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
    const response = await listProjects()
    console.log('音频编辑器项目列表:', response)
    
    if (response && response.success) {
      let projectList = response.projects || []
      
      // 应用过滤器
      if (searchTerm.value) {
        projectList = projectList.filter(project => 
          (project.title || project.name || '').toLowerCase().includes(searchTerm.value.toLowerCase())
        )
      }
      
      if (typeFilter.value) {
        projectList = projectList.filter(project => {
          const projectType = getProjectType(project)
          return projectType === typeFilter.value
        })
      }
      
      projects.value = projectList
      pagination.value.total = projectList.length
    } else {
      message.error('加载项目列表失败')
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
  newProjectForm.value = {
    title: '',
    description: '',
    template: 'default'
  }
  newProjectModalVisible.value = true
}

// 处理创建项目
const handleCreateProject = async () => {
  if (!newProjectForm.value.title) {
    message.error('请输入项目名称')
    return
  }
  
  try {
    // 创建项目信息（确保所有必需字段都有正确的数据类型）
    const projectInfo = {
      title: String(newProjectForm.value.title || ''),
      description: String(newProjectForm.value.description || ''),
      author: 'AI-Sound',
      totalDuration: 0.0,  // 确保是浮点数
      sampleRate: 44100,   // 确保是整数
      channels: 2,         // 确保是整数
      bitDepth: 16,        // 确保是整数
      exportFormat: 'wav', // 确保是字符串
      createdAt: new Date().toISOString(),
      version: '1.0'
    }
    
    // 后端API期望的格式
    const requestData = {
      project: projectInfo
    }
    
    console.log('发送创建项目请求:', requestData)
    const response = await createProject(requestData)
    
    if (response && response.success) {
      message.success('项目创建成功')
      newProjectModalVisible.value = false
      loadProjects()
      
      // 创建后直接进入编辑器
      if (response.data && response.data.project && response.data.project.id) {
        router.push(`/sound-editor/edit/${response.data.project.id}`)
      }
    } else {
      message.error('创建项目失败')
    }
  } catch (error) {
    console.error('创建项目失败:', error)
    if (error.response) {
      console.error('API响应错误:', error.response.data)
      
      // 显示详细的验证错误
      if (error.response.data.detail && Array.isArray(error.response.data.detail)) {
        const errors = error.response.data.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join('\n')
        console.error('验证错误详情:', errors)
        message.error(`数据验证失败:\n${errors}`)
      } else {
        message.error(`创建项目失败: ${error.response.data.detail || error.response.statusText}`)
      }
    } else {
      message.error('创建项目失败: 网络错误')
    }
  }
}

// 打开项目
const openProject = (project) => {
  router.push(`/sound-editor/edit/${project.id}`)
}

// 导入项目
const importProject = () => {
  message.info('导入功能开发中')
}

// 从书籍导入资源
const importFromBook = () => {
  bookImportModalVisible.value = true
}

// 处理从书籍创建项目成功
const onProjectCreatedFromBook = (result) => {
  bookImportModalVisible.value = false
  loadProjects()
  
  // 显示创建结果
  if (result && result.projectId) {
    message.success(`项目创建成功，已导入${result.summary?.chapters_count || 0}个章节的资源`)
  }
}

// 处理视图切换
const handleViewChange = ({ key }) => {
  viewMode.value = key
}

// 处理表格变化
const handleTableChange = (pag) => {
  pagination.value.current = pag.current
  pagination.value.pageSize = pag.pageSize
}

// 处理项目操作
const handleProjectAction = async ({ key }, project) => {
  switch (key) {
    case 'duplicate':
      message.info('复制功能开发中')
      break
    case 'export':
      message.info('导出功能开发中')
      break
    case 'delete':
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除项目 "${project.title || project.name}" 吗？此操作不可恢复。`,
        okText: '确认删除',
        okType: 'danger',
        cancelText: '取消',
        onOk: async () => {
          try {
            const response = await deleteProject(project.id)
            if (response && response.success) {
              message.success('项目删除成功')
              loadProjects()
            } else {
              message.error('删除项目失败')
            }
          } catch (error) {
            console.error('删除项目失败:', error)
            message.error('删除项目失败')
          }
        }
      })
      break
  }
}

// 获取项目类型
const getProjectType = (project) => {
  if (!project.tracks) return 'mixed'
  
  const hasDialogue = project.tracks.some(track => track.type === 'dialogue' && track.clips?.length > 0)
  const hasEnvironment = project.tracks.some(track => track.type === 'environment' && track.clips?.length > 0)
  const hasMusic = project.tracks.some(track => track.type === 'background' && track.clips?.length > 0)
  
  if (hasDialogue && hasEnvironment && hasMusic) return 'mixed'
  if (hasDialogue) return 'dialogue'
  if (hasEnvironment) return 'environment'
  if (hasMusic) return 'music'
  return 'mixed'
}

// 获取项目类型标签
const getProjectTypeLabel = (project) => {
  const type = getProjectType(project)
  const labels = {
    dialogue: '对话项目',
    environment: '环境音',
    music: '音乐项目',
    mixed: '混合项目'
  }
  return labels[type] || '混合项目'
}

// 获取项目类型颜色
const getProjectTypeColor = (project) => {
  const type = getProjectType(project)
  const colors = {
    dialogue: 'blue',
    environment: 'green',
    music: 'red',
    mixed: 'purple'
  }
  return colors[type] || 'purple'
}

// 获取轨道数量
const getTrackCount = (project) => {
  return project.tracks ? project.tracks.length : 3
}

// 时间格式化
const formatTime = (time) => {
  if (!time) return '暂无'
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

// 时长格式化
const formatDuration = (seconds) => {
  if (!seconds || seconds <= 0) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.sound-editor-projects {
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-content .page-title {
  display: flex;
  align-items: center;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.title-icon {
  margin-right: 12px;
  color: #3b82f6;
}

.page-description {
  margin: 8px 0 0 0;
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
  padding: 16px 24px;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.filters-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filters-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.projects-container {
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-content h3 {
  margin: 16px 0 8px 0;
  color: #4b5563;
}

.empty-content p {
  color: #6b7280;
  margin-bottom: 24px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.project-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.project-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.project-version {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
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
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.project-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.create-time,
.update-time {
  font-size: 12px;
  color: #6b7280;
}

.project-actions {
  display: flex;
  gap: 8px;
}

.projects-list {
  overflow-x: auto;
}

.danger-item {
  color: #ef4444 !important;
}

.new-project-content {
  padding: 8px 0;
}
</style> 