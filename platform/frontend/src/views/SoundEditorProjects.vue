<template>
  <PageContainerWithStats
    title="合成中心"
    title-icon="SoundOutlined"
    :data="projects"
    :loading="loading"
    loading-tip="加载项目中..."
    
    :search-value="searchParams.search"
    search-placeholder="搜索项目名称..."
    :filters="searchFilters"
    :actions="headerActions"
    :table-columns="tableColumns"
    :show-pagination="true"
    :pagination="pagination"
    empty-title="暂无混合项目"
    empty-description="创建您的第一个混合项目"
    :empty-action="{ text: '立即创建', action: 'create' }"
    
    :show-stats="true"
    :stats="stats"
    :stats-config="statsConfig"
    
    @search="handleSearch"
    @filter-change="handleFilterChange"
    @refresh="loadProjects"
    @action="handleAction"
    
    @item-click="openProject"
    @edit="openProject"
    @view="openProject"
    @delete="deleteProject"
    @empty-action="createNewProject"
    @page-change="handlePageChange"
  >
    <!-- 自定义表格视图 -->
    <template #table-name="{ record }">
      <div style="display: flex; align-items: center; gap: 12px">
        <div class="table-avatar">
          {{ (record.title || record.name) ? (record.title || record.name).charAt(0) : '项' }}
        </div>
        <div>
          <div style="font-weight: 500">{{ record.title || record.name }}</div>
          <div style="font-size: 12px; color: #6b7280">{{ record.description || '暂无描述' }}</div>
        </div>
      </div>
    </template>

    <template #table-type="{ record }">
      <a-tag :color="getProjectTypeColor(record)">
        {{ getProjectTypeLabel(record) }}
      </a-tag>
    </template>

    <template #table-status="{ record }">
      <a-tag :color="getStatusColor(record.status)">
        {{ getStatusText(record.status) }}
      </a-tag>
    </template>

    <template #table-created_at="{ record }">
      {{ formatDate(record.createdAt) }}
    </template>

    <template #table-actions="{ record }">
      <TableActions
        :record="record"
        :show-edit="true"
        :show-view="true"
        :show-delete="true"
        @edit="openProject"
        @view="openProject"
        @delete="handleDeleteProject"
      />
    </template>
  </PageContainerWithStats>

  <!-- 新建项目弹窗 -->
  <a-modal
    v-model:open="newProjectModalVisible"
    title="新建混合项目"
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

        <!-- 书籍选择 -->
        <a-form-item label="选择书籍" required>
          <a-select 
            v-model:value="newProjectForm.bookId" 
            placeholder="请选择书籍"
            :loading="booksLoading"
          >
            <a-select-option v-for="book in books" :key="book.id" :value="book.id">
              {{ book.title }} - {{ book.author }}
            </a-select-option>
          </a-select>
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
          <a-select v-model:value="newProjectForm.template" placeholder="选择项目模板">
            <a-select-option value="default">标准三轨模板</a-select-option>
            <a-select-option value="dialogue">对话专用模板</a-select-option>
            <a-select-option value="music">音乐制作模板</a-select-option>
            <a-select-option value="empty">空白项目</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </div>
  </a-modal>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { message, Modal } from 'ant-design-vue'
  import {
    listProjects,
    createProject,
    deleteProject
  } from '@/api/sound-editor/multitrackProject'
  import { booksAPI } from '@/api'
  import PageContainerWithStats from '@/components/common/PageContainerWithStats.vue'
  import TableActions from '@/components/common/TableActions.vue'
  import { useErrorHandler } from '@/composables/useErrorHandler'
  import { getStatusColor, getStatusText, formatDate } from '@/utils/formatters'
  import {
    PROJECT_TABLE_COLUMNS,
    PROJECT_SEARCH_FILTERS,
    PROJECT_HEADER_ACTIONS,
    PROJECT_DEFAULT_SEARCH_PARAMS,
    PROJECT_STATS_CONFIG
  } from '@/config/soundEditorConfig'

  const router = useRouter()
  const { handleApiError } = useErrorHandler()

  // 数据状态
  const projects = ref([])
  const loading = ref(false)
  const stats = ref({})

  // 搜索和筛选参数
  const searchParams = ref({ ...PROJECT_DEFAULT_SEARCH_PARAMS })
  const searchFilters = PROJECT_SEARCH_FILTERS
  const headerActions = PROJECT_HEADER_ACTIONS
  const tableColumns = PROJECT_TABLE_COLUMNS
  const statsConfig = PROJECT_STATS_CONFIG

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
    template: 'default',
    bookId: null
  })

  // 书籍相关数据
  const books = ref([])
  const booksLoading = ref(false)

  // 页面加载
  onMounted(() => {
    console.log('SoundEditorProjects组件已挂载')
    loadProjects()
    loadBooks()
  })

  // 事件处理方法
  const handleSearch = (value) => {
    searchParams.value.search = value
    loadProjects()
  }

  const handleFilterChange = (filters) => {
    Object.assign(searchParams.value, filters)
    loadProjects()
  }

  const handleAction = (action) => {
    switch (action.action) {
      case 'create':
        createNewProject()
        break
      case 'refresh':
        loadProjects()
        break
    }
  }

  const handlePageChange = (page, pageSize) => {
    pagination.value.current = page
    pagination.value.pageSize = pageSize
    loadProjects()
  }

  // 加载书籍列表
  const loadBooks = async () => {
    try {
      booksLoading.value = true
      console.log('开始加载书籍列表...')
      const response = await booksAPI.getBooks({ page: 1, page_size: 100 })
      console.log('书籍API响应:', response)
      if (response.data && response.data.success) {
        books.value = response.data.data || []
        console.log('加载到的书籍:', books.value)
      } else {
        console.error('书籍API返回失败:', response)
        message.error('加载书籍列表失败: ' + (response.data?.message || '未知错误'))
      }
    } catch (error) {
      console.error('加载书籍列表失败:', error)
      message.error('加载书籍列表失败: ' + error.message)
    } finally {
      booksLoading.value = false
    }
  }

  // 加载项目列表
  const loadProjects = async () => {
    loading.value = true
    try {
      const response = await listProjects()
      console.log('音频混合项目列表:', response)

      if (response && response.success) {
        let projectList = response.projects || []

        // 应用搜索过滤
        if (searchParams.value.search) {
          projectList = projectList.filter((project) =>
            (project.title || project.name || '')
              .toLowerCase()
              .includes(searchParams.value.search.toLowerCase())
          )
        }

        // 应用类型过滤
        if (searchParams.value.type) {
          projectList = projectList.filter((project) => {
            const projectType = getProjectType(project)
            return projectType === searchParams.value.type
          })
        }

        // 应用状态过滤
        if (searchParams.value.status) {
          projectList = projectList.filter((project) => 
            project.status === searchParams.value.status
          )
        }

        // 排序
        if (searchParams.value.sort_by) {
          projectList.sort((a, b) => {
            const aValue = a[searchParams.value.sort_by]
            const bValue = b[searchParams.value.sort_by]
            if (searchParams.value.sort_order === 'desc') {
              return bValue > aValue ? 1 : -1
            } else {
              return aValue > bValue ? 1 : -1
            }
          })
        }

        projects.value = projectList
        pagination.value.total = projectList.length

        // 更新统计数据
        updateStats(projectList)
      } else {
        message.error('加载项目列表失败')
      }
    } catch (error) {
      handleApiError(error, '加载项目列表')
    } finally {
      loading.value = false
    }
  }

  // 更新统计数据
  const updateStats = (projectList) => {
    const total = projectList.length
    const completed = projectList.filter(p => p.status === 'completed').length
    const processing = projectList.filter(p => p.status === 'processing').length
    const failed = projectList.filter(p => p.status === 'failed').length

    stats.value = {
      total_projects: total,
      completed_projects: completed,
      processing_projects: processing,
      failed_projects: failed
    }
  }

  // 创建新项目
  const createNewProject = () => {
    newProjectForm.value = {
      title: '',
      description: '',
      template: 'default',
      bookId: null
    }
    newProjectModalVisible.value = true
  }

  // 处理创建项目
  const handleCreateProject = async () => {
    if (!newProjectForm.value.title) {
      message.error('请输入项目名称')
      return
    }

    if (!newProjectForm.value.bookId) {
      message.error('请选择书籍')
      return
    }

    try {
      // 创建项目信息
      const projectInfo = {
        title: String(newProjectForm.value.title || ''),
        description: String(newProjectForm.value.description || ''),
        author: 'AI-Sound',
        bookId: newProjectForm.value.bookId,
        totalDuration: 0.0,
        sampleRate: 44100,
        channels: 2,
        bitDepth: 16,
        exportFormat: 'wav',
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
      } else {
        message.error('创建项目失败: ' + (response?.message || '未知错误'))
      }
    } catch (error) {
      handleApiError(error, '创建项目')
    }
  }

  // 打开项目
  const openProject = (project) => {
    router.push(`/sound-editor/edit/${project.id}`)
  }

  // 删除项目
  const handleDeleteProject = (project) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除项目 "${project.title || project.name}" 吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteProject(project.id)
          message.success('项目删除成功')
          loadProjects()
        } catch (error) {
          handleApiError(error, '删除项目')
        }
      }
    })
  }

  // 获取项目类型
  const getProjectType = (project) => {
    if (!project.tracks) return 'mixed'

    const hasDialogue = project.tracks.some(
      (track) => track.type === 'dialogue' && track.clips?.length > 0
    )
    const hasEnvironment = project.tracks.some(
      (track) => track.type === 'environment' && track.clips?.length > 0
    )
    const hasMusic = project.tracks.some(
      (track) => track.type === 'background' && track.clips?.length > 0
    )

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
</script>

<style scoped>
  .table-avatar {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 16px;
  }

  .book-import-placeholder {
    padding: 20px;
    text-align: center;
  }
</style>
