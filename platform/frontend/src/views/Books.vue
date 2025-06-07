<template>
  <div class="books-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>📚 书籍管理</h1>
        <p>管理您的小说、图书内容，为语音合成项目提供文本素材</p>
      </div>
      <div class="header-actions">
        <a-button type="primary" @click="$router.push('/books/create')">
          <template #icon>
            <PlusOutlined />
          </template>
          新建书籍
        </a-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <a-row :gutter="16" align="middle">
        <a-col :span="8">
          <a-input-search
            v-model:value="searchParams.search"
            placeholder="搜索书籍标题、作者..."
            @search="loadBooks"
            @pressEnter="loadBooks"
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="searchParams.status"
            placeholder="状态筛选"
            allowClear
            @change="loadBooks"
          >
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="archived">已归档</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-input
            v-model:value="searchParams.author"
            placeholder="作者筛选"
            @pressEnter="loadBooks"
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="searchParams.sort_by"
            @change="loadBooks"
          >
            <a-select-option value="updated_at">更新时间</a-select-option>
            <a-select-option value="created_at">创建时间</a-select-option>
            <a-select-option value="title">标题</a-select-option>
            <a-select-option value="word_count">字数</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="searchParams.sort_order"
            @change="loadBooks"
          >
            <a-select-option value="desc">降序</a-select-option>
            <a-select-option value="asc">升序</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </div>

    <!-- 书籍列表 -->
    <div class="books-list">
      <a-spin :spinning="loading">
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
                        <FileTextOutlined /> {{ book.wordCount.toLocaleString() }} 字
                      </span>
                      <span class="stat-item">
                        <BookOutlined /> {{ book.chapterCount }} 章节
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

        <!-- 空状态 -->
        <div v-if="!loading && books.length === 0" class="empty-state">
          <a-empty
            description="暂无书籍内容"
          >
            <a-button type="primary" @click="$router.push('/books/create')">
              立即创建
            </a-button>
          </a-empty>
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
  BookOutlined
} from '@ant-design/icons-vue'
import { booksAPI } from '@/api'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const books = ref([])

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
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-content h1 {
  margin: 0;
  color: #1f2937;
  font-size: 24px;
}

.header-content p {
  margin: 8px 0 0 0;
  color: #6b7280;
}

.search-section {
  margin-bottom: 24px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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
  padding: 48px 0;
}

.pagination-section {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
</style> 