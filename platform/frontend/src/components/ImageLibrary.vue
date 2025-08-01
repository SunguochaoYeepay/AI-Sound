<template>
  <div class="image-library">
    <div class="library-header">
      <h4>图片库</h4>
      <a-space size="small">
        <a-button
          size="small"
          @click="refreshLibrary"
          :loading="loading"
          title="刷新图片库"
        >
          <template #icon><ReloadOutlined /></template>
        </a-button>
      </a-space>
    </div>
    <div class="library-content">
      <div class="library-tabs">
        <a-tabs :activeKey="activeTab" size="small" @change="handleTabChange">
          <a-tab-pane key="all" tab="全部图片">
            <ImageFileList
              :images="filteredImages"
              :loading="loading"
              :search-keyword="searchKeyword"
              category="all"
              placeholder="搜索图片内容、场景描述..."
              empty-icon="🖼️"
              empty-text="暂无图片文件"
              empty-desc="前往图片生成页面创建图片"
              :books="books"
              :chapters="chapters"
              :filter-book-id="filterBookId"
              :filter-chapter-id="filterChapterId"
              @search="handleSearch"
              @filter-book="handleBookFilter"
              @filter-chapter="handleChapterFilter"
              @preview="previewImage"
              @download="downloadImage"
              @detail="showImageDetail"
            />
          </a-tab-pane>
          <a-tab-pane key="recent" tab="最近生成">
            <ImageFileList
              :images="recentImages"
              :loading="loading"
              :search-keyword="searchKeyword"
              category="recent"
              placeholder="搜索最近生成的图片..."
              empty-icon="🕒"
              empty-text="暂无最近生成的图片"
              empty-desc="前往图片生成页面创建图片"
              :books="books"
              :chapters="chapters"
              :filter-book-id="filterBookId"
              :filter-chapter-id="filterChapterId"
              @search="handleSearch"
              @filter-book="handleBookFilter"
              @filter-chapter="handleChapterFilter"
              @preview="previewImage"
              @download="downloadImage"
              @detail="showImageDetail"
            />
          </a-tab-pane>
          <a-tab-pane key="favorites" tab="收藏图片">
            <ImageFileList
              :images="favoriteImages"
              :loading="loading"
              :search-keyword="searchKeyword"
              category="favorites"
              placeholder="搜索收藏的图片..."
              empty-icon="⭐"
              empty-text="暂无收藏的图片"
              empty-desc="在图片详情中点击收藏按钮"
              :books="books"
              :chapters="chapters"
              :filter-book-id="filterBookId"
              :filter-chapter-id="filterChapterId"
              @search="handleSearch"
              @filter-book="handleBookFilter"
              @filter-chapter="handleChapterFilter"
              @preview="previewImage"
              @download="downloadImage"
              @detail="showImageDetail"
            />
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <a-pagination
        v-model:current="currentPage"
        v-model:page-size="pageSize"
        :page-size-options="['20', '50', '100']"
        :total="totalCount"
        show-size-changer
        show-quick-jumper
        :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
        @change="handleCurrentChange"
        @show-size-change="handleSizeChange"
      />
    </div>

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
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
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

// 监听书籍选择变化已在handleBookFilter方法中处理，无需重复watch

// 生命周期
onMounted(async () => {
  // 获取已发布状态的书籍用于筛选
  await bookStore.fetchBooks({ status: 'published' })
  await loadImageLibrary()
})
</script>

<style scoped>
.image-library {
  height: 100%;
  display: flex;
  flex-direction: column;
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
</style>