<template>
  <div class="chapter-list-simple">
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
          allowClear
          :loading="loading"
        />
      </div>

      <!-- 使用标准 Ant Menu 组件 -->
      <div class="chapters-container">
        <div v-if="loading" class="loading-state">
          <a-spin tip="加载章节中..." />
        </div>

        <div v-else-if="filteredChapters.length === 0" class="empty-state">
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

        <!-- 标准 Ant Menu -->
        <a-menu
          v-else
          v-model:selectedKeys="selectedKeys"
          mode="inline"
          class="chapter-menu"
          @select="handleMenuSelect"
        >
          <a-menu-item
            v-for="chapter in paginatedChapters"
            :key="chapter.id"
            class="chapter-menu-item"
          >
            <div class="chapter-item-content">
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
          </a-menu-item>
        </a-menu>

        <!-- 分页组件 -->
        <div v-if="totalChapters > pageSize" class="pagination-section">
          <a-pagination
            v-model:current="currentPage"
            v-model:page-size="pageSize"
            :total="filteredChapters.length"
            :show-size-changer="false"
            :show-quick-jumper="true"
            :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
            size="small"
            @change="handlePageChange"
          />
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
  import { ref, computed, watch, onMounted } from 'vue'
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
  const pageSize = ref(50) // 每页显示50个章节
  const currentPage = ref(1)

  // 响应式数据
  const loading = ref(false)
  const searchKeyword = ref('')
  const chapters = ref([])
  const totalChapters = ref(0)
  const selectedKeys = ref([])

  // 计算属性
  const filteredChapters = computed(() => {
    if (!searchKeyword.value) return chapters.value

    const keyword = searchKeyword.value.toLowerCase()
    return chapters.value.filter(
      (chapter) =>
        chapter.chapter_title.toLowerCase().includes(keyword) ||
        chapter.chapter_number.toString().includes(keyword)
    )
  })

  const paginatedChapters = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredChapters.value.slice(start, end)
  })

  // 方法
  const loadChapters = async () => {
    if (!props.bookId) return

    loading.value = true

    try {
      const response = await booksAPI.getBookChapters(props.bookId, {
        skip: 0,
        limit: 10000, // 一次性加载所有章节
        exclude_content: true
      })

      if (response.data?.success) {
        chapters.value = response.data.data || []
        totalChapters.value = response.data.total || 0
        emit('update:total-chapters', totalChapters.value)

        // 如果有章节且没有选中的，选中第一个
        if (chapters.value.length > 0 && !props.selectedChapterId) {
          emit('selectChapter', chapters.value[0])
          selectedKeys.value = [chapters.value[0].id]
        }
      }
    } catch (error) {
      console.error('加载章节失败:', error)
      message.error('加载章节失败')
    } finally {
      loading.value = false
    }
  }

  const handleSearch = () => {
    currentPage.value = 1 // 搜索时重置到第一页
  }

  const handlePageChange = (page) => {
    currentPage.value = page
  }

  const handleMenuSelect = ({ key }) => {
    const chapter = chapters.value.find(c => c.id == key)
    if (chapter) {
      emit('selectChapter', chapter)
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

  // 生命周期
  onMounted(async () => {
    await loadChapters()
  })

  // 监听属性变化
  watch(
    () => props.bookId,
    async (newBookId) => {
      if (newBookId) {
        await loadChapters()
      }
    }
  )

  watch(
    () => props.selectedChapterId,
    (newId) => {
      if (newId) {
        selectedKeys.value = [newId]
      }
    },
    { immediate: true }
  )

  watch(
    () => searchKeyword.value,
    () => {
      currentPage.value = 1 // 搜索变化时重置页码
    }
  )
</script>

<style scoped>
  .chapter-list-simple {
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
    font-weight: 600;
  }

  .chapter-count {
    color: #666;
    font-weight: normal;
    font-size: 14px;
  }

  .search-section {
    margin-bottom: 16px;
  }

  .chapters-container {
    flex: 1;
    overflow: hidden;
  }

  .loading-state,
  .empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 200px;
  }

  .chapter-menu {
    border: none;
    background: transparent;
    max-height: 600px;
    overflow-y: auto;
  }

  .chapter-menu-item {
    height: auto !important;
    line-height: normal !important;
    padding: 8px 16px !important;
    margin-bottom: 4px;
    border-radius: 6px;
  }

  .chapter-menu-item:hover {
    background-color: #f5f5f5;
  }

  .chapter-menu-item.ant-menu-item-selected {
    background-color: #e6f7ff;
    border-right: 3px solid #1890ff;
  }

  .chapter-item-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }

  .chapter-main {
    flex: 1;
    min-width: 0;
  }

  .chapter-number {
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
  }

  .chapter-title {
    font-size: 14px;
    font-weight: 500;
    color: #333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chapter-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
  }

  .chapter-stats {
    font-size: 12px;
    color: #999;
  }

  .word-count {
    margin-right: 8px;
  }

  .preparation-status {
    display: flex;
    gap: 4px;
  }

  .pagination-section {
    margin-top: 16px;
    text-align: center;
    padding: 16px 0;
    border-top: 1px solid #f0f0f0;
  }
</style>