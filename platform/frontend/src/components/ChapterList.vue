<template>
  <div class="chapter-list">
    <a-card :bordered="false" class="chapter-card">
      <template #title>
        <div class="chapter-header">
          <h3>
            📚 章节列表 <span class="chapter-count">共{{ totalChapters }}章</span>
          </h3>
        </div>
      </template>

      <template #extra>
        <a-button @click="$emit('detectChapters')" :loading="detectingChapters" size="small">
          🔍 重新检测
        </a-button>
      </template>

      <!-- 搜索框 -->
      <div class="search-section">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索章节标题..."
          @search="handleSearch"
          @change="handleSearchChange"
          allowClear
          :loading="loading"
        />
      </div>

      <!-- 性能提示 -->
      <div v-if="totalChapters > 1000" class="performance-tip">
        <a-alert
          message="性能优化"
          description="检测到大量章节，已启用分页加载"
          type="info"
          show-icon
          :closable="false"
        />
      </div>

      <!-- 章节列表 -->
      <div class="chapters-container" ref="containerRef">
        <div v-if="loading && paginatedChapters.length === 0" class="loading-state">
          <a-spin tip="加载章节中..." />
        </div>

        <div v-else-if="paginatedChapters.length === 0" class="empty-state">
          <a-empty
            :description="searchKeyword ? '没有找到匹配的章节' : '暂无章节'"
            :image="searchKeyword ? undefined : 'simple'"
          >
            <a-button
              v-if="!searchKeyword && totalChapters === 0"
              type="primary"
              @click="$emit('detectChapters')"
              :loading="detectingChapters"
            >
              🔍 检测章节
            </a-button>
          </a-empty>
        </div>

        <!-- 虚拟滚动容器 -->
        <div v-else class="virtual-scroll-container">
          <div class="virtual-scroll-viewport" ref="viewportRef" @scroll="handleScroll">
            <div class="virtual-scroll-content" :style="{ height: totalHeight + 'px' }">
              <div
                v-for="chapter in visibleChapters"
                :key="chapter.id"
                class="chapter-item"
                :class="{
                  'chapter-active': selectedChapterId === chapter.id,
                  'chapter-prepared': chapterPreparationStatus[chapter.id]?.preparation_complete
                }"
                :style="{ transform: `translateY(${chapter.offsetY}px)` }"
                @click="selectChapter(chapter)"
              >
                <div class="chapter-main">
                  <div class="chapter-number">第{{ chapter.chapter_number }}章</div>
                  <div class="chapter-title">{{ chapter.chapter_title }}</div>
                </div>

                <div class="chapter-meta">
                  <div class="chapter-stats">
                    <span class="word-count">{{ chapter.word_count || 0 }} 字</span>
                  </div>

                  <!-- 智能准备状态 -->
                  <div class="preparation-status">
                    <a-tag
                      v-if="chapterPreparationStatus[chapter.id]"
                      :color="getPreparationStatusColor(chapterPreparationStatus[chapter.id])"
                      size="small"
                    >
                      {{ getPreparationStatusText(chapterPreparationStatus[chapter.id]) }}
                    </a-tag>
                    <a-tag v-else-if="chapter.status === 'completed'" color="green" size="small">
                      已准备
                    </a-tag>
                    <a-tag v-else color="default" size="small"> 未准备 </a-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页信息 -->
      <div v-if="totalChapters > 0" class="pagination-info">
        <span>显示 {{ visibleStart }} - {{ visibleEnd }} / {{ totalChapters }} 章</span>
        <a-button
          v-if="hasMore && !loading"
          type="link"
          size="small"
          @click="loadMore"
          :loading="loadingMore"
        >
          加载更多
        </a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup>
  import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
  import { booksAPI } from '@/api'
  import { message } from 'ant-design-vue'

  const props = defineProps({
    bookId: {
      type: [String, Number],
      required: true
    },
    selectedChapterId: {
      type: [String, Number],
      default: null
    },
    chapterPreparationStatus: {
      type: Object,
      default: () => ({})
    },
    preparingChapters: {
      type: Set,
      default: () => new Set()
    },
    detectingChapters: {
      type: Boolean,
      default: false
    }
  })

  const emit = defineEmits([
    'selectChapter',
    'prepareChapter',
    'detectChapters',
    'update:total-chapters'
  ])

  // 分页配置
  const ITEM_HEIGHT = 72 // 每个章节项的高度(px)
  const PAGE_SIZE = 100 // 每次加载的章节数
  const VISIBLE_BUFFER = 5 // 可视区域缓冲区

  // 响应式数据
  const loading = ref(false)
  const loadingMore = ref(false)
  const searchKeyword = ref('')
  const chapters = ref([])
  const skip = ref(0)
  const totalChapters = ref(0)

  // 客户端缓存
  const chapterCache = new Map()
  const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

  // 虚拟滚动相关
  const containerRef = ref(null)
  const viewportRef = ref(null)
  const scrollTop = ref(0)
  const containerHeight = ref(0)

  // 分页数据
  const currentPage = ref(1)

  // 计算属性
  const allChapters = computed(() => {
    // 客户端搜索过滤
    if (!searchKeyword.value) return chapters.value

    const keyword = searchKeyword.value.toLowerCase()
    return chapters.value.filter(
      (chapter) =>
        chapter.title.toLowerCase().includes(keyword) || chapter.number.toString().includes(keyword)
    )
  })

  const totalHeight = computed(() => allChapters.value.length * ITEM_HEIGHT)

  const visibleStart = computed(() =>
    Math.max(0, Math.floor(scrollTop.value / ITEM_HEIGHT) - VISIBLE_BUFFER)
  )

  const visibleEnd = computed(() =>
    Math.min(
      allChapters.value.length,
      Math.ceil((scrollTop.value + containerHeight.value) / ITEM_HEIGHT) + VISIBLE_BUFFER
    )
  )

  const visibleChapters = computed(() => {
    const start = visibleStart.value
    const end = visibleEnd.value

    return allChapters.value.slice(start, end).map((chapter, index) => ({
      ...chapter,
      offsetY: (start + index) * ITEM_HEIGHT
    }))
  })

  const hasMore = computed(() => skip.value + PAGE_SIZE < totalChapters.value)

  const paginatedChapters = computed(() => allChapters.value)

  // 方法
  const loadChapters = async (loadMore = false) => {
    if (!props.bookId) return

    if (loadMore) {
      loadingMore.value = true
    } else {
      loading.value = true
    }

    try {
      const cacheKey = `chapters_${props.bookId}_${skip.value}_${searchKeyword.value}`

      // 检查缓存
      if (!loadMore && chapterCache.has(cacheKey)) {
        const cachedData = chapterCache.get(cacheKey)
        chapters.value = cachedData.chapters
        totalChapters.value = cachedData.total
        emit('update:total-chapters', totalChapters.value)

        if (cachedData.chapters.length > 0 && !props.selectedChapterId) {
          emit('selectChapter', cachedData.chapters[0])
        }
        return
      }

      const params = {
        skip: skip.value,
        limit: PAGE_SIZE,
        exclude_content: true
      }

      // 服务端搜索
      if (searchKeyword.value) {
        params.query = searchKeyword.value
      }

      const response = await booksAPI.getBookChapters(props.bookId, params)

      if (response.data?.success) {
        const newChapters = response.data.data || []

        if (loadMore) {
          chapters.value.push(...newChapters)
        } else {
          chapters.value = newChapters
        }

        totalChapters.value = response.data.total || 0
        emit('update:total-chapters', totalChapters.value)

        // 缓存数据
        if (!loadMore) {
          chapterCache.set(cacheKey, {
            chapters: newChapters,
            total: response.data.total || 0,
            timestamp: Date.now()
          })
        }

        // 如果是首次加载且有章节，选中第一个
        if (!loadMore && newChapters.length > 0 && !props.selectedChapterId) {
          emit('selectChapter', newChapters[0])
        }
      }
    } catch (error) {
      console.error('加载章节失败:', error)
      message.error('加载章节失败')
    } finally {
      loading.value = false
      loadingMore.value = false
    }
  }

  const loadMore = async () => {
    if (hasMore.value && !loadingMore.value) {
      skip.value += PAGE_SIZE
      await loadChapters(true)
    }
  }

  const selectChapter = (chapter) => {
    emit('selectChapter', chapter)
  }

  const handleSearch = async (value) => {
    searchKeyword.value = value
    skip.value = 0

    // 清除搜索缓存
    if (!value) {
      // 清除所有搜索相关的缓存
      for (const key of chapterCache.keys()) {
        if (key.includes('_search_')) {
          chapterCache.delete(key)
        }
      }
    }

    // 服务端搜索
    if (value) {
      const searchCacheKey = `chapters_${props.bookId}_search_${value}`

      // 检查搜索缓存
      if (chapterCache.has(searchCacheKey)) {
        const cachedData = chapterCache.get(searchCacheKey)
        chapters.value = cachedData.chapters
        totalChapters.value = cachedData.total
        return
      }

      try {
        const response = await booksAPI.searchChapters(props.bookId, {
          query: value,
          skip: 0,
          limit: 1000 // 搜索时获取更多结果
        })

        if (response.data?.success) {
          chapters.value = response.data.data || []
          totalChapters.value = response.data.total || 0

          // 缓存搜索结果
          chapterCache.set(searchCacheKey, {
            chapters: response.data.data || [],
            total: response.data.total || 0,
            timestamp: Date.now()
          })
        }
      } catch (error) {
        console.error('搜索章节失败:', error)
        message.error('搜索章节失败')
      }
    } else {
      // 重置为分页加载
      await loadChapters()
    }
  }

  const handleSearchChange = (e) => {
    const value = e.target.value
    // 防抖搜索
    clearTimeout(window.searchTimeout)
    window.searchTimeout = setTimeout(() => {
      handleSearch(value)
    }, 300)
  }

  const handleScroll = (event) => {
    scrollTop.value = event.target.scrollTop
  }

  const updateContainerHeight = () => {
    if (viewportRef.value) {
      containerHeight.value = viewportRef.value.clientHeight
    }
  }

  const getPreparationStatusColor = (status) => {
    if (status?.preparation_complete) return 'green'
    if (status?.preparation_started) return 'blue'
    return 'default'
  }

  const getPreparationStatusText = (status) => {
    if (status?.preparation_complete) return '已准备'
    if (status?.preparation_started) return '准备中'
    return '未准备'
  }

  // 监听滚动到底部
  const handleScrollToBottom = () => {
    if (viewportRef.value) {
      const { scrollTop, scrollHeight, clientHeight } = viewportRef.value
      if (scrollTop + clientHeight >= scrollHeight - 100 && hasMore.value) {
        loadMore()
      }
    }
  }

  // 缓存管理
  const clearExpiredCache = () => {
    const now = Date.now()
    for (const [key, value] of chapterCache.entries()) {
      if (now - value.timestamp > CACHE_DURATION) {
        chapterCache.delete(key)
      }
    }
  }

  // 延迟加载策略
  const loadChapterContent = async (chapterId) => {
    const contentCacheKey = `content_${chapterId}`

    // 检查内容缓存
    if (chapterCache.has(contentCacheKey)) {
      return chapterCache.get(contentCacheKey).content
    }

    try {
      const response = await booksAPI.getChapterContent(chapterId)
      if (response.data?.success) {
        const content = response.data.data?.content || ''

        // 缓存内容（3分钟）
        chapterCache.set(contentCacheKey, {
          content,
          timestamp: Date.now()
        })

        return content
      }
    } catch (error) {
      console.error('加载章节内容失败:', error)
    }

    return ''
  }

  // 批量加载准备状态
  const loadPreparationStatusBatch = async (chapterIds) => {
    if (!chapterIds?.length) return

    const statusCacheKey = `status_${props.bookId}_${chapterIds.join('_')}`

    // 检查状态缓存
    if (chapterCache.has(statusCacheKey)) {
      return chapterCache.get(statusCacheKey).status
    }

    try {
      const response = await booksAPI.getChaptersPreparationStatus(props.bookId, {
        chapter_ids: chapterIds
      })

      if (response.data?.success) {
        const statusMap = response.data.data || {}

        // 缓存状态（1分钟）
        chapterCache.set(statusCacheKey, {
          status: statusMap,
          timestamp: Date.now()
        })

        return statusMap
      }
    } catch (error) {
      console.error('批量加载准备状态失败:', error)
    }

    return {}
  }

  // 生命周期
  let cacheCleanupInterval
  
  onMounted(async () => {
    // 清理过期缓存
    clearExpiredCache()

    await loadChapters()

    nextTick(() => {
      updateContainerHeight()
      if (viewportRef.value) {
        viewportRef.value.addEventListener('scroll', handleScrollToBottom)
      }
    })

    // 每5分钟清理一次过期缓存
    cacheCleanupInterval = setInterval(clearExpiredCache, 5 * 60 * 1000)
  })

  onUnmounted(() => {
    if (cacheCleanupInterval) {
      clearInterval(cacheCleanupInterval)
    }
    if (viewportRef.value) {
      viewportRef.value.removeEventListener('scroll', handleScrollToBottom)
    }
  })

  // 监听属性变化
  watch(
    () => props.bookId,
    async (newBookId) => {
      if (newBookId) {
        skip.value = 0
        searchKeyword.value = ''
        await loadChapters()
      }
    }
  )

  watch(
    () => props.chapters,
    (newChapters) => {
      if (newChapters && newChapters.length > 0) {
        chapters.value = newChapters
        totalChapters.value = newChapters.length
      }
    }
  )
</script>

<style scoped>
  .chapter-list {
    height: 100%;
  }

  .chapter-card {
    display: flex;
    flex-direction: column;
  }

  .chapter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }

  .chapter-header h3 {
    margin: 0;
    font-size: 16px;
    color: #1f2937;
  }

  .chapter-count {
    font-size: 12px;
    color: #6b7280;
  }

  .search-section {
    margin-bottom: 16px;
  }

  .chapters-container {
    flex: 1;
    overflow: hidden;
  }

  .chapters-list {
    height: 100%;
    overflow-y: auto;
    padding-right: 4px;
  }

  .chapter-item {
    display: flex;
    align-items: center;
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid transparent;
    position: relative;
  }

  .chapter-item:hover {
    transform: translateX(4px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .chapter-item.chapter-active {
    background: #dbeafe;
    border-color: #3b82f6;
    transform: translateX(4px);
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
  }

  .chapter-item.chapter-prepared {
    border-left: 4px solid #10b981;
  }

  .chapter-main {
    flex: 1;
    min-width: 0;
  }

  .chapter-number {
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 2px;
  }

  .chapter-title {
    font-size: 14px;
    color: #1f2937;
    font-weight: 500;
    line-height: 1.4;
    word-break: break-word;
  }

  .chapter-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-items: flex-end;
    margin-left: 12px;
  }

  .chapter-stats {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .word-count {
    font-size: 11px;
    color: #9ca3af;
  }

  .preparation-status {
    display: flex;
    align-items: center;
  }

  .chapter-actions {
    margin-left: 8px;
    opacity: 0;
    transition: opacity 0.2s;
  }

  .chapter-item:hover .chapter-actions {
    opacity: 1;
  }

  .chapter-item.chapter-active .chapter-actions {
    opacity: 1;
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
  }

  /* 滚动条样式 */
  .chapters-list::-webkit-scrollbar {
    width: 6px;
  }

  .chapters-list::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
  }

  .chapters-list::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }

  .chapters-list::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
</style>
