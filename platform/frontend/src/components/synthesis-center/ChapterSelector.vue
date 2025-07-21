<template>
  <div class="chapter-selection-area">
    <!-- 章节选择控制 -->
    <div class="chapter-controls">
      <span class="control-title">选择章节</span>
      <a-button @click="$emit('loadChapters')" :loading="loading" size="small" type="text">
        <template #icon><ReloadOutlined /></template>
        刷新
      </a-button>
    </div>

    <!-- 章节列表 -->
    <div class="chapters-list">
      <div v-if="loading" class="loading-state">
        <a-spin size="large" />
        <p style="margin-top: 16px; color: #666">加载章节中...</p>
      </div>

      <!-- 有章节数据时显示章节列表 -->
      <div v-else-if="chapters.length > 0" class="chapters-container">
        <div
          v-for="chapter in chapters"
          :key="chapter.id"
          :class="['chapter-menu-item', { active: selectedChapter === chapter.id }]"
          @click="$emit('select', chapter.id)"
        >
          <div class="chapter-info">
            <div class="chapter-title">第{{ chapter.chapter_number }}章 {{ chapter.chapter_title }}</div>
            <div class="chapter-meta">
              <span class="word-count">{{ formatNumber(chapter.word_count || 0) }} 字</span>
              <span class="chapter-status" :class="getChapterStatusClass(chapter)">
                {{ getChapterStatusText(chapter) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-chapters">
        <a-empty description="暂无章节数据" :image="Empty.PRESENTED_IMAGE_SIMPLE">
          <a-button type="primary" @click="$emit('loadChapters')">重新加载</a-button>
        </a-empty>
      </div>
    </div>

    <!-- 直接文本项目提示 -->
    <div class="text-project-hint"></div>
  </div>
</template>

<script setup>
  import { ReloadOutlined } from '@ant-design/icons-vue'
  import { Empty } from 'ant-design-vue'

  defineProps({
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
    }
  })

  defineEmits(['select', 'loadChapters'])

  const formatNumber = (num) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + '万'
    }
    return num.toString()
  }

  const getChapterStatusText = (chapter) => {
    const status = chapter.analysis_status || 'pending'
    const statusMap = {
      pending: '待分析',
      processing: '分析中',
      completed: '已完成',
      failed: '分析失败',
      ready: '准备就绪'
    }
    return statusMap[status] || '未知'
  }

  const getChapterStatusClass = (chapter) => {
    const status = chapter.analysis_status || 'pending'
    return `status-${status}`
  }
</script>

<style scoped>
  .chapter-selection-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .chapter-controls {
    padding: 12px 24px;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #fafafa;
  }

  .chapters-list {
    flex: 1;
    overflow-y: auto;
  }

  .loading-state {
    padding: 40px 24px;
    text-align: center;
  }

  .chapters-container {
    padding: 8px;
  }

  .chapter-menu-item {
    padding: 12px 16px;
    margin-bottom: 8px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid #e8e8e8;
    background: #fafafa;
  }

  .chapter-menu-item:hover {
    background: #f0f6ff;
    border-color: #91caff;
    transform: translateY(-1px);
  }

  .chapter-menu-item.active {
    background: #e6f4ff;
    border-color: #1890ff;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
  }

  .chapter-menu-item.active .chapter-title {
    color: #1890ff;
    font-weight: 600;
  }

  .chapter-info {
    flex: 1;
    min-width: 0;
  }

  .chapter-title {
    font-size: 14px;
    font-weight: 500;
    color: #1f2937;
    line-height: 1.4;
    margin-bottom: 4px;
  }

  .chapter-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 12px;
  }

  .word-count {
    color: #666;
  }

  .chapter-status {
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
  }

  .status-pending {
    background: #fff7e6;
    color: #fa8c16;
  }

  .status-processing {
    background: #e6f7ff;
    color: #1890ff;
  }

  .status-completed {
    background: #f6ffed;
    color: #52c41a;
  }

  .status-failed {
    background: #fff2f0;
    color: #ff4d4f;
  }

  .status-ready {
    background: #f0f5ff;
    color: #2f54eb;
  }

  .empty-chapters {
    padding: 40px 24px;
    text-align: center;
  }

  .text-project-hint {
    padding: 24px;
  }

  /* 暗黑模式适配 */
  [data-theme='dark'] .chapter-selection-area {
    background: #1f1f1f !important;
  }

  [data-theme='dark'] .chapter-controls {
    background: #2d2d2d !important;
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .chapter-menu-item {
    background: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .chapter-menu-item:hover {
    background: #3a3a3a !important;
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .chapter-menu-item.active {
    background: rgba(var(--primary-color-rgb), 0.1) !important;
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .chapter-menu-item.active .chapter-title {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .chapter-title {
    color: #fff !important;
  }

  [data-theme='dark'] .word-count {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .status-pending {
    background: rgba(250, 140, 22, 0.1) !important;
    color: #fa8c16 !important;
  }

  [data-theme='dark'] .status-processing {
    background: rgba(24, 144, 255, 0.1) !important;
    color: #1890ff !important;
  }

  [data-theme='dark'] .status-completed {
    background: rgba(82, 196, 26, 0.1) !important;
    color: #52c41a !important;
  }

  [data-theme='dark'] .status-failed {
    background: rgba(255, 77, 79, 0.1) !important;
    color: #ff4d4f !important;
  }

  [data-theme='dark'] .status-ready {
    background: rgba(47, 84, 235, 0.1) !important;
    color: #2f54eb !important;
  }

  /* 移动端响应式设计 */
  @media (max-width: 768px) {
    .chapter-selection-area {
      flex-direction: row;
      max-height: 120px;
      overflow-x: auto;
      overflow-y: hidden;
    }

    .chapter-controls {
      flex: 0 0 auto;
      padding: 8px 12px;
      border-bottom: none;
      border-right: 1px solid #f0f0f0;
      min-width: 120px;
      background: #f8f9fa;
    }

    .chapters-list {
      flex: 1;
      overflow-x: auto;
      overflow-y: hidden;
    }

    .chapters-container {
      display: flex;
      gap: 8px;
      padding: 8px;
      min-width: max-content;
    }

    .chapter-menu-item {
      flex: 0 0 auto;
      min-width: 200px;
      margin-bottom: 0;
      padding: 8px 12px;
    }

    .chapter-title {
      font-size: 13px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .chapter-meta {
      gap: 8px;
    }

    .loading-state {
      padding: 20px 12px;
    }

    .empty-chapters {
      padding: 20px 12px;
    }

    .text-project-hint {
      padding: 12px;
    }
  }

  @media (max-width: 480px) {
    .chapter-controls {
      min-width: 100px;
      padding: 6px 8px;
    }

    .chapter-menu-item {
      min-width: 180px;
      padding: 6px 10px;
    }

    .chapter-title {
      font-size: 12px;
    }

    .chapter-meta {
      font-size: 11px;
    }

    .chapter-status {
      font-size: 10px;
      padding: 1px 4px;
    }
  }

  /* 移动端暗黑模式适配 */
  @media (max-width: 768px) {
    [data-theme='dark'] .chapter-controls {
      background: #2d2d2d !important;
      border-right-color: #434343 !important;
    }
  }
</style>
