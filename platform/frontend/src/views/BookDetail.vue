<template>
  <div class="book-detail-container">
    <!-- Loading状态 -->
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载书籍详情中...">
        <div style="height: 200px"></div>
      </a-spin>
    </div>

    <!-- 书籍详情内容 -->
    <div v-else-if="book" class="detail-content">
      <!-- 顶部书籍信息卡片 -->
      <BookHeaderCard
        :book="book"
        :chapter-count="chapters.length"
        :show-details="false"
        @go-back="goBack"
        @edit-book="editBook"
        @create-project="createProject"
        @open-character-management="openCharacterManagement"
      />

      <!-- 主要内容区域 -->
      <div class="main-content">
        <a-row :gutter="24">
          <!-- 左侧：章节列表 -->
          <a-col :span="chapterListCollapsed ? 1 : 4" class="chapter-list-col">
            <div class="chapter-list-container">
              <ChapterSelector
                :chapters="chapters"
                :selected-chapter="selectedChapterId"
                :loading="chaptersLoading"
                :detecting-chapters="detectingChapters"
                :show-collapse="true"
                :show-search="true"
                :show-status="true"
                :show-refresh="true"
                :show-reset="true"
                :show-chapter-count="true"
                :pagination-type="'page'"
                :page-size="50"
                :current-page="currentPage"
                :total-pages="totalPages"
                :total-chapters="totalChapters"
                title="章节列表"
                @select="selectChapter"
                @reset="detectChapters"
                @refresh="loadChapters"
                @page-change="handlePageChange"
                @toggle-collapse="toggleChapterList"
              />
            </div>
          </a-col>

          <!-- 右侧：章节详情 -->
          <a-col :span="chapterListCollapsed ? 23 : 20">
            <ChapterDetail
              :chapter="selectedChapter"
              :chapter-preparation-status="selectedChapterPreparationStatus"
              :preparing-chapter="preparingChapters.has(selectedChapter?.id)"
              @prepare="prepareSelectedChapter"
              @save-content="handleContentChanged"
              @save-analysis="saveAnalysis"
            />
          </a-col>
        </a-row>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-content">
      <a-result status="404" title="书籍不存在" sub-title="抱歉，您访问的书籍不存在或已被删除">
        <template #extra>
          <a-button type="primary" @click="goBack">返回列表</a-button>
        </template>
      </a-result>
    </div>

    <!-- 角色管理抽屉已移除，改为直接跳转到角色配音页面 -->
  </div>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { message, Modal } from 'ant-design-vue'
  import { booksAPI } from '@/api'
  import BookHeaderCard from '@/components/BookHeaderCard.vue'
  import ChapterSelector from '@/components/common/ChapterSelector.vue'
  import ChapterDetail from '@/components/ChapterDetail.vue'
  // 移除CharacterManagement组件引用，改为直接跳转到角色配音页面

  const router = useRouter()
  const route = useRoute()

  // 响应式数据
  const loading = ref(true)
  const detectingChapters = ref(false)
  const preparingChapters = ref(new Set())
  const chapterPreparationStatus = ref({})
  // characterManagementVisible已移除，改为直接跳转
  const chapterListCollapsed = ref(false) // 章节列表收起状态

  const book = ref(null)
  const chapters = ref([])
  const selectedChapterId = ref(null)

  // 计算属性
  const selectedChapter = computed(() => {
    return chapters.value.find((c) => c.id === selectedChapterId.value) || null
  })

  const selectedChapterPreparationStatus = computed(() => {
    return selectedChapterId.value ? chapterPreparationStatus.value[selectedChapterId.value] : null
  })

  // 页面初始化
  onMounted(() => {
    loadBook()
  })

  // 加载书籍信息
  const loadBook = async () => {
    const bookId = route.params.id
    if (!bookId) {
      message.error('书籍ID不存在')
      return
    }

    loading.value = true
    try {
      const response = await booksAPI.getBookDetail(bookId)
      if (response.data && response.data.success) {
        book.value = response.data.data
        await loadChapters()
      } else {
        message.error('加载书籍失败')
      }
    } catch (error) {
      console.error('加载书籍失败:', error)
      message.error('加载书籍失败')
    } finally {
      loading.value = false
    }
  }

  // 响应式数据 - 翻页相关
  const currentPage = ref(1)
  const totalPages = ref(1)
  const totalChapters = ref(0)
  const chaptersLoading = ref(false)

  // 加载章节列表
  const loadChapters = async (page = 1) => {
    if (!book.value?.id) return

    try {
      chaptersLoading.value = true
      const response = await booksAPI.getBookChapters(book.value.id, {
        page: page,
        page_size: 50, // 每页50条
        sort_by: 'chapter_number',
        sort_order: 'asc',
        exclude_content: false
      })
      
      if (response.data && response.data.success) {
        const chaptersData = response.data.data || []
        chapters.value = chaptersData.map((chapter) => ({
          id: chapter.id,
          number: chapter.chapter_number,
          title: chapter.chapter_title || `第${chapter.chapter_number}章`,
          wordCount: chapter.word_count || 0,
          status: chapter.analysis_status,
          content: chapter.content,
          book_id: book.value.id,
          chapter_number: chapter.chapter_number,
          chapter_title: chapter.chapter_title || `第${chapter.chapter_number}章`
        }))

        // 更新分页信息
        if (response.data.pagination) {
          currentPage.value = response.data.pagination.page || page
          totalPages.value = response.data.pagination.total_pages || 1
          totalChapters.value = response.data.pagination.total || 0
        }

        // 如果是第一页且有章节数据，选中第一个章节
        if (page === 1 && !selectedChapterId.value && chapters.value.length > 0) {
          selectedChapterId.value = chapters.value[0].id
          await loadChapterPreparationStatus(selectedChapterId.value)
        }

        console.log('📊 章节加载完成，当前页:', currentPage.value, '总页数:', totalPages.value)
      }
    } catch (error) {
      console.error('加载章节失败:', error)
    } finally {
      chaptersLoading.value = false
    }
  }

  // 处理翻页
  const handlePageChange = async (pageInfo) => {
    await loadChapters(pageInfo.page)
  }

  // 更新总章节数
  const updateTotalChapters = (total) => {
    console.log('总章节数更新为:', total)
  }

  // 加载单个章节的智能准备状态（按需加载）
  const loadChapterPreparationStatus = async (chapterId) => {
    if (!chapterId) return

    try {
      const response = await booksAPI.getPreparationStatus(chapterId)
      if (response.data?.success) {
        chapterPreparationStatus.value = {
          ...chapterPreparationStatus.value,
          [chapterId]: response.data.data
        }
      }
    } catch (error) {
      console.error(`加载章节${chapterId}状态失败:`, error)
      chapterPreparationStatus.value = {
        ...chapterPreparationStatus.value,
        [chapterId]: { preparation_complete: false, preparation_started: false }
      }
    }
  }

  // 批量加载指定章节的智能准备状态（可选优化）
  const loadSelectedChaptersPreparationStatus = async (chapterIds) => {
    if (!chapterIds?.length) return

    try {
      const response = await booksAPI.getChaptersPreparationStatus(book.value?.id, {
        chapter_ids: chapterIds
      })
      
      if (response.data?.success) {
        const statusMap = response.data.data || {}
        chapterPreparationStatus.value = {
          ...chapterPreparationStatus.value,
          ...statusMap
        }
      }
    } catch (error) {
      console.error('批量加载章节状态失败:', error)
    }
  }

  // 选择章节 - 按需加载准备状态
  const selectChapter = async (chapterId) => {
    selectedChapterId.value = chapterId
    
    // 🔥 优化：选择章节时加载该章节的准备状态
    if (chapterId) {
      await loadChapterPreparationStatus(chapterId)
    }
  }

  // 章节检测
  const detectChapters = async (forceReprocess = false) => {
    if (!book.value?.id) return

    detectingChapters.value = true
    try {
      const response = await booksAPI.detectChapters(book.value.id, { force_reprocess: forceReprocess })
      if (response.data && response.data.success) {
        message.success('章节检测完成')
        await Promise.all([loadChapters(), loadBook()])
      }
    } catch (error) {
      console.error('章节检测失败:', error)
      
      // 🔥 修复：如果是因为已有章节导致的错误，提示用户是否强制重新处理
      if (error.response?.status === 400 && error.response?.data?.message?.includes('force_reprocess=true')) {
        Modal.confirm({
          title: '检测到已有章节',
          content: '书籍已有章节数据，是否强制重新检测？这将覆盖现有的章节信息。',
          okText: '强制重新检测',
          cancelText: '取消',
          onOk: () => {
            detectChapters(true)
          }
        })
      } else {
        message.error('章节检测失败')
      }
    } finally {
      detectingChapters.value = false
    }
  }

  // 智能准备章节
  const prepareChapterForSynthesis = async (chapter, isRerun = false) => {
    if (!chapter?.id) return

    preparingChapters.value.add(chapter.id)
    try {
      const response = await booksAPI.prepareChapterForSynthesis(chapter.id, {
        force_reprocess: isRerun
      })
      if (response.data && response.data.success) {
        message.success(`章节 "${chapter.title}" 智能准备完成`)
        // 更新章节准备状态
        await loadChapterPreparationStatus(chapter.id)
        // 如果是当前选中的章节，加载分析数据
        if (selectedChapterId.value === chapter.id) {
          // loadAnalysisData(chapter.id) // Removed as per edit hint
        }
      }
    } catch (error) {
      console.error('章节准备失败:', error)
      message.error('章节准备失败')
    } finally {
      preparingChapters.value.delete(chapter.id)
    }
  }

  // 准备选中的章节
  const prepareSelectedChapter = () => {
    if (selectedChapter.value) {
      prepareChapterForSynthesis(selectedChapter.value)
    }
  }



  // 章节列表收起展开切换
  const toggleChapterList = () => {
    chapterListCollapsed.value = !chapterListCollapsed.value
  }

  // 处理章节列表收起/展开
  const handleChapterListToggle = (collapsed) => {
    chapterListCollapsed.value = collapsed
  }

  // 页面操作
  const goBack = () => {
    router.push('/books')
  }

  const editBook = () => {
    router.push(`/books/edit/${route.params.id}`)
  }

  const createProject = () => {
    router.push(`/novel-reader/create?bookId=${route.params.id}`)
  }

  const openCharacterManagement = () => {
    // 直接跳转到角色配音页面，并带上书籍ID作为查询条件
    router.push({
      name: 'Characters',
      query: { bookId: book.value?.id, bookTitle: book.value?.title }
    })
  }

  const openCharacterConfig = (chapter) => {
    console.log('配置章节角色:', chapter)
    // 这里可以实现章节角色配置功能
  }

  const handleContentChanged = (content) => {
    console.log('章节内容已修改:', selectedChapter.value, content)
    // 这里可以实现章节内容保存功能
  }

  const refreshAnalysis = (chapter) => {
    // Removed as per edit hint
  }

  const saveAnalysis = async (data) => {
    if (!selectedChapter.value?.id) {
      message.error('请先选择章节')
      return
    }

    try {
      console.log('📥 BookDetail收到保存事件:', {
        chapterId: selectedChapter.value.id,
        chapterTitle: selectedChapter.value.title,
        dataReceived: !!data,
        dataType: typeof data
      })

      // 🔥 修复：添加加载状态提示
      message.loading('正在保存分析数据...', 0)

      // 调用API保存分析数据
      const response = await booksAPI.updatePreparationResult(selectedChapter.value.id, data)

      message.destroy() // 关闭加载提示

      if (response.data && response.data.success) {
        message.success('分析数据保存成功')

        // 如果同步了其他章节，显示提示
        if (response.data.data?.synced_chapters > 0) {
          message.info(`已同步角色配置到 ${response.data.data.synced_chapters} 个章节`)
        }

        // 重新加载章节准备状态
        await loadChapterPreparationStatus(selectedChapter.value.id)
      } else {
        message.error(response.data?.message || '保存失败')
      }
    } catch (error) {
      console.error('❌ 保存分析数据失败:', error)
      message.destroy() // 关闭加载提示
      
      // 🔥 修复：提供更详细的错误信息
      const errorMessage = error.response?.data?.message || error.message || '未知错误'
      message.error(`保存分析数据失败: ${errorMessage}`)
      
      // 🔥 修复：如果网络错误，提示检查网络连接
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        message.warning('网络连接超时，请检查网络后重试')
      }
    }
  }
</script>

<style scoped>
  .book-detail-container {
    min-height: 100vh;
    background-color: var(--ant-color-bg-container);
  }

  .loading-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 50vh;
  }

  .detail-content {
    min-height: 100vh;
    color: var(--ant-color-text);
  }

  .main-content {
    margin-top: 16px;
  }

  .error-content {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 50vh;
  }

  /* 全局样式调整 */
  .main-content .ant-row {
    height: calc(100vh - var(--spacing-xxxl) - var(--spacing-xxxl));
  }

  .main-content .ant-col {
    background-color: var(--ant-color-bg-container);
  }

  /* 章节列表收起展开样式 */
  .chapter-list-col {
    transition: all 0.3s ease;
  }

  .chapter-list-container {
    height: 100%;
    display: flex;
    flex-direction: column;
  }



  /* 响应式设计 */
  @media (max-width: 768px) {
    .detail-content {
      padding: 16px;
    }

    .main-content .ant-row {
      height: auto;
    }

    .main-content .ant-col {
      height: auto;
      margin-bottom: 16px;
    }

    .collapse-toggle {
      justify-content: center;
    }
  }
</style>
