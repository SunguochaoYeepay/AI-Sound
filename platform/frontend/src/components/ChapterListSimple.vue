<template>
  <div class="chapter-list-simple">
    <a-card :bordered="false" class="chapter-card">
      <template #title>
        <div class="chapter-header">
          <div class="title-section">
            <a-button
              type="text"
              size="small"
              @click="toggleCollapse"
              :title="collapsed ? '展开章节列表' : '收起章节列表'"
              class="collapse-btn"
            >
              <template #icon>
                <MenuUnfoldOutlined v-if="collapsed" />
                <MenuFoldOutlined v-else />
              </template>
             
            </a-button>
            <h3 v-if="!collapsed">
              章节列表 <span class="chapter-count">共{{ totalChapters }}章</span>
            </h3>
          </div>
        </div>
      </template>

      <template #extra>
        <a-button 
          v-if="!collapsed"
          @click="$emit('detectChapters')" 
          :loading="detectingChapters" 
          size="small"
        >
          🔍 重置
        </a-button>
      </template>

      <!-- 章节列表内容 -->
      <div v-show="!collapsed" class="chapter-content">
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
            :key="String(chapter.id)"
            class="chapter-menu-item"
          >
            <div class="chapter-item-content">
              <div class="chapter-main">
                <div class="chapter-number">第{{ chapter.chapter_number }}章</div>
                <div class="chapter-title">{{ chapter.chapter_title }}</div>
              </div>
            </div>
          </a-menu-item>
        </a-menu>

          <!-- 加载更多按钮 -->
          <div v-if="hasMore" class="load-more-section">
            <a-button
              type="default"
              size="small"
              @click="loadMore"
              :loading="loading"
              block
            >
              点击加载更多 (还有 {{ filteredChapters.length - displayedCount }} 章)
            </a-button>
          </div>
          
          <!-- 显示统计信息 -->
          <div v-if="filteredChapters.length > 0" class="chapter-stats">
            已显示 {{ Math.min(displayedCount, filteredChapters.length) }} / {{ filteredChapters.length }} 章
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
  import { ref, computed, watch, onMounted } from 'vue'
  import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons-vue'
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
    'update:total-chapters',
    'toggle-collapse'
  ])

  // 分页配置
  const pageSize = ref(50) // 每次加载50个章节
  const displayedCount = ref(50) // 当前显示的章节数量

  // 响应式数据
  const loading = ref(false)
  const searchKeyword = ref('')
  const chapters = ref([])
  const totalChapters = ref(0)
  const selectedKeys = ref([])
  const collapsed = ref(false) // 收起状态

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
    return filteredChapters.value.slice(0, displayedCount.value)
  })

  // 是否还有更多章节可以加载
  const hasMore = computed(() => {
    return displayedCount.value < filteredChapters.value.length
  })

  // 方法
  const loadChapters = async () => {
    if (!props.bookId) return

    loading.value = true

    try {
      const response = await booksAPI.getBookChapters(props.bookId, {
        skip: 0,
        limit: 10000, // 一次性加载所有章节
        exclude_content: true,
        sort_by: 'chapter_number',
        sort_order: 'asc'
      })

      if (response.data?.success) {
        chapters.value = response.data.data || []
        totalChapters.value = response.data.total || 0
        emit('update:total-chapters', totalChapters.value)

        // 如果已有选中的章节ID，确保selectedKeys正确设置
        if (props.selectedChapterId) {
          selectedKeys.value = [String(props.selectedChapterId)]
        }
        // 注意：不在这里自动选中第一个章节，让父组件控制选中逻辑
      }
    } catch (error) {
      console.error('加载章节失败:', error)
      message.error('加载章节失败')
    } finally {
      loading.value = false
    }
  }

  const handleSearch = () => {
    displayedCount.value = pageSize.value // 搜索时重置显示数量
  }

  const loadMore = () => {
    displayedCount.value = Math.min(
      displayedCount.value + pageSize.value,
      filteredChapters.value.length
    )
  }

  const handleMenuSelect = ({ key }) => {
    const chapter = chapters.value.find(c => c.id == key)
    if (chapter) {
      selectedKeys.value = [key]
      emit('selectChapter', chapter)
    }
  }

  const toggleCollapse = () => {
    collapsed.value = !collapsed.value
    emit('toggle-collapse', collapsed.value)
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
        selectedKeys.value = [String(newId)]
      } else {
        selectedKeys.value = []
      }
    },
    { immediate: true }
  )

  watch(
    () => searchKeyword.value,
    () => {
      displayedCount.value = pageSize.value // 搜索变化时重置显示数量
    }
  )
</script>

<style scoped>
  .chapter-list-simple {
    height: 100%;
    overflow: hidden;
  }

  .chapter-header {
    width: 100%;
  }

  .title-section {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .collapse-btn {
    border: none;
    box-shadow: none;
    padding: 4px 8px;
  }

  .chapter-content {
    transition: all 0.3s ease;
  }

  .chapter-card {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .chapter-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .chapter-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }

  .chapter-count {
    color: var(--ant-color-text-secondary);
    font-size: 14px;
  }

  .search-section {
    margin-bottom: 16px;
  }

  .chapters-container {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .loading-state,
  .empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 32px;
  }

  .chapter-menu {
    border: none;
    background: transparent;
    flex: 1;
    overflow-y: auto;
    width: 100%;
  }

  .chapter-menu-item {
    height: auto !important;
    line-height: normal !important;
    padding: 8px 16px !important;
    margin-bottom: 4px;
    border-radius: 6px;
  }

  .chapter-menu-item:hover {
    background: var(--ant-color-bg-elevated);
  }

  .chapter-menu-item.ant-menu-item-selected {
    background: var(--ant-color-primary-1);
    color: var(--ant-color-primary);
  }

  .chapter-item-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
  }

  .chapter-main {
    display: flex;
    align-items: center;
    gap: 8px;
    overflow: hidden;
    flex: 1;
    min-width: 0;
  }

  .chapter-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }



  .chapter-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--ant-color-text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
  }

  .load-more-section {
    margin-top: 16px;
    padding: 16px;
    border-top: 1px solid var(--ant-color-border);
    background: var(--ant-color-bg-container);
  }

  .chapter-stats {
    margin-top: 8px;
    padding: 8px 16px;
    text-align: center;
    font-size: 12px;
    color: var(--ant-color-text-secondary);
    background: var(--ant-color-bg-container);
  }
</style>