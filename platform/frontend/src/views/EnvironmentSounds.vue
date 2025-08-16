<template>
  <PageContainer
    title="环境音合成"
    title-icon="SoundOutlined"
    :data="projects"
    :loading="loading"
    loading-tip="加载环境音项目中..."
    
    :search-value="searchParams.search"
    search-placeholder="搜索项目名称..."
    :filters="searchFilters"
    :actions="headerActions"
    :table-columns="tableColumns"
    :show-pagination="true"
    :pagination="pagination"
    empty-title="暂无环境音项目"
    empty-description="创建您的第一个环境音分析项目"
    :empty-action="{ text: '立即创建', action: 'create' }"
    @search="handleSearch"
    @filter-change="handleFilterChange"
    @refresh="loadProjects"
    @action="handleAction"
    
    @item-click="viewProjectDetail"
    @edit="viewProjectDetail"
    @view="viewProjectDetail"
    @delete="deleteProject"
    @empty-action="handleEmptyAction"
    @page-change="handlePageChange"
  >
    <!-- 自定义表格视图 -->
    <template #table-name="{ record }">
      <div style="display: flex; align-items: center; gap: 12px">
        <div class="table-avatar">
          {{ record.name ? record.name.charAt(0) : '环' }}
        </div>
        <div>
          <div style="font-weight: 500">{{ record.name || '未命名项目' }}</div>
          <div style="font-size: 12px; color: #6b7280">{{ record.description || '暂无描述' }}</div>
        </div>
      </div>
    </template>

    <template #table-book="{ record }">
      <div>
        <BookOutlined style="margin-right: 8px" />
        {{ record.book?.title || '未知书籍' }}
      </div>
    </template>

    <template #table-status="{ record }">
      <a-tag :color="getStatusColor(record.status)">
        {{ getStatusText(record.status) }}
      </a-tag>
    </template>

    <template #table-soundCount="{ record }">
      <div>
        <SoundOutlined style="margin-right: 8px" />
        {{ record.sound_count || 0 }} 个
      </div>
    </template>

    <template #table-createdAt="{ record }">
      {{ formatDate(record.created_at) }}
    </template>

    <template #table-actions="{ record }">
      <TableActions
        :record="record"
        :show-edit="true"
        :show-view="true"
        :show-delete="true"
        @edit="viewProjectDetail"
        @view="viewProjectDetail"
        @delete="deleteProject"
      >
        <template #custom-actions="{ record }">
          <a-button 
            type="text" 
            size="small" 
            @click.stop="viewGeneratedSounds(record)"
          >
            <SoundOutlined />
            查看音效
          </a-button>
        </template>
      </TableActions>
    </template>
  </PageContainer>

  <!-- 删除确认弹窗 -->
  <a-modal
    :open="deleteModal.visible"
    title="确认删除"
    @ok="confirmDelete"
    @cancel="deleteModal.visible = false"
  >
    <p>确定要删除环境音分析项目 "{{ deleteModal.project?.name || '未命名项目' }}" 吗？</p>
    <p v-if="deleteModal.project?.sound_count > 0" style="color: red">
      ⚠️ 该项目已生成 {{ deleteModal.project.sound_count }} 个环境音文件，删除后这些文件也会被删除。
    </p>
  </a-modal>

  <!-- 新增项目抽屉 -->
  <CreateProjectDrawer
    v-model:open="showCreateProjectDrawer"
    :books="books"
    :loading="booksLoading"
    @create="handleCreateProject"
  />
</template>

<script setup>
  import { ref, reactive, onMounted, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import { message } from 'ant-design-vue'
  import { BookOutlined, SoundOutlined } from '@ant-design/icons-vue'
  import { environmentGenerationAPI } from '@/api'
  import { booksAPI } from '@/api'
  import { useErrorHandler } from '@/composables/useErrorHandler'
  import { getStatusColor, getStatusText, formatDate } from '@/utils/formatters'
  import {
    ENVIRONMENT_PROJECT_TABLE_COLUMNS,
    ENVIRONMENT_PROJECT_SEARCH_FILTERS,
    ENVIRONMENT_PROJECT_HEADER_ACTIONS,
    ENVIRONMENT_PROJECT_DEFAULT_SEARCH_PARAMS
  } from '@/config/environmentSoundsConfig'
  import PageContainer from '@/components/common/PageContainer.vue'
  import TableActions from '@/components/common/TableActions.vue'
  import CreateProjectDrawer from '@/components/environment-sounds/CreateProjectDrawer.vue'

    // 路由
    const router = useRouter()
    const { handleApiError } = useErrorHandler()

    // 响应式数据
    const loading = ref(false)
    const projects = ref([])
    const books = ref([])
    const booksLoading = ref(false)

    // 搜索参数
    const searchParams = reactive({
      search: '',
      ...ENVIRONMENT_PROJECT_DEFAULT_SEARCH_PARAMS
    })

    // 分页
    const pagination = reactive({
      page: 1,
      pageSize: 20,
      total: 0
    })

    // 删除弹窗
    const deleteModal = reactive({
      visible: false,
      project: null,
      force: false
    })

    // 新增项目抽屉控制
    const showCreateProjectDrawer = ref(false)

    // 搜索筛选器配置
    const searchFilters = computed(() => ENVIRONMENT_PROJECT_SEARCH_FILTERS)

    // 头部操作按钮配置
    const headerActions = computed(() => ENVIRONMENT_PROJECT_HEADER_ACTIONS)

    // 表格列定义
    const tableColumns = ENVIRONMENT_PROJECT_TABLE_COLUMNS

  // 移除智能分析相关状态和书籍章节数据（已统一使用新增项目抽屉）



  // 生命周期
  onMounted(() => {
    loadInitialData()
  })

  // 方法
  const loadInitialData = async () => {
    console.log('🚀 开始加载初始数据')
    try {
      await Promise.all([
        loadProjects(),
        loadBooks(),
        loadStats()
      ])
      console.log('✅ 初始数据加载完成')
    } catch (error) {
      console.error('❌ 初始数据加载失败:', error)
    }
  }

  const loadBooks = async () => {
    try {
      booksLoading.value = true
      const response = await booksAPI.getBooks()
      
      if (response.data.success) {
        books.value = response.data.data || []
        console.log('✅ 书籍列表加载成功:', books.value.length)
      } else {
        message.error('加载书籍列表失败')
      }
    } catch (error) {
      console.error('加载书籍列表失败:', error)
      message.error('加载书籍列表失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      booksLoading.value = false
    }
  }

  const loadProjects = async () => {
    try {
      loading.value = true
      
      // 构建查询参数
      const params = {
        page: pagination.page,
        page_size: pagination.pageSize,
        ...searchParams
      }

      // 调用API获取项目列表
      const response = await environmentGenerationAPI.getProjects(params)
      
      if (response.data.success) {
        // 修复：后端返回的是 response.data.data.data.projects
        const projectData = response.data.data.data || response.data.data
        projects.value = projectData.projects || []
        pagination.total = projectData.total || 0
      } else {
        message.error('加载项目列表失败')
      }
    } catch (error) {
      handleApiError(error, '加载环境音项目列表')
    } finally {
      loading.value = false
    }
  }

  const loadStats = async () => {
    // 统计功能已移除
    console.log('统计功能已移除')
  }

  const handleSearch = (value) => {
    searchParams.search = value
    loadProjects()
  }

  const handleFilterChange = (filters) => {
    Object.assign(searchParams, filters)
    loadProjects()
  }

  const handlePageChange = ({ page, pageSize }) => {
    pagination.page = page
    pagination.pageSize = pageSize
    loadProjects()
  }



  const viewProjectDetail = (project) => {
    router.push({
      name: 'EnvironmentAnalysisDetail',
      params: { 
        analysisId: project.id
      }
    })
  }

  const deleteProject = (project) => {
    deleteModal.project = project
    deleteModal.visible = true
    deleteModal.force = false
  }

  const confirmDelete = async () => {
    try {
      await environmentGenerationAPI.deleteProject(deleteModal.project.id)
      message.success('项目删除成功')
      deleteModal.visible = false
      loadProjects()
    } catch (error) {
      handleApiError(error, '删除环境音项目')
    }
  }



  const viewGeneratedSounds = (project) => {
    // 跳转到音频库页面，显示该项目生成的环境音
    router.push({
      name: 'AudioLibrary',
      query: { 
        project_id: project.id,
        filter: 'environment_sounds'
      }
    })
  }

  // 移除智能分析相关方法（已统一使用新增项目抽屉）

  // 移除生成相关方法（已统一使用新增项目抽屉）

  const handleAction = (action) => {
    if (action.action === 'create') {
      showCreateProjectDrawer.value = true
    }
  }

  const handleEmptyAction = () => {
    showCreateProjectDrawer.value = true
  }



  const handleCreateProject = async (projectData) => {
    try {
      message.success('环境音分析项目创建成功！正在跳转到项目详情...')
      
      // 跳转到项目详情页面
      router.push(`/environment-sounds/analysis/${projectData.id}`)
      
      // 刷新项目列表
      loadProjects()
    } catch (error) {
      handleApiError(error, '处理创建项目结果')
    }
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
</style>
