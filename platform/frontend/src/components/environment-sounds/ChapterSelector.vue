<template>
  <div class="chapter-selector">
    <div class="section-header">
      <h3>选择章节</h3>
    </div>
    
    <!-- 使用标准 Ant Menu 组件 -->
    <a-menu
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

const props = defineProps({
  chapters: {
    type: Array,
    default: () => []
  },
  selectedChapterId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['select-chapter'])

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
</script>

<style scoped>
.chapter-selector {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--ant-text-color);
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
</style>
