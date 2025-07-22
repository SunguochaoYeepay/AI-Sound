<template>
  <div class="chapter-detail">
    <a-card :bordered="false" class="detail-card">
      <!-- 章节标题和操作 -->
      <template #title>
        <div v-if="chapter" class="chapter-header">
          <div class="chapter-info">
            <h2 class="chapter-title">第{{ chapter.chapter_number }}章 {{ chapter.chapter_title }}</h2>
          </div>
          <div class="chapter-actions">
            <a-radio-group v-model:value="activeView" button-style="solid" size="small">
              <a-radio-button value="content"> 📝 原文内容 </a-radio-button>
              <a-radio-button value="analysis"> 🤖 智能准备结果 </a-radio-button>
            </a-radio-group>
          </div>
        </div>
      </template>

      <!-- 内容区域 -->
      <div class="content-container">
        <!-- 原文内容 -->
        <chapter-content
          v-if="activeView === 'content'"
          :chapter="chapter"
          @save="handleContentSave"
        />

        <!-- 智能准备结果 -->
        <chapter-analysis
          v-if="activeView === 'analysis'"
          :chapter="chapter"
          :analysis-data="analysisData"
          :loading="loadingAnalysis"
          :preparing-chapter="preparingChapter"
          :preparation-status="chapterPreparationStatus"
          @refresh="handlePrepareChapter"
          @save="handleAnalysisSave"
        />
      </div>
    </a-card>
  </div>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import { message } from 'ant-design-vue'
  import ChapterContent from './ChapterContent.vue'
  import ChapterAnalysis from './ChapterAnalysis.vue'
  import { booksAPI } from '../api'

  const props = defineProps({
    chapter: {
      type: Object,
      default: null
    },
    chapterPreparationStatus: {
      type: Object,
      default: null
    },
    preparingChapter: {
      type: Boolean,
      default: false
    }
  })

  const emit = defineEmits(['prepare', 'save-content', 'save-analysis'])

  const activeView = ref('analysis')
  const loadingAnalysis = ref(false)
  const analysisData = ref(null)

  // 加载分析数据 - 总是获取最新数据
  const loadAnalysisData = async () => {
    if (!props.chapter?.id) return

    loadingAnalysis.value = true
    try {
      // 🔥 强制刷新：总是获取最新数据，不使用缓存
      const response = await booksAPI.getPreparationResult(props.chapter.id, { force_refresh: true })
      if (response.data && response.data.success) {
        analysisData.value = response.data.data
        console.log('[ChapterDetail] 加载最新分析数据成功')
      } else {
        analysisData.value = null
        message.error(response.data?.message || '加载分析数据失败')
      }
    } catch (error) {
      console.error('加载分析数据失败:', error)
      message.error('加载分析数据失败')
      analysisData.value = null
    } finally {
      loadingAnalysis.value = false
    }
  }

  // 监听章节变化
  watch(
    () => props.chapter?.id,
    async (newId) => {
      try {
        if (newId) {
          await loadAnalysisData()
        } else {
          analysisData.value = null
        }
      } catch (error) {
        console.error('加载分析数据失败:', error)
        message.error('加载分析数据失败')
        analysisData.value = null
      }
    },
    { immediate: true }
  )

  // 处理智能准备
  const handlePrepareChapter = () => {
    emit('prepare')
  }

  // 处理内容保存
  const handleContentSave = (content) => {
    emit('save-content', content)
  }

  // 处理分析结果保存
  const handleAnalysisSave = (data) => {
    emit('save-analysis', data)
  }

  // 监听视图切换
  watch(activeView, (newView) => {
    if (newView === 'analysis') {
      loadAnalysisData()
    }
  })
</script>

<style scoped>
  .chapter-detail {
    height: 100%;
    overflow: hidden;
  }

  .detail-card {
    height: 100%;

    :deep(.ant-card-body) {
      height: calc(100% - 57px);
      padding: 12px;
      overflow: hidden;
    }
  }

  .chapter-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .chapter-info {
    flex: 1;
    min-width: 0;
  }

  .chapter-title {
    margin: 0;
    font-size: 18px;
    line-height: 1.4;
    color: var(--primary-color);
  }

  .chapter-meta {
    margin-top: 4px;
  }

  .chapter-actions {
    display: flex;
    align-items: center;
    gap: 8px;

    .ant-radio-group {
      display: flex;
      gap: 4px;
    }

    .ant-radio-button-wrapper {
      padding: 0 12px;

      &.ant-radio-button-wrapper-checked {
        background: var(--primary-color);
        border-color: var(--primary-color);

        &:hover {
          background: var(--primary-color);
          border-color: var(--primary-color);
        }
      }
    }
  }

  .content-container {
    height: 100%;
    overflow: hidden;
  }
</style>
