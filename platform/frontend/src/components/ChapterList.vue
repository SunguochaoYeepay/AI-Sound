<template>
  <div class="chapter-list">
    <a-card :bordered="false" class="chapter-card">
      <template #title>
        <div class="chapter-header">
          <h3>📚 章节列表  <span class="chapter-count">共{{ chapters.length }}章</span></h3>
          <!-- <a-badge :count="chapters.length" :offset="[10, 0]">
            <span class="chapter-count">共{{ chapters.length }}章</span>
          </a-badge> -->
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
        />
      </div>

      <!-- 章节列表 -->
      <div class="chapters-container">
        <div v-if="filteredChapters.length === 0" class="empty-state">
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

        <div v-else class="chapters-list">
          <div
            v-for="chapter in filteredChapters"
            :key="chapter.id"
            class="chapter-item"
            :class="{ 
              'chapter-active': selectedChapterId === chapter.id,
              'chapter-prepared': chapterPreparationStatus[chapter.id]?.preparation_complete
            }"
            @click="selectChapter(chapter)"
          >
            <div class="chapter-main">
              <div class="chapter-number">第{{ chapter.number }}章</div>
              <div class="chapter-title">{{ chapter.title }}</div>
            </div>
            
            <div class="chapter-meta">
              <div class="chapter-stats">
                <span class="word-count">{{ chapter.wordCount || 0 }} 字</span>
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
                <a-tag v-else color="default" size="small">
                  未准备
                </a-tag>
              </div>
            </div>

            <!-- 操作按钮 -->
            <!-- <div class="chapter-actions" @click.stop>
              <a-tooltip :title="chapterPreparationStatus[chapter.id]?.preparation_complete ? '重新准备' : '智能准备'">
                <a-button 
                  :type="chapterPreparationStatus[chapter.id]?.preparation_complete ? 'default' : 'primary'"
                  size="small"
                  @click="$emit('prepareChapter', chapter)"
                  :loading="preparingChapters.has(chapter.id)"
                >
                  {{ chapterPreparationStatus[chapter.id]?.preparation_complete ? '🔄' : '🎭' }}
                </a-button>
              </a-tooltip>
            </div> -->
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

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
  }
})

const emit = defineEmits(['selectChapter', 'prepareChapter', 'detectChapters'])

const searchKeyword = ref('')

const filteredChapters = computed(() => {
  // 🔧 首先确保章节按照chapter_number排序
  const sortedChapters = [...props.chapters].sort((a, b) => {
    // 兼容不同的字段名称
    const aNum = parseInt(a.number || a.chapter_number) || 0
    const bNum = parseInt(b.number || b.chapter_number) || 0
    return aNum - bNum
  })
  
  // 然后进行搜索过滤
  if (!searchKeyword.value) return sortedChapters
  
  const keyword = searchKeyword.value.toLowerCase()
  return sortedChapters.filter(chapter => 
    chapter.title.toLowerCase().includes(keyword) ||
    (chapter.number || chapter.chapter_number).toString().includes(keyword)
  )
})

const selectChapter = (chapter) => {
  emit('selectChapter', chapter)
}

const handleSearch = (value) => {
  searchKeyword.value = value
}

const handleSearchChange = (e) => {
  searchKeyword.value = e.target.value
}

const getPreparationStatusColor = (status) => {
  if (status.preparation_complete) return 'green'
  if (status.preparation_started) return 'blue'
  return 'default'
}

const getPreparationStatusText = (status) => {
  if (status.preparation_complete) return '已准备'
  if (status.preparation_started) return '准备中'
  return '未准备'
}

// 监听章节变化，自动选中第一个章节
watch(() => props.chapters, (newChapters) => {
  if (newChapters.length > 0 && !props.selectedChapterId) {
    emit('selectChapter', newChapters[0])
  }
}, { immediate: true })
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