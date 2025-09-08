<template>
  <div class="book-analysis-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>书籍分析管理</h2>
        <p class="header-desc">管理和监控AI驱动的6卡片分析项目</p>
      </div>
      <div class="header-right">
        <a-button type="primary" @click="showCreateModal" :loading="loading">
          <template #icon>
            <PlusOutlined />
          </template>
          创建新项目
        </a-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总分析项目"
              :value="sessionCount"
              :value-style="{ color: '#1890ff' }"
            />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="已完成"
              :value="completedSessions.length"
              :value-style="{ color: '#52c41a' }"
            />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="进行中"
              :value="pendingSessions.length"
              :value-style="{ color: '#fa8c16' }"
            />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="失败"
              :value="failedSessions.length"
              :value-style="{ color: '#f5222d' }"
            />
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <a-card>
        <a-row :gutter="16" align="middle">
          <a-col :span="6">
            <a-select
              v-model:value="filters.status"
              placeholder="选择状态"
              allow-clear
              style="width: 100%"
            >
              <a-select-option value="pending">等待处理</a-select-option>
              <a-select-option value="processing">处理中</a-select-option>
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="paused">已暂停</a-select-option>
              <a-select-option value="failed">处理失败</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="8">
            <a-input-search
              v-model:value="filters.search"
              placeholder="搜索书籍名称或项目ID"
              @search="handleSearch"
              style="width: 100%"
            />
          </a-col>
          <a-col :span="4">
            <a-button @click="resetFilters">重置筛选</a-button>
          </a-col>
          <a-col :span="6">
            <a-button type="primary" @click="loadSessions">刷新</a-button>
          </a-col>
        </a-row>
      </a-card>
    </div>

    <!-- 分析项目列表 -->
    <div class="sessions-table">
      <a-card>
        <a-table
          :columns="columns"
          :data-source="filteredSessions"
          :loading="loading"
          :pagination="pagination"
          @change="handleTableChange"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'progress'">
              <a-progress
                :percent="record.progress || 0"
                :status="getProgressStatus(record.status)"
                size="small"
              />
            </template>
            <template v-else-if="column.key === 'book_info'">
              <div class="book-info">
                <div class="book-title">{{ record.book?.title || '未知书籍' }}</div>
                <div class="book-author">{{ record.book?.author || '未知作者' }}</div>
              </div>
            </template>
            <template v-else-if="column.key === 'description'">
              <div class="project-description">
                {{ record.description || '-' }}
              </div>
            </template>
            <template v-else-if="column.key === 'created_at'">
              {{ formatDate(record.created_at) }}
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space>
                <a-button
                  size="small"
                  type="primary"
                  @click="viewDetail(record.id)"
                >
                  查看详情
                </a-button>
                <a-popconfirm
                  title="确定要删除这个分析项目吗？"
                  @confirm="deleteProject(record.id)"
                >
                  <a-button size="small" danger>删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- 创建分析模态框 -->
    <a-modal
      v-model:open="createModalVisible"
      title="创建新分析项目"
      @ok="handleCreateSession"
      @cancel="createModalVisible = false"
      :confirm-loading="creating"
    >
      <a-form :model="createForm" layout="vertical">
        <a-form-item label="选择书籍" required>
          <a-select
            v-model:value="createForm.bookId"
            placeholder="请选择要分析的书籍"
            :loading="booksLoading"
            :options="booksOptions"
            show-search
            filter-option
          />
        </a-form-item>
        <a-form-item label="项目名称" required>
          <a-input
            v-model:value="createForm.projectName"
            placeholder="请输入项目名称"
          />
        </a-form-item>
        <a-form-item label="项目描述">
          <a-textarea
            v-model:value="createForm.description"
            placeholder="请输入项目描述（可选）"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useStoryboardStore } from '@/stores/storyboard'
import { STATUS_CONFIG } from '@/api/storyboard'
import booksAPI from '@/api/books'
import projectsAPI from '@/api/projects'

const router = useRouter()
const storyboardStore = useStoryboardStore()

// 响应式数据
const loading = ref(false)
const creating = ref(false)
const booksLoading = ref(false)
const createModalVisible = ref(false)
const booksOptions = ref([])
const projects = ref([])

const filters = ref({
  status: undefined,
  search: ''
})

const createForm = ref({
  bookId: undefined,
  projectName: '',
  description: ''
})

const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

// 表格列定义
const columns = [
  {
    title: '项目ID',
    dataIndex: 'id',
    key: 'id',
    width: 80
  },
  {
    title: '项目名称',
    dataIndex: 'name',
    key: 'name',
    width: 200
  },
  {
    title: '书籍信息',
    key: 'book_info',
    width: 200
  },
  {
    title: '状态',
    key: 'status',
    width: 120
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    width: 200
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 150
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right'
  }
]

// 计算属性 - 确保数据是数组格式
const sessionCount = computed(() => {
  return Array.isArray(projects.value) ? projects.value.length : 0
})

const completedSessions = computed(() => {
  if (!Array.isArray(projects.value)) return []
  return projects.value.filter(p => p.status === 'completed')
})

const pendingSessions = computed(() => {
  if (!Array.isArray(projects.value)) return []
  return projects.value.filter(p => p.status === 'pending' || p.status === 'processing')
})

const failedSessions = computed(() => {
  if (!Array.isArray(projects.value)) return []
  return projects.value.filter(p => p.status === 'failed')
})

const filteredSessions = computed(() => {
  if (!Array.isArray(projects.value)) return []

  let filtered = projects.value

  // 状态筛选
  if (filters.value.status) {
    filtered = filtered.filter(p => p.status === filters.value.status)
  }

  // 搜索筛选
  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    filtered = filtered.filter(p => 
      p.id.toString().includes(search) ||
      p.name?.toLowerCase().includes(search) ||
      p.description?.toLowerCase().includes(search)
    )
  }

  return filtered
})

// 方法
const loadSessions = async () => {
  try {
    loading.value = true
    const response = await projectsAPI.getProjects()
    if (response.data && response.data.data) {
      projects.value = response.data.data
    } else {
      projects.value = []
    }
  } catch (error) {
    message.error('加载项目列表失败')
    console.error('Load projects error:', error)
  } finally {
    loading.value = false
  }
}

const loadBooks = async () => {
  try {
    booksLoading.value = true
    const response = await booksAPI.getBooks({ limit: 100 })
    
    // 根据API返回格式处理数据
    let books = []
    if (response.data && response.data.data && Array.isArray(response.data.data)) {
      books = response.data.data
    } else if (response.data && Array.isArray(response.data)) {
      books = response.data
    } else {
      console.warn('Unexpected books API response format:', response.data)
      books = []
    }
    
    booksOptions.value = books.map(book => ({
      label: `${book.title} - ${book.author}`,
      value: book.id
    }))
  } catch (error) {
    message.error('加载书籍列表失败')
    console.error('Load books error:', error)
  } finally {
    booksLoading.value = false
  }
}

const showCreateModal = () => {
  createModalVisible.value = true
  loadBooks()
}

const handleCreateSession = async () => {
  if (!createForm.value.bookId) {
    message.error('请选择要分析的书籍')
    return
  }

  if (!createForm.value.projectName) {
    message.error('请输入项目名称')
    return
  }

  try {
    creating.value = true
    
    const projectData = {
      book_id: createForm.value.bookId,
      name: createForm.value.projectName,
      description: createForm.value.description || '基于6类卡片方案的AI驱动小说分析项目',
      status: 'pending'
    }
    
    const response = await projectsAPI.createProject(projectData)
    message.success('分析项目创建成功')
    createModalVisible.value = false
    createForm.value.bookId = undefined
    createForm.value.projectName = ''
    createForm.value.description = ''
    
    // 跳转到详情页面
    router.push(`/content-management/book-analysis/${response.data.id}`)
  } catch (error) {
    message.error('创建分析项目失败')
    console.error('Create project error:', error)
  } finally {
    creating.value = false
  }
}

const viewDetail = (sessionId) => {
  router.push(`/content-management/book-analysis/${sessionId}`)
}


const deleteProject = async (projectId) => {
  try {
    await projectsAPI.deleteProject(projectId)
    message.success('项目已删除')
    await loadSessions() // 重新加载列表
  } catch (error) {
    message.error('删除项目失败')
    console.error('Delete project error:', error)
  }
}

const handleSearch = () => {
  pagination.value.current = 1
}

const resetFilters = () => {
  filters.value = {
    status: undefined,
    search: ''
  }
  pagination.value.current = 1
}

const handleTableChange = (pag) => {
  pagination.value.current = pag.current
  pagination.value.pageSize = pag.pageSize
}

const getStatusColor = (status) => {
  const statusColors = {
    'pending': '#fa8c16',
    'processing': '#1890ff',
    'completed': '#52c41a',
    'paused': '#d9d9d9',
    'failed': '#f5222d'
  }
  return statusColors[status] || '#d9d9d9'
}

const getStatusText = (status) => {
  const statusTexts = {
    'pending': '等待处理',
    'processing': '处理中',
    'completed': '已完成',
    'paused': '已暂停',
    'failed': '处理失败'
  }
  return statusTexts[status] || '未知状态'
}

const getProgressStatus = (status) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  if (status === 'processing') return 'active'
  return 'normal'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.book-analysis-list {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #262626;
}

.header-desc {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.stats-cards {
  margin-bottom: 24px;
}

.filter-section {
  margin-bottom: 24px;
}

.sessions-table {
  margin-bottom: 24px;
}

.book-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.book-title {
  font-weight: 500;
  color: #262626;
}

.book-author {
  font-size: 12px;
  color: #666;
}

.project-description {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #666;
  font-size: 12px;
}
</style>
