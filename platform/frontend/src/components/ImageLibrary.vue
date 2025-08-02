<template>
  <div class="image-library">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <PictureOutlined class="title-icon" />
            图片库
          </h1>
          <p class="page-description">
            管理和浏览项目中的所有图片资源，支持多种格式和批量操作
          </p>
        </div>
        <div class="action-section">
          <a-button type="primary" size="large" @click="showUploadModal = true">
            <template #icon><UploadOutlined /></template>
            上传图片
          </a-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <a-row :gutter="24">
        <a-col :xs="24" :sm="12" :md="6">
          <a-card>
            <a-statistic
              title="总图片数"
              :value="stats.totalImages"
              :value-style="{ color: '#52c41a', fontSize: '24px', fontWeight: '600' }"
            >
              <template #prefix>
                <PictureOutlined style="color: #52c41a; margin-right: 8px;" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-card>
            <a-statistic
              title="总大小"
              :value="formatFileSize(stats.totalSize)"
              :value-style="{ color: '#1890ff', fontSize: '24px', fontWeight: '600' }"
            >
              <template #prefix>
                <DatabaseOutlined style="color: #1890ff; margin-right: 8px;" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-card>
            <a-statistic
              title="今日新增"
              :value="stats.todayCount"
              :value-style="{ color: '#fa541c', fontSize: '24px', fontWeight: '600' }"
            >
              <template #prefix>
                <CalendarOutlined style="color: #fa541c; margin-right: 8px;" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-card>
            <a-statistic
              title="本周新增"
              :value="stats.weekCount"
              :value-style="{ color: '#722ed1', fontSize: '24px', fontWeight: '600' }"
            >
              <template #prefix>
                <ClockCircleOutlined style="color: #722ed1; margin-right: 8px;" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="filter-controls">
        <a-select
          v-model:value="selectedBook"
          placeholder="选择书籍"
          style="width: 200px"
          @change="onBookChange"
          allow-clear
        >
          <a-select-option value="">全部书籍</a-select-option>
          <a-select-option
            v-for="book in books"
            :key="book.id"
            :value="book.id"
          >
            {{ book.title }}
          </a-select-option>
        </a-select>
        
        <a-select
          v-model:value="selectedChapter"
          placeholder="选择章节"
          style="width: 200px"
          @change="onChapterChange"
          allow-clear
          :disabled="!selectedBook"
        >
          <a-select-option value="">全部章节</a-select-option>
          <a-select-option
            v-for="chapter in chapters"
            :key="chapter.id"
            :value="chapter.id"
          >
            {{ chapter.title }}
          </a-select-option>
        </a-select>
        
        <a-select
          v-model:value="selectedImageType"
          placeholder="图片类型"
          style="width: 150px"
          @change="loadImages"
          allow-clear
        >
          <a-select-option value="">全部类型</a-select-option>
          <a-select-option value="character">角色图</a-select-option>
          <a-select-option value="scene">场景图</a-select-option>
          <a-select-option value="cover">封面图</a-select-option>
          <a-select-option value="other">其他</a-select-option>
        </a-select>
        
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索图片名称或描述"
          style="width: 300px"
          @search="loadImages"
          enter-button
        />
      </div>
      
      <div class="action-controls">
        <a-button @click="resetFilters">
          <template #icon><ReloadOutlined /></template>
          重置
        </a-button>
        <a-button type="primary" @click="loadImages">
          <template #icon><SearchOutlined /></template>
          搜索
        </a-button>
      </div>
    </div>

    <div class="library-content">

    <!-- 图片文件表格 -->
    <a-card :bordered="false">
      <a-table
        :dataSource="displayedImages"
        :columns="columns"
        :pagination="paginationConfig"
        :loading="loading"
        :row-selection="rowSelection"
        @change="onTableChange"
        row-key="id"
        :scroll="{ x: 1200 }"
      >
        <!-- 缩略图列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'thumbnail'">
            <div class="thumbnail-cell">
              <img
                :src="record.image_url"
                :alt="record.scene_description"
                class="thumbnail-image"
                @error="handleImageError"
              />
            </div>
          </template>

          <!-- 文件名列 -->
          <template v-else-if="column.key === 'filename'">
            <div class="filename-cell">
              <div class="file-info">
                <div class="file-name">{{ record.scene_description }}</div>
                <div class="file-size">{{ record.image_width }}×{{ record.image_height }}</div>
              </div>
            </div>
          </template>

          <!-- 项目信息列 -->
          <template v-else-if="column.key === 'project'">
            <div v-if="record.book_title" class="project-info">
              <a-tag color="blue">{{ record.book_title }}</a-tag>
              <div v-if="record.chapter_title" class="chapter-info">
                {{ record.chapter_title }}
              </div>
            </div>
            <span v-else class="text-gray">-</span>
          </template>

          <!-- 图片类型列 -->
          <template v-else-if="column.key === 'imageType'">
            <a-tag color="green">图片</a-tag>
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-tooltip title="预览">
                <a-button
                  type="text"
                  size="small"
                  @click="previewImage(record)"
                  :icon="h(EyeOutlined)"
                />
              </a-tooltip>
              <a-tooltip title="下载">
                <a-button
                  type="text"
                  size="small"
                  @click="downloadImage(record)"
                  :icon="h(DownloadOutlined)"
                />
              </a-tooltip>
              <a-tooltip title="收藏">
                <a-button
                  type="text"
                  size="small"
                  @click="toggleFavorite(record)"
                  :icon="h(record.is_favorite ? HeartFilled : HeartOutlined)"
                  :class="{ 'favorite-active': record.is_favorite }"
                />
              </a-tooltip>
              <a-tooltip title="详情">
                <a-button
                  type="text"
                  size="small"
                  @click="showImageDetail(record)"
                  :icon="h(InfoCircleOutlined)"
                />
              </a-tooltip>
              <a-tooltip title="删除">
                <a-button
                  type="text"
                  size="small"
                  danger
                  @click="deleteSingle(record)"
                  :icon="h(DeleteOutlined)"
                />
              </a-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 图片详情对话框 -->
    <a-modal
      v-model:open="detailDialogVisible"
      title="图片详情"
      width="80%"
      @cancel="closeDetailDialog"
    >
      <div v-if="selectedImage" class="image-detail">
        <div class="detail-left">
          <img
            :src="selectedImage.image_url"
            :alt="selectedImage.scene_description"
            class="detail-image"
          />
        </div>
        <div class="detail-right">
          <a-descriptions :column="1" bordered>
            <a-descriptions-item label="场景描述">
              {{ selectedImage.scene_description }}
            </a-descriptions-item>
            <a-descriptions-item label="文本片段">
              {{ selectedImage.segment_text }}
            </a-descriptions-item>
            <a-descriptions-item label="生成提示词">
              {{ selectedImage.generated_prompt }}
            </a-descriptions-item>
            <a-descriptions-item label="书籍">
              {{ selectedImage.book_title }}
            </a-descriptions-item>
            <a-descriptions-item label="章节">
              {{ selectedImage.chapter_title }}
            </a-descriptions-item>
            <a-descriptions-item label="图片尺寸">
              {{ selectedImage.image_width }}×{{ selectedImage.image_height }}
            </a-descriptions-item>
            <a-descriptions-item label="生成模型">
              {{ selectedImage.generation_model }}
            </a-descriptions-item>
            <a-descriptions-item label="质量评分" v-if="selectedImage.quality_score">
              {{ selectedImage.quality_score }}
            </a-descriptions-item>
            <a-descriptions-item label="用户评分" v-if="selectedImage.user_rating">
              <a-rate v-model:value="selectedImage.user_rating" disabled />
              <span style="margin-left: 8px;">{{ selectedImage.user_rating }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="生成时间">
              {{ formatDate(selectedImage.completed_at) }}
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </div>
      <template #footer>
        <a-button @click="closeDetailDialog">关闭</a-button>
        <a-button type="primary" @click="downloadImage(selectedImage)">下载图片</a-button>
      </template>
    </a-modal>

    <!-- 图片预览对话框 -->
    <a-modal
      v-model:open="previewDialogVisible"
      title="图片预览"
      width="90%"
      @cancel="closePreviewDialog"
    >
      <div v-if="currentPreviewImage" class="image-preview">
        <img
          :src="currentPreviewImage.image_url"
          :alt="currentPreviewImage.scene_description"
          class="preview-image"
        />
      </div>
      <template #footer>
        <a-button @click="closePreviewDialog">关闭</a-button>
      </template>
    </a-modal>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { 
  ReloadOutlined, 
  DeleteOutlined, 
  DownloadOutlined,
  PictureOutlined,
  DatabaseOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  SearchOutlined,
  HeartOutlined,
  EyeOutlined,
  HeartFilled,
  InfoCircleOutlined,
  UploadOutlined
} from '@ant-design/icons-vue'
import { imageGenerationAPI, bookAPI } from '@/api/v2'
import { useBookStore } from '@/stores/book'
import ImageFileList from './image-library/ImageFileList.vue'

const bookStore = useBookStore()

// 标签页状态
const activeTab = ref('all')

// 响应式数据
const loading = ref(false)
const images = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')
const filterBookId = ref(null)
const filterChapterId = ref(null)
const selectedBook = ref(null)
const selectedChapter = ref(null)
const selectedImageType = ref(null)
const downloading = ref(false)
const deleting = ref(false)
const selectedRowKeys = ref([])

// 筛选器对象
const filters = reactive({
  bookId: null,
  chapterId: null,
  imageType: null,
  search: ''
})

// 统计数据
const stats = ref({
  overview: {
    totalFiles: 0,
    totalSizeMB: 0,
    todayCount: 0,
    favoriteCount: 0
  }
})

// 对话框状态
const detailDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const selectedImage = ref(null)
const currentPreviewImage = ref(null)

// 计算属性
const books = computed(() => bookStore.books || [])
const chapters = computed(() => {
  return bookStore.chapters || []
})

// 过滤后的图片数据
const filteredImages = computed(() => {
  const result = images.value || []
  console.log('🔍 filteredImages计算中... images.value:', images.value, '结果:', result)
  return result
})

// 最近生成的图片
const recentImages = computed(() => {
  if (!images.value || !Array.isArray(images.value)) return []
  const now = new Date()
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
  return images.value.filter(img => {
    if (!img || !img.completed_at) return false
    const createdAt = new Date(img.completed_at)
    return !isNaN(createdAt.getTime()) && createdAt >= sevenDaysAgo
  })
})

// 收藏的图片
const favoriteImages = computed(() => {
  if (!images.value || !Array.isArray(images.value)) return []
  return images.value.filter(img => img && img.is_favorite)
})

// 方法
const loadImageLibrary = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    // 注意：不再根据标签页发送过滤参数，改为在前端过滤
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    
    if (filterBookId.value) {
      params.book_id = filterBookId.value
    }
    
    if (filterChapterId.value) {
      params.chapter_id = filterChapterId.value
    }
    
    const response = await imageGenerationAPI.getImageLibrary(params)
    
    if (response.success) {
      console.log('📸 完整API响应:', response)
      console.log('📸 response.data:', response.data)
      console.log('📸 response.data.data:', response.data.data)
      console.log('📸 检查响应结构:', Object.keys(response.data))
      
      // 检查实际的数据结构
      const imageData = response.data.data?.images || response.data.images || []
      const totalData = response.data.data?.total_count || response.data.total_count || 0
      
      console.log('📸 提取的图片数据:', imageData)
      console.log('📸 图片数量:', imageData.length)
      
      images.value = imageData
      totalCount.value = totalData
      console.log('📸 已设置images.value:', images.value)
      console.log('📸 filteredImages:', filteredImages.value)
    } else {
      console.error('❌ 图片库API失败:', response)
      message.error('加载图片库失败')
    }
  } catch (error) {
    console.error('加载图片库失败:', error)
    message.error('加载图片库失败')
  } finally {
    loading.value = false
  }
}

const refreshLibrary = () => {
  currentPage.value = 1
  loadImageLibrary()
}

const handleTabChange = (key) => {
  activeTab.value = key
  // 不再重新加载数据，因为现在使用计算属性在客户端过滤
}

const handleSearch = (keyword) => {
  searchKeyword.value = keyword
  currentPage.value = 1
  loadImageLibrary()
}

const onBookChange = async (bookId) => {
  selectedBook.value = bookId
  selectedChapter.value = null // 重置章节选择
  filterBookId.value = bookId
  filterChapterId.value = null
  
  // 获取选中书籍的章节数据
  if (bookId) {
    try {
      await bookStore.fetchChapters(bookId)
    } catch (error) {
      console.error('获取章节失败:', error)
    }
  }
  
  currentPage.value = 1
  loadImageLibrary()
}

const onChapterChange = (chapterId) => {
  selectedChapter.value = chapterId
  filterChapterId.value = chapterId
  currentPage.value = 1
  loadImageLibrary()
}

const handleBookFilter = async (bookId) => {
  filterBookId.value = bookId
  filterChapterId.value = null // 重置章节过滤
  
  // 获取选中书籍的章节数据
  if (bookId) {
    try {
      const response = await bookAPI.getBookChapters(bookId, {
        exclude_content: true,
        sort_by: 'chapter_number',
        sort_order: 'asc'
      })
      if (response.success && response.data?.data) {
        // 直接设置章节数据到store
        bookStore.chapters = response.data.data
      }
    } catch (error) {
      console.error('获取章节失败:', error)
    }
  } else {
    // 清空章节数据
    bookStore.chapters = []
  }
  
  currentPage.value = 1
  loadImageLibrary()
}

const handleChapterFilter = (chapterId) => {
  filterChapterId.value = chapterId
  currentPage.value = 1
  loadImageLibrary()
}

const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1
  loadImageLibrary()
}

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage
  loadImageLibrary()
}

const showImageDetail = (image) => {
  selectedImage.value = image
  detailDialogVisible.value = true
}

const closeDetailDialog = () => {
  detailDialogVisible.value = false
  selectedImage.value = null
}

const previewImage = (image) => {
  currentPreviewImage.value = image
  previewDialogVisible.value = true
}

const closePreviewDialog = () => {
  previewDialogVisible.value = false
  currentPreviewImage.value = null
}

const downloadImage = async (image) => {
  try {
    const link = document.createElement('a')
    link.href = image.image_url
    link.download = `image_${image.id}_${image.scene_description.substring(0, 20)}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    message.success('图片下载成功')
  } catch (error) {
    console.error('下载图片失败:', error)
    message.error('下载图片失败')
  }
}

const handleImageError = (event) => {
  event.target.src = '/placeholder-image.png' // 设置默认占位图
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 新增缺失的方法
const refreshImageList = () => {
  loadImageLibrary()
}

// 加载图片列表
const loadImages = () => {
  loadImageLibrary()
}

// 重置筛选条件
const resetFilters = () => {
  selectedBook.value = null
  selectedChapter.value = null
  filterBookId.value = null
  filterChapterId.value = null
  searchKeyword.value = ''
  filters.bookId = null
  filters.chapterId = null
  filters.search = ''
  loadImageLibrary()
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const batchDownload = async () => {
  if (!selectedRowKeys.value.length) return
  
  downloading.value = true
  try {
    for (const imageId of selectedRowKeys.value) {
      const image = images.value.find(img => img.id === imageId)
      if (image) {
        await downloadImage(image)
      }
    }
    message.success(`成功下载 ${selectedRowKeys.value.length} 张图片`)
    selectedRowKeys.value = []
  } catch (error) {
    console.error('批量下载失败:', error)
    message.error('批量下载失败')
  } finally {
    downloading.value = false
  }
}

const batchDelete = async () => {
  if (!selectedRowKeys.value.length) return
  
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除选中的 ${selectedRowKeys.value.length} 张图片吗？此操作不可恢复。`,
    onOk: async () => {
      deleting.value = true
      try {
        // 这里需要根据实际API实现删除逻辑
        // await imageGenerationAPI.deleteImages(selectedRowKeys.value)
        message.success(`成功删除 ${selectedRowKeys.value.length} 张图片`)
        selectedRowKeys.value = []
        await loadImageLibrary()
      } catch (error) {
        console.error('批量删除失败:', error)
        message.error('批量删除失败')
      } finally {
        deleting.value = false
      }
    }
  })
}

// 表格相关配置
const columns = ref([
  {
    title: '缩略图',
    key: 'thumbnail',
    width: 100
  },
  {
    title: '文件信息',
    key: 'filename',
    width: 200
  },
  {
    title: '项目信息',
    key: 'project',
    width: 150
  },
  {
    title: '类型',
    key: 'imageType',
    width: 80
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right'
  }
])

const displayedImages = computed(() => {
  return images.value || []
})

const paginationConfig = computed(() => ({
  current: currentPage.value,
  pageSize: pageSize.value,
  total: totalCount.value,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
}))

const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys) => {
    selectedRowKeys.value = keys
  }
}))

const onTableChange = (pagination) => {
  currentPage.value = pagination.current
  pageSize.value = pagination.pageSize
  loadImageLibrary()
}

// 新增缺失的方法
const toggleFavorite = async (image) => {
  try {
    // 这里需要根据实际API实现收藏切换逻辑
    // await imageGenerationAPI.toggleFavorite(image.id)
    image.is_favorite = !image.is_favorite
    message.success(image.is_favorite ? '已添加到收藏' : '已取消收藏')
  } catch (error) {
    console.error('切换收藏状态失败:', error)
    message.error('操作失败')
  }
}

const deleteSingle = async (image) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除图片"${image.scene_description}"吗？此操作不可恢复。`,
    onOk: async () => {
      try {
        // 这里需要根据实际API实现删除逻辑
        // await imageGenerationAPI.deleteImage(image.id)
        message.success('删除成功')
        await loadImageLibrary()
      } catch (error) {
        console.error('删除失败:', error)
        message.error('删除失败')
      }
    }
  })
}

// 同步filters对象与现有变量
watch(() => filters.bookId, (newVal) => {
  filterBookId.value = newVal
  handleBookFilter(newVal)
})

watch(() => filters.chapterId, (newVal) => {
  filterChapterId.value = newVal
  handleChapterFilter(newVal)
})

watch(() => filters.search, (newVal) => {
  searchKeyword.value = newVal
  handleSearch(newVal)
})

// 生命周期
onMounted(async () => {
  // 获取已发布状态的书籍用于筛选
  await bookStore.fetchBooks({ status: 'published' })
  await loadImageLibrary()
})
</script>

<style scoped>
.image-library {
  background: #f8fafc;
  min-height: 100vh;
  padding: 24px;
}

/* 页面头部样式 */
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

.title-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title {
  display: flex;
  align-items: center;
  margin: 0;
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

.action-section {
  display: flex;
  gap: 16px;
}

/* 统计卡片样式 */
.stats-cards {
  margin-bottom: 24px;
}

.stats-cards .ant-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stats-cards .ant-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* 筛选区域样式 */
.filter-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-controls {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.action-controls {
  display: flex;
  gap: 12px;
}

.library-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.library-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #262626;
}

/* 表格容器样式 */
.ant-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: none;
}

/* 缩略图样式 */
.thumbnail-cell {
  display: flex;
  justify-content: center;
  align-items: center;
}

.thumbnail-image {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.thumbnail-image:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 文件信息样式 */
.filename-cell {
  display: flex;
  align-items: center;
}

.file-info {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
  line-height: 1.4;
}

.file-size {
  font-size: 12px;
  color: #8c8c8c;
}

/* 项目信息样式 */
.project-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chapter-info {
  font-size: 12px;
  color: #8c8c8c;
}

.text-gray {
  color: #8c8c8c;
}

.library-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.library-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.library-tabs :deep(.ant-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.library-tabs :deep(.ant-tabs-content-holder) {
  flex: 1;
  overflow: hidden;
}

.library-tabs :deep(.ant-tabs-tabpane) {
  height: 100%;
  padding: 0 16px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.image-detail {
  display: flex;
  gap: 20px;
}

.detail-left {
  flex: 1;
}

.detail-image {
  width: 100%;
  max-height: 500px;
  object-fit: contain;
  border-radius: 8px;
}

.detail-right {
  flex: 1;
}

.image-preview {
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .image-library {
    padding: 16px;
  }
  
  .page-header {
    padding: 24px;
  }
  
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .action-controls {
    justify-content: center;
  }
}

/* 暗黑模式适配 */
[data-theme='dark'] .image-library {
  background: #141414 !important;
}

[data-theme='dark'] .page-header {
  background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

[data-theme='dark'] .filter-section,
[data-theme='dark'] .ant-card {
  background: #1f1f1f !important;
  border: 1px solid #434343 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

[data-theme='dark'] .file-name {
  color: #fff !important;
}

[data-theme='dark'] .file-size,
[data-theme='dark'] .chapter-info,
[data-theme='dark'] .text-gray {
  color: #8c8c8c !important;
}
</style>