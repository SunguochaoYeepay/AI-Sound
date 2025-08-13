<template>
  <div class="environment-sounds-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-with-back">
            <h1 class="page-title">
              <SoundOutlined class="title-icon" />
              环境音管理
            </h1>
          </div>
          
        </div>
        <div class="action-section">
          <a-space size="large">
            <a-button
              type="primary"
              size="large"
              @click="startNewAnalysis"
            >
              <BulbOutlined />
              新建环境音分析
            </a-button>
          </a-space>
        </div>
      </div>
    </div>



    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <a-card>
        <a-form layout="inline" :model="searchForm">
          <a-form-item label="搜索">
            <a-input
              v-model:value="searchForm.search"
              placeholder="搜索项目名称、章节名称或分析内容"
              style="width: 300px"
              @pressEnter="loadProjects"
            >
              <template #prefix>
                <SearchOutlined />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item label="状态">
            <a-select
              v-model:value="searchForm.status"
              placeholder="项目状态"
              style="width: 120px"
              allowClear
              @change="loadProjects"
            >
              <a-select-option value="analyzed">已分析</a-select-option>
              <a-select-option value="generating">生成中</a-select-option>
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="时间范围">
            <a-range-picker
              v-model:value="searchForm.dateRange"
              style="width: 200px"
              @change="loadProjects"
            />
          </a-form-item>

          <a-form-item>
            <a-button type="primary" @click="loadProjects">
              <SearchOutlined />
              搜索
            </a-button>
          </a-form-item>

          <a-form-item>
            <a-button @click="resetSearch"> 重置 </a-button>
          </a-form-item>

          <a-form-item>
            <a-button @click="loadProjects" :loading="loading">
              <ReloadOutlined />
              刷新
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>

    <!-- 环境音分析项目列表 -->
    <div class="projects-section">
      <a-card>
        <template #title>
          <div class="list-header">
            <span>环境音项目列表</span>
            <div class="list-actions">
              <a-select
                v-model:value="sortBy"
                style="width: 120px; margin-left: 8px"
                @change="loadProjects"
              >
                <a-select-option value="created_at">创建时间</a-select-option>
                <a-select-option value="updated_at">更新时间</a-select-option>
                <a-select-option value="analysis_tracks">轨道数量</a-select-option>
                <a-select-option value="generation_count">生成数量</a-select-option>
              </a-select>
            </div>
          </div>
        </template>

        <div class="projects-grid">
          <div
            v-for="project in projects"
            :key="project.id"
            class="project-card"
            :class="{ 
              'completed': project.status === 'completed',
              'processing': project.status === 'generating',
              'failed': project.status === 'failed'
            }"
            @click="viewProjectDetail(project)"
          >
            <!-- 状态标识 -->
            <div class="status-badge">
              <a-badge
                :status="getProjectStatusType(project.status)"
                :text="getProjectStatusText(project.status)"
              />
            </div>

            <!-- 项目信息 -->
            <div class="project-info">
              <h3 class="project-name">{{ project.name || '未命名项目' }}</h3>
            
              
              <div class="project-meta">
                <div class="meta-item">
                  <BookOutlined />
                  <span>{{ project.book_name || '未知书籍' }}</span>
                </div>
                <div class="meta-item">
                  <FileTextOutlined />
                  <span>{{ project.chapter_name || '未知章节' }}</span>
                </div>
                <div class="meta-item">
                  <ClockCircleOutlined />
                  <span>{{ formatDateTime(project.created_at) }}</span>
                </div>
              </div>
            </div>

            <!-- 统计信息 -->
            <div class="project-stats">
              <div class="stat-item">
                <BulbOutlined />
                <span>{{ project.analysis_tracks || 0 }} 轨道</span>
              </div>
              <div class="stat-item">
                <SoundOutlined />
                <span>{{ project.generation_count || 0 }} 已生成</span>
              </div>
              <div class="stat-item">
                <CheckCircleOutlined />
                <span>{{ project.matched_count || 0 }} 已匹配</span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="project-actions">
              <a-button 
                type="primary" 
                size="small"
                @click.stop="viewProjectDetail(project)"
              >
                查看详情
              </a-button>
              <a-button 
                v-if="project.status === 'analyzed'"
                type="default" 
                size="small"
                @click.stop="startGeneration(project)"
              >
                开始生成
              </a-button>
              <a-button 
                v-if="project.status === 'completed'"
                type="default" 
                size="small"
                @click.stop="viewGeneratedSounds(project)"
              >
                查看音频
              </a-button>
              <a-button 
                type="text" 
                size="small"
                danger
                @click.stop="deleteProject(project)"
              >
                <DeleteOutlined />
                删除
              </a-button>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && projects.length === 0" class="empty-state">
          <a-empty description="暂无环境音分析项目">
            <template #image>
              <div class="empty-icon">
                <SoundOutlined style="font-size: 64px; color: #d9d9d9;" />
              </div>
            </template>
            <div class="empty-actions">
              <a-space>
                <a-button type="primary" @click="showSmartAnalysisModal = true">
                  <BulbOutlined />
                  开始第一个智能分析
                </a-button>
              </a-space>
            </div>
            <div class="empty-tips">
              <p>💡 提示：</p>
              <ul>
                <li>点击"开始第一个智能分析"来基于您的书籍章节创建环境音分析项目</li>
                <li>分析完成后，您可以查看详情并批量生成环境音</li>
              </ul>
            </div>
          </a-empty>
        </div>

        <!-- 分页 -->
        <div v-if="projects.length > 0" class="pagination-wrapper">
          <a-pagination
            v-model:current="pagination.current"
            v-model:pageSize="pagination.pageSize"
            :total="pagination.total"
            :show-size-changer="true"
            :show-quick-jumper="true"
            :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
            @change="handlePageChange"
            @showSizeChange="handlePageSizeChange"
          />
        </div>
      </a-card>
    </div>

    <!-- 智能分析对话框 -->
    <a-drawer
      v-model:open="showSmartAnalysisModal"
      title="智能分析环境音"
      width="800px"
      placement="right"
      :closable="true"
    >
      <!-- 智能分析内容 -->
      <div class="analysis-content">
        <!-- 步骤指示器 -->
        <div class="analysis-steps">
          <a-steps :current="analysisStep" size="small">
            <a-step title="选择章节" />
            <a-step title="智能分析" />
            <a-step title="环境音匹配" />
            <a-step title="生成计划" />
          </a-steps>
        </div>

        <!-- 步骤0: 选择章节 -->
        <div v-if="analysisStep === 0" class="analysis-step">
          <h3>选择要分析的章节</h3>
       

          <!-- 书籍选择 -->
          <a-form layout="vertical">
            <a-form-item label="选择书籍">
              <div style="margin-bottom: 8px; color: #666; font-size: 12px;">
                调试信息: 书籍数量: {{ books.length }}, 当前选中: {{ selectedBook }}
              </div>
              <a-select
                v-model:value="selectedBook"
                placeholder="请选择书籍"
                style="width: 100%"
                @change="onBookChange"
                :loading="loadingChapters"
              >
                <a-select-option
                  v-for="book in books"
                  :key="book.id"
                  :value="book.id"
                >
                  {{ book.title }}
                </a-select-option>
              </a-select>
            </a-form-item>

            <!-- 章节选择 -->
            <a-form-item label="选择章节">
              <div style="margin-bottom: 8px; color: #666; font-size: 12px;">
                调试信息: 选中书籍ID: {{ selectedBook }}, 章节数量: {{ chapters.length }}, 加载状态: {{ loadingChapters }}
              </div>
              <a-select
                v-model:value="selectedChapterIds"
                mode="multiple"
                placeholder="请选择要分析的章节"
                style="width: 100%"
                :loading="loadingChapters"
                :disabled="!selectedBook"
              >
                <a-select-option
                  v-for="chapter in chapters"
                  :key="chapter.id"
                  :value="chapter.id"
                >
                  {{ chapter.chapter_title || chapter.title || `第${chapter.chapter_number}章` }}
                </a-select-option>
              </a-select>
            </a-form-item>

            <!-- 分析选项 -->
            <a-form-item label="分析选项">
              <div>
                <a-checkbox 
                  v-model:checked="analysisOptions.precise_timing"
                  @change="(checked) => analysisOptions.precise_timing = checked"
                >
                  精确时间轴
                </a-checkbox>
              </div>
              <div>
                <a-checkbox 
                  v-model:checked="analysisOptions.intensity_analysis"
                  @change="(checked) => analysisOptions.intensity_analysis = checked"
                >
                  强度分析
                </a-checkbox>
              </div>
              <div>
                <a-checkbox 
                  v-model:checked="analysisOptions.include_emotion"
                  @change="(checked) => analysisOptions.include_emotion = checked"
                >
                  情感分析
                </a-checkbox>
              </div>
            </a-form-item>
          </a-form>

          <div class="step-actions">
            <a-button type="primary" @click="startAnalysis" :disabled="selectedChapterIds.length === 0">
              开始分析
            </a-button>
          </div>
        </div>

        <!-- 步骤1: 智能分析进度 -->
        <div v-if="analysisStep === 1" class="analysis-step">
          <div v-if="analyzing" class="analyzing-progress">
            <div class="progress-header">
              <a-spin size="large">
                <template #indicator>
                  <BulbOutlined style="font-size: 32px" spin />
                </template>
              </a-spin>
              <h2>正在智能分析章节内容...</h2>
              <p>分析旁白内容，提取环境音需求</p>
            </div>
            <a-progress :percent="analysisProgress" status="active" />
          </div>

          <!-- 分析结果 -->
          <div v-if="analysisResult && !analyzing" class="analysis-result">
            <h3>🎯 分析结果</h3>
            <div class="result-summary">
              <a-row :gutter="16">
                <a-col :span="6">
                  <div class="summary-item">
                    <div class="summary-number">{{ analysisResult.analysis_metadata?.track_count || analysisResult.total_tracks || 0 }}</div>
                    <div class="summary-label">检测到轨道</div>
                  </div>
                </a-col>
                <a-col :span="6">
                  <div class="summary-item">
                    <div class="summary-number">{{ analysisResult.analysis_metadata?.total_duration || analysisResult.total_duration || 0 }}s</div>
                    <div class="summary-label">总时长</div>
                  </div>
                </a-col>
                <a-col :span="6">
                  <div class="summary-item">
                    <div class="summary-number">{{ analysisResult.environment_tracks?.length || analysisResult.unique_keywords || 0 }}</div>
                    <div class="summary-label">环境轨道</div>
                  </div>
                </a-col>
                <a-col :span="6">
                  <div class="summary-item">
                    <div class="summary-number">{{ analysisResult.analysis_metadata?.analyzer_version || analysisResult.confidence || '2.0' }}</div>
                    <div class="summary-label">分析版本</div>
                  </div>
                </a-col>
              </a-row>
            </div>

            <div class="step-actions" style="margin-top: 16px">
              <a-space>
                <a-button @click="analysisStep = 0">重新选择</a-button>
                <a-button type="primary" @click="proceedToGeneration">
                  进入生成计划
                </a-button>
              </a-space>
            </div>
          </div>
        </div>

        <!-- 步骤3: 生成计划 -->
        <div v-if="analysisStep === 3" class="analysis-step">
          <h3>📋 生成计划确认</h3>
          <p class="step-description">
            确认环境音生成计划，系统将根据计划批量生成环境音
          </p>

          <div class="generation-plan">
            <a-alert
              message="生成计划"
              description="请确认以下生成计划，生成后将无法撤销"
              type="info"
              show-icon
              style="margin-bottom: 16px"
            />

            <div class="plan-summary">
              <a-descriptions :column="2" size="small">
                <a-descriptions-item label="需生成数量">
                  {{ analysisResult.environment_tracks?.length || 0 }} 个
                </a-descriptions-item>
                <a-descriptions-item label="预估时间">
                  {{ Math.ceil((analysisResult.environment_tracks?.length || 0) * 2) }} 分钟
                </a-descriptions-item>
                <a-descriptions-item label="分析版本">
                  {{ analysisResult.analysis_metadata?.analyzer_version || '2.0' }}
                </a-descriptions-item>
                <a-descriptions-item label="总时长">
                  {{ analysisResult.analysis_metadata?.total_duration || analysisResult.total_duration || 0 }} 秒
                </a-descriptions-item>
              </a-descriptions>
            </div>

            <div class="step-actions" style="margin-top: 16px">
              <a-space>
                <a-button @click="analysisStep = 1">返回分析</a-button>
                <a-button type="primary" @click="confirmGeneration">
                  确认并创建项目
                </a-button>
              </a-space>
            </div>
          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 新增项目抽屉 -->
    <a-drawer
      v-model:open="showCreateProjectDrawer"
      title="新建环境音分析项目"
      placement="right"
      width="600px"
      @close="handleCloseCreateDrawer"
    >
      <div class="create-project-form">
        <a-form :model="newProjectForm" layout="vertical">
          <!-- 项目基本信息 -->
          <a-form-item label="项目名称" required>
            <a-input
              v-model:value="newProjectForm.name"
              placeholder="请输入项目名称"
              :maxlength="100"
              show-count
            />
          </a-form-item>

          <a-form-item label="项目描述">
            <a-textarea
              v-model:value="newProjectForm.description"
              placeholder="请输入项目描述"
              :rows="3"
              :maxlength="500"
              show-count
            />
          </a-form-item>

          <!-- 书籍选择 -->
          <a-form-item label="选择书籍" required>
            <a-select
              v-model:value="newProjectForm.book_id"
              placeholder="请选择书籍"
              :loading="booksLoading"
            >
              <a-select-option
                v-for="book in books"
                :key="book.id"
                :value="book.id"
              >
                {{ book.title }} ({{ book.chapter_count || 0 }}章)
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-form>

        <!-- 操作按钮 -->
        <div class="drawer-footer">
          <a-space>
            <a-button @click="handleCloseCreateDrawer">取消</a-button>
            <a-button
              type="primary"
              :loading="creatingProject"
              @click="handleCreateProject"
            >
              创建项目
            </a-button>
          </a-space>
        </div>
      </div>
    </a-drawer>

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
      SoundOutlined,
      SearchOutlined,
      CheckCircleOutlined,
      BulbOutlined,
      ReloadOutlined,
      BookOutlined,
      FileTextOutlined,
      ClockCircleOutlined,
      DeleteOutlined
    } from '@ant-design/icons-vue'

    import EditModal from '@/components/environment-sounds/EditModal.vue'
        import { booksAPI, chaptersAPI, environmentGenerationAPI } from '@/api'

    // 路由
    const router = useRouter()

    // 响应式数据
    const loading = ref(false)

  // 项目相关数据
  const projects = ref([])

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
  const creatingProject = ref(false)
  const newProjectForm = reactive({
    name: '',
    description: '',
    book_id: null
  })

  // 智能分析相关
  const showSmartAnalysisModal = ref(false)
  const analyzing = ref(false)
  const analysisStep = ref(0)
  const analysisProgress = ref(0)
  const analysisResult = ref(null)

  // 新的4步优化流程相关
  const selectedChapterIds = ref([])
  const analysisOptions = ref({
    precise_timing: true,
    intensity_analysis: true,
    include_emotion: false
  })

  // 书籍和章节数据
  const books = ref([])
  const chapters = ref([])
  const loadingChapters = ref(false)
  const booksLoading = ref(false)
  const selectedBook = ref(null)



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
        loadStats(),
        loadBooks()
      ])
      console.log('✅ 初始数据加载完成')
    } catch (error) {
      console.error('❌ 初始数据加载失败:', error)
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

  const loadBooks = async () => {
    try {
      console.log('📚 开始加载书籍列表')
      const response = await booksAPI.getBooks()
      console.log('📚 书籍API响应:', response.data)
      console.log('📚 响应结构:', {
        success: response.data.success,
        hasData: !!response.data.data,
        dataType: typeof response.data.data,
        dataLength: response.data.data ? response.data.data.length : 'N/A'
      })
      
      if (response.data.success && response.data.data) {
        books.value = response.data.data
        console.log('✅ 书籍加载成功，数量:', books.value.length)
        console.log('📖 书籍数据示例:', books.value.slice(0, 2))
        console.log('📖 当前books.value:', books.value)
      } else {
        books.value = []
        console.log('❌ 书籍数据为空或格式错误')
        console.log('❌ 响应详情:', {
          success: response.data.success,
          data: response.data.data,
          message: response.data.message
        })
      }
    } catch (error) {
      console.error('加载书籍失败:', error)
      books.value = []
    }
  }

  const onBookChange = async (bookId) => {
    if (!bookId) {
      chapters.value = []
      return
    }

    try {
      loadingChapters.value = true
      console.log('🔍 开始加载章节，书籍ID:', bookId)
      const response = await chaptersAPI.getChapters({ book_id: bookId })
      console.log('📋 章节API响应:', response.data)
      
      if (response.data.success && response.data.data) {
        chapters.value = response.data.data
        console.log('✅ 章节加载成功，数量:', chapters.value.length)
        console.log('📖 章节数据示例:', chapters.value.slice(0, 2))
      } else {
        chapters.value = []
        console.log('❌ 章节数据为空或格式错误')
      }
    } catch (error) {
      console.error('加载章节失败:', error)
      message.error('加载章节失败')
      chapters.value = []
    } finally {
      loadingChapters.value = false
    }
  }

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

  const getProjectStatusType = (status) => {
    const statusMap = {
      'analyzed': 'processing',
      'generating': 'processing',
      'completed': 'success',
      'failed': 'error'
    }
    return statusMap[status] || 'default'
  }

  const getProjectStatusText = (status) => {
    const statusMap = {
      'analyzed': '已分析',
      'generating': '生成中',
      'completed': '已完成',
      'failed': '失败'
    }
    return statusMap[status] || '未知'
  }

  const formatDateTime = (timestamp) => {
    if (!timestamp) return '未知时间'
    const date = new Date(timestamp)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
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

  const startGeneration = async (project) => {
    try {
      await environmentGenerationAPI.startGeneration(project.id)
      message.success('开始生成环境音')
      loadProjects() // 刷新项目列表
    } catch (error) {
      console.error('开始生成失败:', error)
      message.error('开始生成失败: ' + (error.response?.data?.detail || error.message))
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

  // 智能分析相关方法
  const startAnalysis = async () => {
    if (selectedChapterIds.value.length === 0) {
      message.error('请选择要分析的章节')
      return
    }

    return startNewAnalysisFlow()
  }

  const startNewAnalysisFlow = async () => {
    analyzing.value = true
    analysisStep.value = 1
    analysisProgress.value = 0

    try {
      const progressInterval = setInterval(() => {
        if (analysisProgress.value < 90) {
          analysisProgress.value += Math.random() * 10
        }
      }, 500)

      const response = await environmentGenerationAPI.analyzeChaptersEnvironment(
        selectedChapterIds.value,
        analysisOptions.value
      )

      clearInterval(progressInterval)
      analysisProgress.value = 100

      // 修复：适配后端返回的数据结构
      if (response.data.success && response.data.analysis_result) {
        analysisResult.value = response.data.analysis_result
      } else if (response.data.enhanced_analysis_result) {
        analysisResult.value = response.data.enhanced_analysis_result
      } else if (response.data.chapters) {
        analysisResult.value = response.data
      } else {
        analysisResult.value = response.data
      }

      message.success('章节环境音分析完成！')

      // 简化流程：分析完成后直接进入生成计划
      analysisStep.value = 3
    } catch (error) {
      console.error('章节分析失败:', error)
      message.error('章节分析失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      analyzing.value = false
    }
  }

  const proceedToGeneration = () => {
    analysisStep.value = 3
  }

  const confirmGeneration = async () => {
    try {
      // 创建环境音分析项目
      const projectData = {
        name: `环境音分析_${new Date().toLocaleString()}`,
        description: `基于${selectedChapterIds.value.length}个章节的智能环境音分析`,
        analysis_result: analysisResult.value,
        matching_result: null, // 简化流程，不再需要匹配结果
        chapter_ids: selectedChapterIds.value,
        analysis_options: analysisOptions.value
      }

      const response = await environmentGenerationAPI.createProject(projectData)
      
      if (response.data.success) {
        const projectId = response.data.data.id
        message.success('环境音分析项目创建成功！正在跳转到项目详情...')
        showSmartAnalysisModal.value = false
        
        // 重置状态
        analysisStep.value = 0
        analysisResult.value = null
        // matchingResult.value = null // Removed as per edit hint
        selectedChapterIds.value = []
        
        // 跳转到项目详情页面
        router.push(`/environment-sounds/analysis/${projectId}`)
        
        // 刷新项目列表
        loadProjects()
        loadStats()
      } else {
        message.error('创建项目失败')
      }
    } catch (error) {
      console.error('创建项目失败:', error)
      message.error('创建项目失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleEditSuccess = () => {
    loadProjects()
    loadStats()
  }

  const startNewAnalysis = () => {
    // 直接显示新增项目抽屉，不需要验证章节选择
    showCreateProjectDrawer.value = true
  }

  const handleCloseCreateDrawer = () => {
    showCreateProjectDrawer.value = false
    newProjectForm.name = ''
    newProjectForm.description = ''
    newProjectForm.book_id = null
  }

  const handleCreateProject = async () => {
    if (!newProjectForm.name) {
      message.error('项目名称不能为空')
      return
    }
    if (!newProjectForm.book_id) {
      message.error('请选择书籍')
      return
    }

    creatingProject.value = true
    try {
      const projectData = {
        name: newProjectForm.name,
        description: newProjectForm.description,
        book_id: newProjectForm.book_id,
        chapter_ids: [], // 默认为空数组
        analysis_options: {
          mode: 'auto', // 默认智能分析
          environment_types: ['nature', 'urban', 'indoor', 'action'], // 默认包含所有类型
          precision: 'medium' // 默认中等精度
        }
      }

      const response = await environmentGenerationAPI.createProject(projectData)

      if (response.data.success) {
        const projectId = response.data.data.id
        message.success('环境音分析项目创建成功！正在跳转到项目详情...')
        showCreateProjectDrawer.value = false
        
        // 重置状态
        newProjectForm.name = ''
        newProjectForm.description = ''
        newProjectForm.book_id = null

        // 跳转到项目详情页面
        router.push(`/environment-sounds/analysis/${projectId}`)
        
        // 刷新项目列表
        loadProjects()
        loadStats()
      } else {
        message.error('创建项目失败: ' + (response.data.detail || response.data.message))
      }
    } catch (error) {
      console.error('创建项目失败:', error)
      message.error('创建项目失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      creatingProject.value = false
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

  /* 智能分析抽屉样式 */
  .smart-analysis-drawer :deep(.ant-drawer-body) {
    padding: 24px;
    height: 100%;
    overflow-y: auto;
  }

  .smart-analysis-content {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .analysis-steps {
    margin-bottom: 24px;
    padding: 16px;
    background: #fafafa;
    border-radius: 8px;
    flex-shrink: 0;
  }

  /* 智能分析抽屉暗黑模式适配 */
  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-drawer-header) {
    background-color: #1f1f1f !important;
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-drawer-title) {
    color: #fff !important;
  }

  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-drawer-body) {
    background-color: #1f1f1f !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-drawer-close) {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-drawer-close:hover) {
    color: #fff !important;
  }

  [data-theme='dark'] .analysis-steps {
    background: #2d2d2d !important;
    border: 1px solid #434343 !important;
  }

  [data-theme='dark'] .analysis-step h3 {
    color: #fff !important;
  }

  [data-theme='dark'] .analyzing-progress h2,
  [data-theme='dark'] .generating-state h3 {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .analyzing-progress p,
  [data-theme='dark'] .generating-state p {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .scene-item {
    background: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .scene-header h4 {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .prompt-item {
    background: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .prompt-header h4 {
    color: #fff !important;
  }

  [data-theme='dark'] .prompt-content code {
    background: #1f1f1f !important;
    color: #d1d5db !important;
    border: 1px solid #434343 !important;
  }

  [data-theme='dark'] .prompt-features {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .prompt-settings {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .logs-container {
    background: #1f1f1f !important;
    border: 1px solid #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .log-time {
    color: #8c8c8c !important;
  }

  /* 智能分析抽屉内的卡片适配 */
  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-card) {
    background: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-card-head) {
    background: #2d2d2d !important;
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-card-head-title) {
    color: #fff !important;
  }

  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-card-body) {
    background: #2d2d2d !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-descriptions-item-label) {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .smart-analysis-drawer :deep(.ant-descriptions-item-content) {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .smart-analysis-drawer .narrative_analysis span {
    color: #8c8c8c !important;
  }

  .analysis-step {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .analyzing-progress,
  .generating-state {
    text-align: center;
    padding: 40px 20px;
  }

  .analyzing-progress h2,
  .generating-state h3 {
    color: #1890ff;
    margin-bottom: 8px;
  }

  .progress-header {
    margin-bottom: 32px;
  }

  .progress-header h2 {
    margin: 16px 0 8px 0;
    color: #1890ff;
  }

  .scenes-list,
  .tracks-list {
    space-y: 16px;
  }

  .scene-item,
  .track-item {
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    background: #fafafa;
  }

  .scene-header,
  .track-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .scene-header h4,
  .track-header h4 {
    margin: 0;
    color: #1890ff;
  }

  .scene-details,
  .track-details {
    margin-bottom: 8px;
  }

  .scene-keywords,
  .track-keywords {
    margin-top: 8px;
  }

  .prompts-list {
    space-y: 20px;
  }

  .prompt-item {
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
    background: #fff;
  }

  .prompt-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .prompt-header h4 {
    margin: 0;
    color: #2c3e50;
    font-size: 16px;
  }

  .prompt-content {
    margin-bottom: 12px;
  }

  .prompt-content code {
    background: #f6f8fa;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 13px;
    line-height: 1.6;
    display: block;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .prompt-features {
    margin-bottom: 8px;
    color: #666;
  }

  .prompt-settings {
    font-size: 12px;
    color: #888;
  }

  .step-actions {
    margin-top: 24px;
    text-align: center;
  }

  .generation-progress {
    text-align: center;
  }

  .generation-logs {
    max-height: 200px;
    overflow-y: auto;
  }

  .logs-container {
    background: #f8f9fa;
    border-radius: 4px;
    padding: 12px;
    font-family: monospace;
    font-size: 12px;
  }

  .log-item {
    display: flex;
    margin-bottom: 4px;
    line-height: 1.4;
  }

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

  .log-time {
    color: #666;
    margin-right: 8px;
    min-width: 80px;
  }

  .log-message {
    flex: 1;
  }

  .log-item.success .log-message {
    color: #52c41a;
  }

  .log-item.error .log-message {
    color: #ff4d4f;
  }

  .log-item.warning .log-message {
    color: #fa8c16;
  }

  .log-item.info .log-message {
    color: #1890ff;
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

    /* 移动端抽屉全屏显示 */
    .smart-analysis-drawer :deep(.ant-drawer) {
      width: 100vw !important;
    }

    .smart-analysis-drawer :deep(.ant-drawer-body) {
      padding: 16px;
    }

    .prompt-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .step-actions {
      margin-top: 16px;
    }

    .step-actions :deep(.ant-space) {
      width: 100%;
      justify-content: center;
    }

    .analysis-steps {
      margin-bottom: 16px;
      padding: 12px;
    }

    .analysis-steps :deep(.ant-steps) {
      font-size: 12px;
    }
  }

  .track-item {
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
    background: #fafafa;
  }

  .track-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .track-header h4,
  .track-header h5 {
    margin: 0;
    color: #333;
  }

  .track-details {
    margin-bottom: 8px;
  }

  .track-keywords {
    margin-top: 8px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
  }

  .chapter-tracks {
    margin-bottom: 24px;
  }

  .chapter-tracks h4 {
    color: #1890ff;
    margin-bottom: 16px;
    font-weight: 600;
  }

  .total-stats {
    background: #f6f8fa;
    padding: 16px;
    border-radius: 8px;
    text-align: center;
  }

  .track-match-info {
    margin-top: 8px;
  }

  .track-match-info .ant-alert {
    border-radius: 4px;
  }
</style>
