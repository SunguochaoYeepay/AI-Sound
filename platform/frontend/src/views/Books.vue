<template>
  <PageContainer
    title="书籍列表"
    title-icon="BookOutlined"
    :data="books"
    :loading="loading"
    loading-tip="加载书籍中..."
    
    :search-value="searchParams.search"
    search-placeholder="搜索书籍标题、作者..."
    :filters="searchFilters"
    :actions="headerActions"
    :table-columns="tableColumns"
    :show-pagination="true"
    :pagination="pagination"
    empty-title="暂无书籍"
    empty-description="创建您的第一本书籍"
    :empty-action="{ text: '立即创建', action: 'create' }"
    @search="handleSearch"
    @filter-change="handleFilterChange"
    @refresh="loadBooks"
    @action="handleAction"
    
    @item-click="viewBookDetail"
    @edit="editBook"
    @view="viewBookDetail"
    @delete="deleteBook"
    @empty-action="handleEmptyAction"
    @page-change="handlePageChange"
  >


    <!-- 自定义表格视图 -->
    <template #table-title="{ record }">
      <div style="display: flex; align-items: center; gap: 12px">
        <div class="table-avatar">
          {{ record.title ? record.title.charAt(0) : '书' }}
        </div>
        <div>
          <div style="font-weight: 500">{{ record.title }}</div>
          <div style="font-size: 12px; color: #6b7280">{{ record.description || '暂无描述' }}</div>
        </div>
      </div>
    </template>

    <template #table-author="{ record }">
      <div>
        <UserOutlined style="margin-right: 8px" />
        {{ record.author || '未知作者' }}
      </div>
    </template>

    <template #table-stats="{ record }">
      <div>
        <div>{{ (record.wordCount || 0).toLocaleString() }} 字</div>
        <div>{{ record.chapterCount || 0 }} 章节</div>
      </div>
    </template>

    <template #table-status="{ record }">
      <a-tag :color="getStatusColor(record.status)">
        {{ getStatusText(record.status) }}
      </a-tag>
    </template>

    <template #table-createdAt="{ record }">
      {{ formatDate(record.createdAt) }}
    </template>

    <template #table-actions="{ record }">
      <TableActions
        :record="record"
        :show-synthesis="true"
        @edit="editBook"
        @view="viewBookDetail"
        @synthesis="createSynthesisProject"
        @delete="deleteBook"
      />
    </template>
  </PageContainer>

  <!-- 删除确认弹窗 -->
  <DeleteConfirmModal
    v-model:visible="deleteModal.visible"
    :book="deleteModal.book"
    :force="deleteModal.force"
    @confirm="confirmDelete"
    @cancel="deleteModal.visible = false"
    @update:force="deleteModal.force = $event"
  />
</template>

<script setup>
  import { ref, reactive, onMounted, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import { message } from 'ant-design-vue'
  import { UserOutlined } from '@ant-design/icons-vue'
  import { booksAPI } from '@/api'
  import { useErrorHandler } from '@/composables/useErrorHandler'
  import { getStatusColor, getStatusText, formatDate } from '@/utils/formatters'
  import {
    BOOK_TABLE_COLUMNS,
    BOOK_SEARCH_FILTERS,
    BOOK_HEADER_ACTIONS,
    BOOK_DEFAULT_SEARCH_PARAMS
  } from '@/config/bookConfig'
  import PageContainer from '@/components/common/PageContainer.vue'
  import DeleteConfirmModal from '@/components/common/DeleteConfirmModal.vue'
  import TableActions from '@/components/common/TableActions.vue'

  const router = useRouter()
  const { handleApiError } = useErrorHandler()

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
    ...BOOK_DEFAULT_SEARCH_PARAMS
  })

  const deleteModal = reactive({
    visible: false,
    book: null,
    force: false
  })

  // 搜索筛选器配置
  const searchFilters = computed(() => BOOK_SEARCH_FILTERS)

  // 头部操作按钮配置
  const headerActions = computed(() => BOOK_HEADER_ACTIONS)

  // 表格列定义
  const tableColumns = BOOK_TABLE_COLUMNS

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
      handleApiError(error, '加载书籍列表')
    } finally {
      loading.value = false
    }
  }

  const viewBookDetail = (book) => {
    const bookId = typeof book === 'object' ? book.id : book
    router.push(`/books/detail/${bookId}`)
  }

  const editBook = (book) => {
    const bookId = typeof book === 'object' ? book.id : book
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
      handleApiError(error, '删除书籍')
    }
  }

  const createSynthesisProject = (book) => {
    // 跳转到项目创建页面，预填书籍信息
    router.push({
      path: '/novel-reader/create',
      query: { bookId: book.id }
    })
  }



  // 新的事件处理方法
  const handleSearch = (value) => {
    searchParams.search = value
    loadBooks()
  }

  const handleFilterChange = (filters) => {
    Object.assign(searchParams, filters)
    loadBooks()
  }

  const handleAction = (action) => {
    if (action.action === 'create') {
      router.push('/books/create')
    }
  }



  const handleEmptyAction = () => {
    router.push('/books/create')
  }

  const handlePageChange = ({ page, pageSize }) => {
    pagination.page = page
    pagination.pageSize = pageSize
    loadBooks()
  }

  // 生命周期
  onMounted(() => {
    loadBooks()
  })
</script>

<style scoped>
/* 表格头像样式 */
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
</style>
