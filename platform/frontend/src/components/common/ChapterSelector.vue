<template>
  <div class="chapter-selector">
    <!-- 头部控制区域 -->
    <div class="section-header">
      <div class="title-section">
        <!-- 收起/展开按钮 -->
        <a-button
          v-if="showCollapse"
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
        
        <!-- 标题 -->
        <h3 v-if="!collapsed">
          {{ title }}
          <span v-if="showChapterCount" class="chapter-count">共{{ totalChapters || chapters.length }}章</span>
        </h3>
      </div>
      
             <!-- 右侧操作按钮 -->
       <div class="header-actions">
         <!-- 更多操作下拉菜单 -->
         <a-dropdown
           v-if="(showRefresh || showReset || showSearch) && !collapsed"
           :trigger="['click']"
           placement="bottomRight"
         >
           <a-button size="small" type="text" class="more-actions-btn">
             <template #icon><MoreOutlined /></template>
           </a-button>
           <template #overlay>
             <a-menu>
               <a-menu-item
                 v-if="showSearch"
                 key="search"
                 @click="toggleSearch"
               >
                 <template #icon><SearchOutlined /></template>
                 {{ showSearchInput ? '隐藏搜索' : '搜索章节' }}
               </a-menu-item>
               <a-menu-item
                 v-if="showRefresh"
                 key="refresh"
                 @click="$emit('refresh')"
                 :disabled="loading"
               >
                 <template #icon><ReloadOutlined /></template>
                 刷新
               </a-menu-item>
               <a-menu-item
                 v-if="showReset"
                 key="reset"
                 @click="$emit('reset')"
                 :disabled="detectingChapters"
               >
                 <template #icon><SearchOutlined /></template>
                 重置
               </a-menu-item>
             </a-menu>
           </template>
         </a-dropdown>
       </div>
    </div>
    
         <!-- 章节列表内容 -->
     <div v-if="!collapsed" class="chapter-content">
       <!-- 搜索框 -->
       <div v-if="showSearch && showSearchInput" class="search-section">
         <a-input-search
           v-model:value="searchKeyword"
           placeholder="搜索章节标题..."
           @search="handleSearch"
           allowClear
           :loading="loading"
         />
       </div>
      
      <!-- 章节列表 -->
      <div class="chapters-list">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <a-spin size="large" />
          <p style="margin-top: 16px; color: #666">加载章节中...</p>
        </div>
        
        <!-- 空状态 -->
        <div v-else-if="displayedChapters.length === 0" class="empty-state">
          <a-empty
            :description="searchKeyword ? '没有找到匹配的章节' : '暂无章节数据'"
            :image="Empty.PRESENTED_IMAGE_SIMPLE"
          >
            <a-button
              v-if="showReset && !searchKeyword"
              type="primary"
              @click="$emit('reset')"
              :loading="detectingChapters"
            >
              🔍 检测章节
            </a-button>
            <a-button
              v-else-if="showRefresh"
              type="primary"
              @click="$emit('refresh')"
            >
              重新加载
            </a-button>
          </a-empty>
        </div>
        
        <!-- 章节列表 -->
        <div v-else class="chapters-container">
          <!-- 使用 Ant Menu 组件 -->
          <a-menu
            v-model:selectedKeys="selectedKeys"
            mode="inline"
            class="chapter-menu"
            @select="handleMenuSelect"
          >
            <a-menu-item
              v-for="chapter in displayedChapters"
              :key="String(chapter.id)"
              class="chapter-menu-item"
            >
              <div class="chapter-item-content">
                <div class="chapter-main">
                  <div class="chapter-number">第{{ chapter.chapter_number }}章</div>
                  <div class="chapter-title">{{ chapter.chapter_title }}</div>
                  <div class="chapter-meta">
                    <span class="word-count">{{ formatNumber(chapter.word_count || 0) }} 字</span>
                    <!-- 章节状态 - 已移除，改为在右侧标题显示 -->
                  </div>
                </div>
              </div>
            </a-menu-item>
          </a-menu>
          
                                <!-- 简单翻页控制 -->
            <div v-if="paginationType === 'page' && totalPages > 1" class="simple-pagination">
              <a-button
                size="small"
                :disabled="currentPage === 1"
                @click="prevPage"
                class="page-btn"
              >
                <template #icon><LeftOutlined /></template>
              </a-button>
              <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
              <a-button
                size="small"
                :disabled="currentPage === totalPages"
                @click="nextPage"
                class="page-btn"
              >
                <template #icon><RightOutlined /></template>
              </a-button>
            </div>
          
          <!-- 加载更多 -->
          <div v-if="paginationType === 'load-more' && hasMore" class="load-more-section">
            <a-button
              type="default"
              size="small"
              @click="$emit('load-more')"
              :loading="loadingMore"
              block
            >
              加载更多
            </a-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { 
  MenuFoldOutlined, 
  MenuUnfoldOutlined, 
  LeftOutlined, 
  RightOutlined,
  ReloadOutlined,
  MoreOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'
import { Empty } from 'ant-design-vue'

// Props
const props = defineProps({
  // 数据
  chapters: {
    type: Array,
    default: () => []
  },
  selectedChapter: {
    type: [Number, String],
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  loadingMore: {
    type: Boolean,
    default: false
  },
  detectingChapters: {
    type: Boolean,
    default: false
  },
  
  // 功能开关
  showCollapse: {
    type: Boolean,
    default: true
  },
  showSearch: {
    type: Boolean,
    default: false
  },
  showStatus: {
    type: Boolean,
    default: false
  },
  showRefresh: {
    type: Boolean,
    default: false
  },
  showReset: {
    type: Boolean,
    default: false
  },
  showChapterCount: {
    type: Boolean,
    default: false
  },
  
  // 配置
  title: {
    type: String,
    default: '选择章节'
  },
     pageSize: {
     type: Number,
     default: 50
   },
  paginationType: {
    type: String,
    default: 'page', // 'page' | 'load-more'
    validator: (value) => ['page', 'load-more'].includes(value)
  },
  
  // 收起状态
  collapsed: {
    type: Boolean,
    default: false
  },
  
  // 后端翻页相关
  totalPages: {
    type: Number,
    default: 1
  },
  currentPage: {
    type: Number,
    default: 1
  },
  totalChapters: {
    type: Number,
    default: 0
  }
})

// Emits
const emit = defineEmits([
  'select',
  'refresh',
  'reset',
  'search',
  'load-more',
  'toggle-collapse',
  'page-change'
])

// 响应式数据
const selectedKeys = ref([])
const searchKeyword = ref('')
const showSearchInput = ref(false)

// 当前页码，从props获取
const currentPage = computed(() => props.currentPage || 1)

// 计算属性
// 总页数由父组件传入，不再根据本地数据计算
const totalPages = computed(() => props.totalPages || 1)

const filteredChapters = computed(() => {
  if (!props.showSearch || !showSearchInput.value || !searchKeyword.value) {
    return props.chapters
  }
  
  const keyword = searchKeyword.value.toLowerCase()
  return props.chapters.filter(chapter => 
    chapter.chapter_title?.toLowerCase().includes(keyword) ||
    chapter.chapter_number?.toString().includes(keyword)
  )
})

const displayedChapters = computed(() => {
  // 后端翻页：直接使用传入的章节数据，不再进行前端切片
  return props.chapters
})

const hasMore = computed(() => {
  if (props.paginationType === 'load-more') {
    return displayedChapters.value.length < filteredChapters.value.length
  }
  return false
})

// 监听选中章节变化
watch(() => props.selectedChapter, (newId) => {
  selectedKeys.value = newId ? [String(newId)] : []
}, { immediate: true })

// 监听搜索关键词变化
watch(searchKeyword, (newKeyword) => {
  if (props.paginationType === 'page') {
    currentPage.value = 1 // 搜索时重置到第一页
  }
  // 只有当搜索框显示时才触发搜索事件
  if (showSearchInput.value) {
    emit('search', newKeyword)
  }
})

// 方法
const handleMenuSelect = ({ key }) => {
  const chapterId = parseInt(key)
  emit('select', chapterId)
}

const toggleCollapse = () => {
  emit('toggle-collapse')
}

const toggleSearch = () => {
  showSearchInput.value = !showSearchInput.value
  if (!showSearchInput.value) {
    // 隐藏搜索框时清空搜索关键词
    searchKeyword.value = ''
  }
}

const handleSearch = (value) => {
  searchKeyword.value = value
}

const prevPage = () => {
  if (currentPage.value > 1) {
    // 触发后端翻页事件
    emit('page-change', {
      page: currentPage.value - 1,
      pageSize: props.pageSize
    })
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    // 触发后端翻页事件
    emit('page-change', {
      page: currentPage.value + 1,
      pageSize: props.pageSize
    })
  }
}

const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

// 状态相关函数已移除，改为在右侧标题显示
</script>

<style scoped>
.chapter-selector {
  background: #fafafa;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: width 0.3s ease;
}

.section-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-btn {
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: color 0.3s ease;
}

.collapse-btn:hover {
  color: #1890ff;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.chapter-count {
  font-size: 12px;
  color: #666;
  font-weight: normal;
  margin-left: 8px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.more-actions-btn {
  padding: 4px 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: color 0.3s ease;
}

.more-actions-btn:hover {
  color: #1890ff;
}

.chapter-content {
  display: flex;
  flex-direction: column;
}

.search-section {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.chapters-list {
  flex: 1;
  overflow-y: auto;
}

.loading-state {
  padding: 40px 24px;
  text-align: center;
}

.empty-state {
  padding: 40px 24px;
  text-align: center;
}

.chapters-container {
  padding: 8px;
}

.chapter-menu {
  border: none;
  background: transparent;
}

.chapter-menu-item {
  margin-bottom: 4px;
}

/* 🔥 增强选中状态样式 */
.chapter-menu .ant-menu-item-selected {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.15), rgba(24, 144, 255, 0.1)) !important;
  border-left: 3px solid #1890ff !important;
  border-radius: 6px !important;
  transform: translateX(4px) !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2) !important;
}

.chapter-menu .ant-menu-item-selected .chapter-number {
  color: #1890ff !important;
  font-weight: 600 !important;
}

.chapter-menu .ant-menu-item-selected .chapter-title {
  color: #1890ff !important;
  font-weight: 500 !important;
}

.chapter-menu .ant-menu-item-selected .chapter-meta {
  color: rgba(24, 144, 255, 0.8) !important;
}

/* 悬停效果 */
.chapter-menu .ant-menu-item:hover {
  background: rgba(24, 144, 255, 0.05) !important;
  border-radius: 6px !important;
  transform: translateX(2px) !important;
  transition: all 0.2s ease !important;
}

.chapter-item-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chapter-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chapter-number {
  font-size: 14px;
  font-weight: 500;
  color: var(--ant-text-color);
}

.chapter-title {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
  line-height: 1.4;
}

.chapter-meta {
  font-size: 11px;
  color: var(--ant-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.word-count {
  color: var(--ant-text-color-secondary);
}

/* 状态样式已移除，改为在右侧标题显示 */

/* 简单翻页控制样式 */
.simple-pagination {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}

.page-btn {
  min-width: 32px;
  height: 28px;
  padding: 0 8px;
}

.page-info {
  font-size: 12px;
  color: #666;
  min-width: 40px;
  text-align: center;
  font-weight: 500;
}

/* 加载更多样式 */
.load-more-section {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

/* 暗黑模式适配 */
[data-theme='dark'] .chapter-selector {
  background: #2a2a2a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .section-header {
  background: #333333;
  border-bottom-color: var(--ant-border-color-split);
}

[data-theme='dark'] .section-header h3 {
  color: var(--ant-color-text);
}

[data-theme='dark'] .collapse-btn {
  color: var(--ant-color-text-secondary);
}

[data-theme='dark'] .collapse-btn:hover {
  color: var(--ant-color-primary);
}

[data-theme='dark'] .chapter-menu {
  background: var(--ant-color-bg-container);
}

[data-theme='dark'] .chapter-number {
  color: var(--ant-color-text);
}

/* 🔥 暗黑模式下的选中状态样式 */
[data-theme='dark'] .chapter-menu .ant-menu-item-selected {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.2), rgba(24, 144, 255, 0.15)) !important;
  border-left: 3px solid #1890ff !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3) !important;
}

[data-theme='dark'] .chapter-menu .ant-menu-item-selected .chapter-number {
  color: #1890ff !important;
  font-weight: 600 !important;
}

[data-theme='dark'] .chapter-menu .ant-menu-item-selected .chapter-title {
  color: #1890ff !important;
  font-weight: 500 !important;
}

[data-theme='dark'] .chapter-menu .ant-menu-item-selected .chapter-meta {
  color: rgba(24, 144, 255, 0.9) !important;
}

/* 暗黑模式下的悬停效果 */
[data-theme='dark'] .chapter-menu .ant-menu-item:hover {
  background: rgba(24, 144, 255, 0.1) !important;
}

[data-theme='dark'] .chapter-title {
  color: var(--ant-color-text-secondary);
}

[data-theme='dark'] .chapter-meta {
  color: var(--ant-color-text-tertiary);
}

[data-theme='dark'] .word-count {
  color: var(--ant-color-text-tertiary);
}

/* 暗黑模式状态样式已移除，改为在右侧标题显示 */

/* 暗黑模式简单翻页控制 */
[data-theme='dark'] .simple-pagination {
  background: var(--ant-color-bg-container);
  border-top-color: var(--ant-color-border);
}

[data-theme='dark'] .page-info {
  color: var(--ant-color-text-secondary);
}

[data-theme='dark'] .load-more-section {
  background: var(--ant-color-bg-container);
  border-top-color: var(--ant-color-border);
}
</style>

