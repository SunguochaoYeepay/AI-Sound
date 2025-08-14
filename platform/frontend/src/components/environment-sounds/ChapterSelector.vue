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
        v-for="chapter in chapters"
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
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons-vue'

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

[data-theme='dark'] .chapter-title {
  color: var(--ant-color-text-secondary);
}

[data-theme='dark'] .chapter-meta {
  color: var(--ant-color-text-tertiary);
}
</style>
