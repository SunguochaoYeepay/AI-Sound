<template>
  <div class="books-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <BookOutlined class="title-icon" />
            书籍管理
          </h1>
          <p class="page-description">
            管理您的小说、图书内容，为语音合成项目提供文本素材
          </p>
        </div>
        <div class="action-section">
          <a-button 
            type="primary" 
            size="large"
            @click="$router.push('/books/create')"
          >
            <PlusOutlined />
            新建书籍
          </a-button>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <div class="search-controls">
        <div class="search-filters">
          <a-input-search
            v-model:value="searchParams.search"
            placeholder="搜索书籍标题、作者..."
            style="width: 300px;"
            size="large"
            @search="loadBooks"
            @pressEnter="loadBooks"
          />

          <a-select
            v-model:value="searchParams.status"
            placeholder="状态筛选"
            style="width: 120px;"
            size="large"
            allowClear
            @change="loadBooks"
          >
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="archived">已归档</a-select-option>
          </a-select>

          <a-input
            v-model:value="searchParams.author"
            placeholder="作者筛选"
            style="width: 150px;"
            size="large"
            @pressEnter="loadBooks"
          />

          <a-select
            v-model:value="searchParams.sort_by"
            style="width: 120px;"
            size="large"
            @change="loadBooks"
          >
            <a-select-option value="updated_at">更新时间</a-select-option>
            <a-select-option value="created_at">创建时间</a-select-option>
            <a-select-option value="title">标题</a-select-option>
            <a-select-option value="word_count">字数</a-select-option>
          </a-select>

          <a-button @click="loadBooks" :loading="loading" size="large">
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
    </div>

    <!-- 书籍列表内容 -->
    <div class="books-content">
      <a-spin :spinning="loading" tip="加载书籍中...">
        <!-- 空状态 -->
        <div v-if="books.length === 0 && !loading" class="empty-state">
          <div class="empty-content">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="#d1d5db">
              <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
            </svg>
            <h3>暂无书籍</h3>
            <p>创建您的第一本书籍</p>
            <a-button type="primary" @click="$router.push('/books/create')">
              立即创建
            </a-button>
          </div>
        </div>

        <!-- 网格视图 -->
        <div v-else-if="viewMode === 'grid'" class="grid-view">
          <a-row :gutter="[16, 16]">
            <a-col
              v-for="book in books"
              :key="book.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
              :xl="6"
            >
              <a-card
                hoverable
                class="book-card"
                @click="viewBookDetail(book.id)"
              >
                <template #actions>
                  <EditOutlined 
                    key="edit" 
                    @click.stop="editBook(book.id)"
                    title="编辑"
                  />
                  <EyeOutlined 
                    key="view" 
                    @click.stop="viewBookDetail(book.id)"
                    title="查看"
                  />
                  <DeleteOutlined 
                    key="delete" 
                    @click.stop="deleteBook(book)"
                    title="删除"
                  />
                  <SoundOutlined 
                    key="synthesis" 
                    @click.stop="createSynthesisProject(book)"
                    title="创建合成项目"
                  />
                </template>

                <a-card-meta>
                  <template #title>
                    <div class="book-title">
                      {{ book.title }}
                      <a-tag :color="getStatusColor(book.status)" size="small">
                        {{ getStatusText(book.status) }}
                      </a-tag>
                    </div>
                  </template>
                  <template #description>
                    <div class="book-info">
                      <div class="book-author">
                        <UserOutlined /> {{ book.author || '未知作者' }}
                      </div>
                      <div class="book-stats">
                        <span class="stat-item">
                          <FileTextOutlined /> {{ (book.wordCount || 0).toLocaleString() }} 字
                        </span>
                        <span class="stat-item">
                          <BookOutlined /> {{ book.chapterCount || 0 }} 章节
                        </span>
                      </div>
                      <div class="book-description">
                        {{ book.description || '暂无描述' }}
                      </div>
                      <div class="book-tags" v-if="book.tags && book.tags.length > 0">
                        <a-tag
                          v-for="tag in book.tags.slice(0, 3)"
                          :key="tag"
                          size="small"
                        >
                          {{ tag }}
                        </a-tag>
                        <span v-if="book.tags.length > 3" class="more-tags">
                          +{{ book.tags.length - 3 }}
                        </span>
                      </div>
                      <div class="book-dates">
                        <span class="date-item">
                          创建: {{ formatDate(book.createdAt) }}
                        </span>
                        <span class="date-item">
                          更新: {{ formatDate(book.updatedAt) }}
                        </span>
                      </div>
                    </div>
                  </template>
                </a-card-meta>
              </a-card>
            </a-col>
          </a-row>
        </div>

        <!-- 列表视图 -->
        <div v-else class="list-view">
          <a-table
            :columns="tableColumns"
            :data-source="books"
            :pagination="false"
            row-key="id"
            size="large"
            @row="(record) => ({ onClick: () => viewBookDetail(record.id) })"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'title'">
                <div style="display: flex; align-items: center; gap: 12px;">
                  <div class="table-avatar">
                    {{ record.title.charAt(0) }}
                  </div>
                  <div>
                    <div style="font-weight: 500;">{{ record.title }}</div>
                    <div style="font-size: 12px; color: #6b7280;">{{ record.description }}</div>
                  </div>
                </div>
              </template>

              <template v-if="column.key === 'author'">
                <div>
                  <UserOutlined style="margin-right: 8px;" />
                  {{ record.author || '未知作者' }}
                </div>
              </template>

              <template v-if="column.key === 'stats'">
                <div>
                  <div>{{ (record.wordCount || 0).toLocaleString() }} 字</div>
                  <div>{{ record.chapterCount || 0 }} 章节</div>
                </div>
              </template>

              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>

              <template v-if="column.key === 'actions'">
                <div style="display: flex; gap: 8px;">
                  <a-button type="text" size="small" @click.stop="editBook(record.id)">
                    编辑
                  </a-button>
                  <a-button type="text" size="small" @click.stop="viewBookDetail(record.id)">
                    查看
                  </a-button>
                  <a-button type="text" size="small" @click.stop="createSynthesisProject(record)">
                    合成
                  </a-button>
                  <a-button type="text" size="small" danger @click.stop="deleteBook(record)">
                    删除
                  </a-button>
                </div>
              </template>
            </template>
          </a-table>
        </div>
      </a-spin>
    </div>

    <!-- 分页 -->
    <div class="pagination-section" v-if="pagination.total > 0">
      <a-pagination
        v-model:current="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :show-size-changer="true"
        :show-quick-jumper="true"
        :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
        @change="loadBooks"
        @showSizeChange="loadBooks"
      />
    </div>

    <!-- 删除确认弹窗 -->
    <a-modal
      v-model:open="deleteModal.visible"
      title="确认删除"
      @ok="confirmDelete"
      @cancel="deleteModal.visible = false"
    >
      <p>确定要删除书籍 "{{ deleteModal.book?.title }}" 吗？</p>
      <p v-if="deleteModal.book?.synthesisProjects?.length > 0" style="color: red;">
        ⚠️ 该书籍有 {{ deleteModal.book.synthesisProjects.length }} 个关联的合成项目，删除后这些项目也会被删除。
      </p>
      <a-checkbox v-model:checked="deleteModal.force">
        强制删除（包括关联的合成项目）
      </a-checkbox>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  EditOutlined,
  EyeOutlined,
  DeleteOutlined,
  SoundOutlined,
  UserOutlined,
  FileTextOutlined,
  BookOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import { booksAPI } from '@/api'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const books = ref([])
const viewMode = ref('grid')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const searchParams = reactive({
  search: '',
  status: '',
  author: '',
  tags: '',
  sort_by: 'updated_at',
  sort_order: 'desc'
})

const deleteModal = reactive({
  visible: false,
  book: null,
  force: false
})

// 表格列定义
const tableColumns = [
  {
    title: '书籍信息',
    key: 'title',
    width: '30%'
  },
  {
    title: '作者',
    key: 'author',
    width: '15%'
  },
  {
    title: '统计',
    key: 'stats',
    width: '15%'
  },
  {
    title: '状态',
    key: 'status',
    width: '10%'
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    width: '15%',
    customRender: ({ record }) => formatDate(record.createdAt)
  },
  {
    title: '操作',
    key: 'actions',
    width: '15%'
  }
]

// 方法
const loadBooks = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchParams
    }

    const response = await booksAPI.getBooks(params)
    if (response.data.success) {
      books.value = response.data.data
      pagination.total = response.data.pagination.total
    }
  } catch (error) {
    console.error('加载书籍列表失败:', error)
    message.error('加载书籍列表失败')
  } finally {
    loading.value = false
  }
}

const viewBookDetail = (bookId) => {
  router.push(`/books/detail/${bookId}`)
}

const editBook = (bookId) => {
  router.push(`/books/edit/${bookId}`)
}

const deleteBook = (book) => {
  deleteModal.book = book
  deleteModal.visible = true
  deleteModal.force = false
}

const confirmDelete = async () => {
  try {
    await booksAPI.deleteBook(deleteModal.book.id, deleteModal.force)
    message.success('书籍删除成功')
    deleteModal.visible = false
    loadBooks()
  } catch (error) {
    console.error('删除书籍失败:', error)
    const errorMsg = error.response?.data?.detail || '删除失败'
    message.error(errorMsg)
  }
}

const createSynthesisProject = (book) => {
  // 跳转到项目创建页面，预填书籍信息
  router.push({
    path: '/novel-reader/create',
    query: { bookId: book.id }
  })
}

const getStatusColor = (status) => {
  const colors = {
    draft: 'orange',
    published: 'green',
    archived: 'gray'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档'
  }
  return texts[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadBooks()
})
</script>

<style scoped>
.books-container {
  background: #f5f5f5;
  min-height: 100vh;
}

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

.search-section {
  margin-bottom: 24px;
  padding: 16px;

  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.search-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.search-filters {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.view-controls {
  flex-shrink: 0;
}

.books-list {
  margin-bottom: 24px;
}

.book-card {
  height: 100%;
  cursor: pointer;
  transition: all 0.3s ease;
}

.book-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.book-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.book-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.book-author {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #6b7280;
  font-size: 14px;
}

.book-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #6b7280;
  font-size: 12px;
}

.book-description {
  color: #4b5563;
  font-size: 13px;
  line-height: 1.4;
  max-height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.book-tags {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.more-tags {
  color: #6b7280;
  font-size: 12px;
}

.book-dates {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #9ca3af;
}

.empty-state {
  text-align: center;
  padding: 80px 0;
}

.empty-content {
  max-width: 400px;
  margin: 0 auto;
}

.empty-content h3 {
  margin: 16px 0 8px 0;
  color: #374151;
  font-size: 18px;
  font-weight: 500;
}

.empty-content p {
  color: #6b7280;
  margin-bottom: 24px;
}

.table-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--primary-color), #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  font-size: 16px;
}

.pagination-section {
  display: flex;
  justify-content: center;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 暗黑模式适配 */
[data-theme="dark"] .books-container {
  background: #141414 !important;
}

[data-theme="dark"] .search-section,
[data-theme="dark"] .pagination-section {
  background: #1f1f1f !important;
  border: 1px solid #434343 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}

[data-theme="dark"] .book-card {
  background: #1f1f1f !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .book-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5) !important;
}

[data-theme="dark"] .book-title {
  color: #fff !important;
}

[data-theme="dark"] .book-author,
[data-theme="dark"] .stat-item,
[data-theme="dark"] .more-tags {
  color: #8c8c8c !important;
}

[data-theme="dark"] .book-description {
  color: #d1d5db !important;
}

[data-theme="dark"] .book-dates {
  color: #8c8c8c !important;
}

[data-theme="dark"] .page-header {
  background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

/* 卡片操作按钮暗黑模式适配 */
[data-theme="dark"] .book-card :deep(.ant-card-actions) {
  background: #2d2d2d !important;
  border-top-color: #434343 !important;
}

[data-theme="dark"] .book-card :deep(.ant-card-actions > li) {
  border-right-color: #434343 !important;
}

[data-theme="dark"] .book-card :deep(.ant-card-actions .anticon) {
  color: #8c8c8c !important;
}

[data-theme="dark"] .book-card :deep(.ant-card-actions .anticon:hover) {
  color: var(--primary-color) !important;
}

[data-theme="dark"] .book-card :deep(.ant-card-actions > li:hover) {
  background: #3a3a3a !important;
}

/* 空状态暗黑模式适配 */
[data-theme="dark"] .empty-content h3 {
  color: #fff !important;
}

[data-theme="dark"] .empty-content p {
  color: #8c8c8c !important;
}

/* 表格暗黑模式适配 */
[data-theme="dark"] .list-view :deep(.ant-table) {
  background: #1f1f1f !important;
}

[data-theme="dark"] .list-view :deep(.ant-table-thead > tr > th) {
  background: #2d2d2d !important;
  border-bottom-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] .list-view :deep(.ant-table-tbody > tr > td) {
  background: #1f1f1f !important;
  border-bottom-color: #434343 !important;
  color: #d1d5db !important;
}

[data-theme="dark"] .list-view :deep(.ant-table-tbody > tr:hover > td) {
  background: #2d2d2d !important;
}
</style> 