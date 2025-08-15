<template>
  <div class="environment-sounds-page">
    <!-- 页面头部 -->
    <PageHeader title="环境音合成">
      <template #actions>
        <a-button type="primary" size="large" @click="startNewAnalysis">
          <BulbOutlined />
          新建环境音分析
        </a-button>
      </template>
    </PageHeader>

    <!-- 筛选和搜索 -->
    <FilterSection
      :filters="searchForm"
      :books="books"
      @search="loadProjects"
      @reset="resetSearch"
    />

    <!-- 环境音分析项目列表 -->
    <ProjectList
      :projects="projects"
      :loading="loading"
      :pagination="pagination"
      @project-click="viewProjectDetail"
      @delete="deleteProject"
      @view-sounds="viewGeneratedSounds"
      @page-change="handlePageChange"
      @size-change="handlePageSizeChange"
    />

    <!-- 新增项目抽屉 -->
    <CreateProjectDrawer
      v-model:open="showCreateProjectDrawer"
      :books="books"
      :loading="booksLoading"
      @create="handleCreateProject"
    />

    <!-- 编辑对话框 -->
    <EditModal
      v-model:open="showEditModal"
      :sound="editingSound"
      @success="handleEditSuccess"
    />
  </div>
</template>

<script setup>
  import { ref, reactive, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { message, Modal } from 'ant-design-vue'
  import {
    BulbOutlined
  } from '@ant-design/icons-vue'
  import { environmentGenerationAPI } from '@/api'
  import { booksAPI } from '@/api'
  
  // 导入缺失的组件
  import PageHeader from '@/components/PageHeader.vue'
  import FilterSection from '@/components/environment-sounds/FilterSection.vue'
  import ProjectList from '@/components/environment-sounds/ProjectList.vue'
  import CreateProjectDrawer from '@/components/environment-sounds/CreateProjectDrawer.vue'
  import EditModal from '@/components/environment-sounds/EditModal.vue'

    // 路由
    const router = useRouter()

    // 响应式数据
    const loading = ref(false)

  // 项目相关数据
  const projects = ref([])
  
  // 书籍相关数据
  const books = ref([])
  const booksLoading = ref(false)

  // 搜索表单
  const searchForm = reactive({
    search: '',
    category_id: null,
    tag_ids: [],
    status: null,
    dateRange: []
  })

  // 排序和筛选
  const showFeaturedOnly = ref(false)
  const sortBy = ref('created_at')

  // 分页
  const pagination = reactive({
    current: 1,
    pageSize: 20,
    total: 0
  })

  // 弹窗控制
  const showEditModal = ref(false)
  const editingSound = ref(null)

  // 新增项目抽屉控制
  const showCreateProjectDrawer = ref(false)

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
        page: pagination.current,
        page_size: pagination.pageSize,
        search: searchForm.search,
        status: searchForm.status,
        sort_by: sortBy.value
      }

      // 添加日期范围
      if (searchForm.dateRange && searchForm.dateRange.length === 2) {
        params.start_date = searchForm.dateRange[0].format('YYYY-MM-DD')
        params.end_date = searchForm.dateRange[1].format('YYYY-MM-DD')
      }

      // 调用API获取项目列表
      const response = await environmentGenerationAPI.getProjects(params)
      
      console.log('🔍 项目列表API响应:', response.data)
      
      if (response.data.success) {
        // 修复：后端返回的是 response.data.data.data.projects
        const projectData = response.data.data.data || response.data.data
        projects.value = projectData.projects || []
        pagination.total = projectData.total || 0
        
        console.log('✅ 项目列表加载成功:', {
          projectsCount: projects.value.length,
          total: pagination.total,
          projects: projects.value
        })
      } else {
        message.error('加载项目列表失败')
      }
    } catch (error) {
      console.error('加载项目列表失败:', error)
      message.error('加载项目列表失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      loading.value = false
    }
  }

  const loadStats = async () => {
    // 统计功能已移除
    console.log('统计功能已移除')
  }

  // 移除书籍和章节加载方法（已统一使用新增项目抽屉）

  const resetSearch = () => {
    Object.assign(searchForm, {
      search: '',
      category_id: null,
      tag_ids: [],
      status: null,
      dateRange: []
    })
    showFeaturedOnly.value = false
    sortBy.value = 'created_at'
    pagination.current = 1
    loadProjects()
  }

  const handlePageChange = (page, pageSize) => {
    pagination.current = page
    pagination.pageSize = pageSize
    loadProjects()
  }

  const handlePageSizeChange = (current, size) => {
    pagination.current = 1
    pagination.pageSize = size
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

  const deleteProject = async (project) => {
    try {
      // 显示确认对话框
      const confirmed = await new Promise((resolve) => {
        Modal.confirm({
          title: '确认删除',
          content: `确定要删除分析项目"${project.name || '未命名项目'}"吗？此操作不可恢复。`,
          okText: '确认删除',
          okType: 'danger',
          cancelText: '取消',
          onOk: () => resolve(true),
          onCancel: () => resolve(false)
        })
      })

      if (!confirmed) return

      // 调用删除API
      await environmentGenerationAPI.deleteProject(project.id)
      
      message.success('项目删除成功')
      
      // 重新加载项目列表
      await loadProjects()
      
    } catch (error) {
      console.error('删除项目失败:', error)
      message.error('删除项目失败: ' + (error.response?.data?.detail || error.message))
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

  const handleEditSuccess = () => {
    loadProjects()
    loadStats()
  }

  const startNewAnalysis = () => {
    // 直接显示新增项目抽屉，不需要验证章节选择
    showCreateProjectDrawer.value = true
  }



  const handleCreateProject = async (projectData) => {
    try {
      message.success('环境音分析项目创建成功！正在跳转到项目详情...')
      
      // 跳转到项目详情页面
      router.push(`/environment-sounds/analysis/${projectData.id}`)
      
      // 刷新项目列表
      loadProjects()
      loadStats()
    } catch (error) {
      console.error('处理创建项目结果失败:', error)
      message.error('处理创建项目结果失败: ' + (error.response?.data?.detail || error.message))
    }
  }


</script>

<style scoped>
  .page-header {
    margin-bottom: 24px;
    padding: 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .title-with-back {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .back-btn {
    font-size: 16px;
    padding: 4px 8px;
    display: flex;
    align-items: center;
    color: rgba(255, 255, 255, 0.8);
    transition: all 0.2s;
  }

  .back-btn:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.1);
  }

  .title-section .page-title {
    display: flex;
    align-items: center;
    margin: 0 0 8px 0;
    font-size: 28px;
    font-weight: 600;
    color: white;
  }

  .title-icon {
    margin-right: 12px;
    color: #ffffff;
  }

  .page-description {
    margin: 0;
    color: rgba(255, 255, 255, 0.85);
    font-size: 14px;
    line-height: 1.5;
  }



  .filter-section {
    margin-bottom: 24px;
  }

  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .list-actions {
    display: flex;
    align-items: center;
  }

  .projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

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
  }

  .empty-state {
    text-align: center;
    padding: 60px 20px;
  }

  .empty-icon {
    margin-bottom: 16px;
  }

  .empty-actions {
    margin: 24px 0;
  }

  .empty-tips {
    text-align: left;
    max-width: 500px;
    margin: 0 auto;
    color: #666;
    font-size: 14px;
  }

  .empty-tips p {
    margin-bottom: 8px;
    font-weight: 500;
  }

  .empty-tips ul {
    margin: 0;
    padding-left: 20px;
  }

  .empty-tips li {
    margin-bottom: 4px;
    line-height: 1.5;
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 24px;
  }

  /* 暗黑模式适配 */
  [data-theme='dark'] .environment-sounds-page {
    background: #141414 !important;
    min-height: 100vh;
  }

  [data-theme='dark'] .page-header {
    background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
  }

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

  [data-theme='dark'] .param {
    background: #2d2d2d !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .project-stats {
    border-top-color: #434343 !important;
  }

  /* 智能分析相关样式已移除 - 已统一使用新增项目抽屉 */

  /* 智能分析抽屉相关样式已移除 - 已统一使用新增项目抽屉 */

  /* 新增项目抽屉样式 */
  .create-project-form {
    padding: 0;
  }

  .drawer-footer {
    position: absolute;
    bottom: 0;
    width: 100%;
    border-top: 1px solid #e8e8e8;
    padding: 16px 24px;
    background: #fff;
    text-align: right;
  }

  .create-project-form .ant-form {
    padding-bottom: 80px;
  }



  /* 响应式设计 */
  @media (max-width: 768px) {
    .environment-sounds-page {
      padding: 16px;
    }

    .header-content {
      flex-direction: column;
      gap: 16px;
    }

    .projects-grid {
      grid-template-columns: 1fr;
    }

    .filter-section :deep(.ant-form-inline) {
      display: block;
    }

    .filter-section :deep(.ant-form-item) {
      margin-bottom: 16px;
    }

  }
</style>
