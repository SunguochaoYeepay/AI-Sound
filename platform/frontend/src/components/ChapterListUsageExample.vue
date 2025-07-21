<template>
  <div class="chapter-list-container">
    <VirtualChapterList
      :chapters="displayChapters"
      :selected-chapter-id="selectedChapterId"
      :chapter-preparation-status="chapterPreparationStatus"
      :preparing-chapters="preparingChapters"
      :detecting-chapters="detectingChapters"
      :loading="loading"
      :total="totalChapters"
      :page-size="pageSize"
      @select-chapter="handleSelectChapter"
      @detect-chapters="handleDetectChapters"
      @load-more="handleLoadMore"
      @search="handleSearch"
      ref="virtualListRef"
    />
  </div>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import VirtualChapterList from './VirtualChapterList.vue'
  import { message } from 'ant-design-vue'

  // 组件引用
  const virtualListRef = ref(null)

  // 状态管理
  const allChapters = ref([])
  const displayChapters = ref([])
  const selectedChapterId = ref(null)
  const chapterPreparationStatus = ref({})
  const preparingChapters = ref(new Set())
  const detectingChapters = ref(false)
  const loading = ref(false)
  const totalChapters = ref(0)
  const pageSize = ref(100)
  const currentPage = ref(1)
  const searchKeyword = ref('')

  // 模拟API调用
  const fetchChapters = async (page = 1, keyword = '', append = false) => {
    try {
      loading.value = true

      // 模拟API延迟
      await new Promise((resolve) => setTimeout(resolve, 500))

      // 模拟数据
      const mockData = []
      const startIndex = (page - 1) * pageSize.value
      const endIndex = Math.min(startIndex + pageSize.value, 8000) // 模拟8000章节

      for (let i = startIndex; i < endIndex; i++) {
        mockData.push({
          id: i + 1,
          number: i + 1,
          title: keyword
            ? `第${i + 1}章：${keyword}相关的章节标题`
            : `第${i + 1}章：这是测试章节标题${i + 1}`,
          wordCount: Math.floor(Math.random() * 5000) + 1000,
          status: Math.random() > 0.5 ? 'completed' : 'pending',
          createdAt: new Date(Date.now() - Math.random() * 86400000 * 30).toISOString()
        })
      }

      if (append) {
        displayChapters.value.push(...mockData)
      } else {
        displayChapters.value = mockData
      }

      totalChapters.value = 8000
      currentPage.value = page
    } catch (error) {
      console.error('获取章节失败:', error)
      message.error('获取章节失败')
    } finally {
      loading.value = false
    }
  }

  // 事件处理
  const handleSelectChapter = (chapter) => {
    selectedChapterId.value = chapter.id
    console.log('选中章节:', chapter)
    // 这里可以触发章节详情加载等操作
  }

  const handleDetectChapters = async () => {
    detectingChapters.value = true
    try {
      // 模拟章节检测
      await new Promise((resolve) => setTimeout(resolve, 2000))
      await fetchChapters(1, '', false)
      message.success('章节检测完成')
    } catch (error) {
      console.error('章节检测失败:', error)
      message.error('章节检测失败')
    } finally {
      detectingChapters.value = false
    }
  }

  const handleLoadMore = async ({ page, keyword }) => {
    console.log('加载更多:', { page, keyword })
    await fetchChapters(page, keyword, true)
  }

  const handleSearch = async ({ keyword }) => {
    searchKeyword.value = keyword
    console.log('搜索:', keyword)
    await fetchChapters(1, keyword, false)

    // 重置虚拟滚动位置
    if (virtualListRef.value) {
      virtualListRef.value.resetScroll()
    }
  }

  // 模拟准备状态更新
  const updatePreparationStatus = () => {
    const status = {}
    displayChapters.value.forEach((chapter) => {
      const rand = Math.random()
      if (rand < 0.3) {
        status[chapter.id] = { preparation_complete: true }
      } else if (rand < 0.6) {
        status[chapter.id] = { preparation_started: true }
      }
    })
    chapterPreparationStatus.value = status
  }

  // 初始化
  onMounted(async () => {
    await fetchChapters(1, '', false)
    updatePreparationStatus()

    // 模拟定期更新准备状态
    setInterval(updatePreparationStatus, 10000)
  })

  // 暴露给父组件的方法
  defineExpose({
    refresh: () => fetchChapters(1, searchKeyword.value, false),
    scrollToChapter: (chapterId) => {
      if (virtualListRef.value) {
        virtualListRef.value.scrollToChapter(chapterId)
      }
    }
  })
</script>

<style scoped>
  .chapter-list-container {
    height: 100vh;
    padding: 16px;
  }

  @media (max-width: 768px) {
    .chapter-list-container {
      padding: 8px;
    }
  }
</style>
