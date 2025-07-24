<template>
  <div class="virtual-chapter-list">
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
          🔍 重置
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
          :loading="searching"
        />
      </div>

      <!-- 虚拟滚动容器 -->
      <div class="virtual-scroll-container" ref="containerRef">
        <div class="virtual-scroll-phantom" :style="{ height: totalHeight + 'px' }">
          <div class="virtual-scroll-content" :style="{ transform: `translateY(${offsetY}px)` }">
            <div
              v-for="item in visibleItems"
              :key="item.chapter.id"
              class="chapter-item"
              :class="{
                'chapter-active': selectedChapterId === item.chapter.id,
                'chapter-prepared': chapterPreparationStatus[item.chapter.id]?.preparation_complete
              }"
              :style="{ 
                height: itemHeight + 'px',
                position: 'absolute',
                top: (item.index * itemHeight) + 'px',
                left: 0,
                right: 0
              }"
              @click="selectChapter(item.chapter)"
            >
              <div class="chapter-main">
                <div class="chapter-number">第{{ item.chapter.chapter_number }}章</div>
                <div class="chapter-title">{{ item.chapter.chapter_title }}</div>
              </div>

              <div class="chapter-meta">
                <div class="chapter-stats">
                  <span class="word-count">{{ item.chapter.word_count || 0 }} 字</span>
                </div>

                <div class="preparation-status">
                  <a-tag
                    v-if="chapterPreparationStatus[item.chapter.id]"
                    :color="getPreparationStatusColor(chapterPreparationStatus[item.chapter.id])"
                    size="small"
                  >
                    {{ getPreparationStatusText(chapterPreparationStatus[item.chapter.id]) }}
                  </a-tag>
                  <a-tag v-else-if="item.chapter.status === 'completed'" color="green" size="small">
                    已准备
                  </a-tag>
                  <a-tag v-else color="default" size="small"> 未准备 </a-tag>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载更多 -->
        <div v-if="loadingMore" class="loading-more">
          <a-spin size="small" />
          <span>加载中...</span>
        </div>

        <!-- 空状态 -->
        <div v-if="visibleItems.length === 0 && !loading" class="empty-state">
          <a-empty
            :description="searchKeyword ? '没有找到匹配的章节' : '暂无章节'"
            :image="searchKeyword ? undefined : 'simple'"
          >
            <a-button
              v-if="!searchKeyword && chapters.length === 0"
              type="primary"
              @click="$emit('detectChapters')"
              :loading="detectingChapters"
            >
              🔍 检测章节
            </a-button>
          </a-empty>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
  import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

  const props = defineProps({
    chapters: {
      type: Array,
      default: () => []
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
    },
    loading: {
      type: Boolean,
      default: false
    },
    pageSize: {
      type: Number,
      default: 100
    },
    total: {
      type: Number,
      default: 0
    }
  })

  const emit = defineEmits([
    'selectChapter',
    'prepareChapter',
    'detectChapters',
    'loadMore',
    'search'
  ])

  // 虚拟滚动相关
  const containerRef = ref(null)
  const itemHeight = 72 // 每个章节项的高度（px）
  const bufferSize = 5 // 缓冲区项目数量
  const scrollTop = ref(0)
  const containerHeight = ref(0)

  // 搜索相关
  const searchKeyword = ref('')
  const searching = ref(false)
  const searchTimeout = ref(null)

  // 分页相关
  const currentPage = ref(1)
  const loadingMore = ref(false)

  // 计算总章节数
  const totalChapters = computed(() => props.total || props.chapters.length)

  // 计算总高度
  const totalHeight = computed(() => {
    return totalChapters.value * itemHeight
  })

  // 计算可视区域的项目索引
  const startIndex = computed(() => {
    return Math.max(0, Math.floor(scrollTop.value / itemHeight) - bufferSize)
  })

  const endIndex = computed(() => {
    return Math.min(
      totalChapters.value,
      Math.ceil((scrollTop.value + containerHeight.value) / itemHeight) + bufferSize
    )
  })

  // 计算偏移量
  const offsetY = computed(() => {
    return startIndex.value * itemHeight
  })

  // 计算可视项目
  const visibleItems = computed(() => {
    const items = []
    for (let i = startIndex.value; i < endIndex.value; i++) {
      if (i < props.chapters.length) {
        items.push({
          index: i,
          chapter: props.chapters[i]
        })
      }
    }
    return items
  })

  // 滚动事件处理
  const handleScroll = async () => {
    if (!containerRef.value) return

    scrollTop.value = containerRef.value.scrollTop
    containerHeight.value = containerRef.value.clientHeight

    // 检查是否需要加载更多
    const scrollBottom = scrollTop.value + containerHeight.value
    const threshold = totalHeight.value - 200 // 距离底部200px时触发

    if (scrollBottom >= threshold && !loadingMore.value && !props.loading) {
      if (props.chapters.length < totalChapters.value) {
        loadingMore.value = true
        currentPage.value++
        emit('loadMore', {
          page: currentPage.value,
          keyword: searchKeyword.value
        })
      }
    }
  }

  // 搜索处理
  const handleSearch = async (value) => {
    searchKeyword.value = value
    searching.value = true

    // 重置分页
    currentPage.value = 1

    emit('search', {
      keyword: value,
      page: 1
    })

    searching.value = false

    // 滚动到顶部
    nextTick(() => {
      if (containerRef.value) {
        containerRef.value.scrollTop = 0
      }
    })
  }

  const handleSearchChange = (e) => {
    const value = e.target.value
    searchKeyword.value = value

    // 防抖搜索
    if (searchTimeout.value) {
      clearTimeout(searchTimeout.value)
    }

    searchTimeout.value = setTimeout(() => {
      handleSearch(value)
    }, 300)
  }

  // 选择章节
  const selectChapter = (chapter) => {
    emit('selectChapter', chapter)
  }

  // 获取准备状态颜色
  const getPreparationStatusColor = (status) => {
    if (status.preparation_complete) return 'green'
    if (status.preparation_started) return 'blue'
    return 'default'
  }

  // 获取准备状态文本
  const getPreparationStatusText = (status) => {
    if (status.preparation_complete) return '已准备'
    if (status.preparation_started) return '准备中'
    return '未准备'
  }

  // 重置滚动位置
  const scrollToChapter = (chapterId) => {
    const index = props.chapters.findIndex((c) => c.id === chapterId)
    if (index !== -1 && containerRef.value) {
      containerRef.value.scrollTop = index * itemHeight
    }
  }

  // 监听数据变化
  watch(
    () => props.chapters,
    () => {
      loadingMore.value = false
    },
    { deep: true }
  )

  // 监听容器大小变化
  const resizeObserver = ref(null)

  onMounted(() => {
    if (containerRef.value) {
      containerHeight.value = containerRef.value.clientHeight
      containerRef.value.addEventListener('scroll', handleScroll)

      // 使用 ResizeObserver 监听容器大小变化
      if (window.ResizeObserver) {
        resizeObserver.value = new ResizeObserver(() => {
          if (containerRef.value) {
            containerHeight.value = containerRef.value.clientHeight
          }
        })
        resizeObserver.value.observe(containerRef.value)
      }
    }
  })

  onUnmounted(() => {
    if (containerRef.value) {
      containerRef.value.removeEventListener('scroll', handleScroll)
    }
    if (resizeObserver.value) {
      resizeObserver.value.disconnect()
    }
    if (searchTimeout.value) {
      clearTimeout(searchTimeout.value)
    }
  })

  // 暴露方法给父组件
  defineExpose({
    scrollToChapter,
    resetScroll: () => {
      if (containerRef.value) {
        containerRef.value.scrollTop = 0
      }
    }
  })
</script>

<style scoped>
  .virtual-chapter-list {
    height: 100%;
  }

  .chapter-card {
    display: flex;
    flex-direction: column;
    height: 100%;
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
    margin-left: 8px;
  }

  .search-section {
    margin-bottom: 16px;
  }

  .virtual-scroll-container {
    flex: 1;
    position: relative;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .virtual-scroll-phantom {
    position: relative;
    width: 100%;
  }

  .virtual-scroll-content {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
  }

  .chapter-item {
    display: flex;
    align-items: center;
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid transparent;
    box-sizing: border-box;
    width: 100%;
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

  .loading-more {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    gap: 8px;
    color: #6b7280;
    font-size: 14px;
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
  }

  /* 滚动条样式 */
  .virtual-scroll-container::-webkit-scrollbar {
    width: 6px;
  }

  .virtual-scroll-container::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
  }

  .virtual-scroll-container::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }

  .virtual-scroll-container::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }

  /* 响应式设计 */
  @media (max-width: 768px) {
    .chapter-item {
      padding: 8px;
      margin-bottom: 4px;
    }

    .chapter-title {
      font-size: 13px;
    }

    .chapter-number {
      font-size: 11px;
    }
  }
</style>
