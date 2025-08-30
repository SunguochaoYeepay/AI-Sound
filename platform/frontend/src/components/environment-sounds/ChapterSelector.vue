<template>
  <div class="chapter-selector">
    <div class="section-header">
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
        <h3 v-if="!collapsed">选择章节</h3>
      </div>
    </div>
    
    <!-- 使用标准 Ant Menu 组件 -->
    <a-menu
      v-if="!collapsed"
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
            </div>
          </div>
        </div>
      </a-menu-item>
    </a-menu>

    <!-- 翻页控制 -->
    <div v-if="!collapsed && chapters.length > pageSize" class="pagination-controls">
      <div class="pagination-info">
        显示 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, chapters.length) }} / {{ chapters.length }} 章
      </div>
      <div class="pagination-buttons">
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
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { MenuFoldOutlined, MenuUnfoldOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  chapters: {
    type: Array,
    default: () => []
  },
  selectedChapterId: {
    type: Number,
    default: null
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select-chapter', 'toggle-collapse'])

// 使用ref而不是computed来避免readonly警告
const selectedKeys = ref([])

// 🔥 翻页功能
const pageSize = 10 // 每页显示10个章节
const currentPage = ref(1)

// 计算总页数
const totalPages = computed(() => Math.ceil(props.chapters.length / pageSize))

// 计算当前页显示的章节
const displayedChapters = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return props.chapters.slice(start, end)
})

// 翻页方法
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

// 监听selectedChapterId变化，更新selectedKeys
watch(() => props.selectedChapterId, (newId) => {
  selectedKeys.value = newId ? [String(newId)] : []
}, { immediate: true })

const handleMenuSelect = ({ key }) => {
  const chapterId = parseInt(key)
  emit('select-chapter', chapterId)
}

const formatNumber = (num) => {
  return num.toLocaleString()
}

const toggleCollapse = () => {
  emit('toggle-collapse')
}
</script>

<style scoped>
.chapter-selector {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: width 0.3s ease;
}

.section-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
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
}

/* 暗色主题适配 */
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

/* 🔥 翻页控制样式 */
.pagination-controls {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.pagination-info {
  color: #666;
}

.pagination-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-btn {
  min-width: 32px;
  height: 24px;
  padding: 0 8px;
}

.page-info {
  font-size: 12px;
  color: #666;
  min-width: 40px;
  text-align: center;
}

/* 暗黑模式翻页控制 */
[data-theme='dark'] .pagination-controls {
  background: var(--ant-color-bg-container);
  border-top-color: var(--ant-color-border);
}

[data-theme='dark'] .pagination-info,
[data-theme='dark'] .page-info {
  color: var(--ant-color-text-secondary);
}
</style>
