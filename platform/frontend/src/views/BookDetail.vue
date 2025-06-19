<template>
  <div class="book-detail-container">
    <!-- Loading状态 -->
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载书籍详情中...">
        <div style="height: 200px;"></div>
      </a-spin>
    </div>

    <!-- 书籍详情内容 -->
    <div v-else-if="book" class="detail-content">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <div class="book-meta">
            <h1>{{ book.title }}</h1>
            <div class="meta-info">
              <a-tag :color="getStatusColor(book.status)">
                {{ getStatusText(book.status) }}
              </a-tag>
              <span class="author">作者：{{ book.author || '未知' }}</span>
              <span class="word-count">字数：{{ (book.word_count || 0).toLocaleString() }}</span>
              <span class="update-time">更新：{{ formatDate(book.updated_at) }}</span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <a-space>
            <a-button @click="goBack">
              ← 返回列表
            </a-button>
            <a-button type="primary" @click="editBook">
              ✏️ 编辑
            </a-button>
            <a-button @click="createProject" :disabled="!book.content">
              🎯 创建项目
            </a-button>
          </a-space>
        </div>
      </div>

      <a-row :gutter="24">
        <!-- 左侧：Tabs式内容区域 -->
        <a-col :span="16">
          <a-card :bordered="false" class="content-tabs-card">
            <a-tabs v-model:activeKey="activeTab" @change="handleTabChange">
              <!-- 智能识别结果 Tab -->
              <a-tab-pane key="chapters" tab="🤖 智能识别结果">
                <div v-if="detectingChapters" class="detecting-chapters">
                  <a-spin size="small" />
                  <span style="margin-left: 8px;">正在检测章节...</span>
                </div>
                
                <div v-else-if="chapters.length > 0" class="chapters-list">
                  <div
                    v-for="(chapter, index) in chapters"
                    :key="index"
                    class="chapter-item"
                  >
                    <div class="chapter-content" @click="scrollToChapter(chapter)">
                      <div class="chapter-number">第{{ chapter.number }}章</div>
                      <div class="chapter-title">{{ chapter.title }}</div>
                      <div class="chapter-stats">{{ chapter.wordCount }} 字</div>
                      <!-- 智能准备状态指示器 -->
                      <div v-if="chapterPreparationStatus[chapter.id]" class="preparation-status">
                        <a-tag 
                          :color="getPreparationStatusColor(chapterPreparationStatus[chapter.id])"
                          size="small"
                        >
                          {{ getPreparationStatusText(chapterPreparationStatus[chapter.id]) }}
                        </a-tag>
                      </div>
                    </div>
                    <div class="chapter-actions">
                      <!-- 根据准备状态显示不同按钮 -->
                      <template v-if="chapterPreparationStatus[chapter.id]?.preparation_complete">
                        <!-- 已完成智能准备 -->
                        <a-button 
                          type="default" 
                          size="small"
                          @click.stop="openAnalysisDrawer(chapter)"
                          title="查看智能准备结果"
                        >
                          📋 查看结果
                        </a-button>
                        <a-button 
                          type="primary" 
                          size="small"
                          @click.stop="prepareChapterForSynthesis(chapter, true)"
                          :loading="preparingChapters.has(chapter.id)"
                          title="重新执行智能准备"
                        >
                          🔄 再次准备
                        </a-button>
                      </template>
                      <template v-else>
                        <!-- 未完成智能准备 -->
                        <a-button 
                          type="primary" 
                          size="small"
                          @click.stop="prepareChapterForSynthesis(chapter)"
                          :loading="preparingChapters.has(chapter.id)"
                          title="智能准备章节内容用于语音合成"
                        >
                          🎭 智能准备
                        </a-button>
                      </template>
                    </div>
                  </div>
                </div>
                
                <div v-else class="no-chapters">
                  <a-empty
                    description="暂无章节"
                  >
                    <a-button type="primary" @click="detectChapters" :loading="detectingChapters">
                      🔍 检测章节
                    </a-button>
                  </a-empty>
                </div>
              </a-tab-pane>

              <!-- 原文预览 Tab -->
              <a-tab-pane key="content" tab="📖 原文预览">
                <div class="content-actions">
                  <a-space>
                    <a-button @click="copyContent" :disabled="!book.content">
                      📋 复制全文
                    </a-button>
                    <a-button @click="downloadTxt" :disabled="!book.content">
                      💾 下载TXT
                    </a-button>
                    <span class="content-stats">
                      共 {{ chapters.length }} 章节 · {{ (book.word_count || 0).toLocaleString() }} 字
                    </span>
                  </a-space>
                </div>
                
                <!-- 按章节显示内容 -->
                <div v-if="chapters.length > 0" class="chapters-content-list">
                  <div
                    v-for="(chapter, index) in chapters"
                    :key="index"
                    class="chapter-content-item"
                    :id="`chapter-${chapter.id}`"
                  >
                    <div class="chapter-content-header">
                      <div class="chapter-info">
                        <span class="chapter-number">第{{ chapter.number }}章</span>
                        <span class="chapter-title">{{ chapter.title }}</span>
                        <span class="chapter-word-count">{{ chapter.wordCount }} 字</span>
                      </div>
                      <div class="chapter-actions">
                        <a-button 
                          v-if="chapterPreparationStatus[chapter.id]?.preparation_complete"
                          type="link" 
                          size="small"
                          @click="openAnalysisDrawer(chapter)"
                        >
                          📋 查看智能结果
                        </a-button>
                        <a-button 
                          v-else
                          type="link" 
                          size="small"
                          @click="prepareChapterForSynthesis(chapter)"
                          :loading="preparingChapters.has(chapter.id)"
                        >
                          🎭 智能准备
                        </a-button>
                      </div>
                    </div>
                    <div class="chapter-content-text">
                      <div v-if="chapter.content" class="content-text">
                        {{ chapter.content }}
                      </div>
                      <div v-else class="no-chapter-content">
                        <a-empty description="该章节暂无内容" size="small" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 无章节时显示完整内容 -->
                <div v-else-if="book.content" class="full-content-fallback">
                  <div class="content-text">
                    {{ book.content }}
                  </div>
                </div>
                
                <div v-else class="no-content">
                  <a-empty description="暂无内容">
                    <a-button type="primary" @click="detectChapters" :loading="detectingChapters">
                      🔍 检测章节
                    </a-button>
                  </a-empty>
                </div>
              </a-tab-pane>
            </a-tabs>
          </a-card>
        </a-col>

        <!-- 右侧：书籍信息和统计 -->
        <a-col :span="8">
          <!-- 基本信息 -->
          <a-card title="📖 书籍信息" :bordered="false" class="info-card">
            <a-descriptions :column="1" bordered>
              <a-descriptions-item label="标题">{{ book.title }}</a-descriptions-item>
              <a-descriptions-item label="作者">{{ book.author || '未知' }}</a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="getStatusColor(book.status)">
                  {{ getStatusText(book.status) }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="字数">{{ (book.word_count || 0).toLocaleString() }}</a-descriptions-item>
              <a-descriptions-item label="章节数">{{ chapters.length || 0 }}</a-descriptions-item>
              <a-descriptions-item label="创建时间">{{ formatDate(book.created_at) }}</a-descriptions-item>
              <a-descriptions-item label="更新时间">{{ formatDate(book.updated_at) }}</a-descriptions-item>
              <a-descriptions-item label="描述">
                <div class="description">
                  {{ book.description || '暂无描述' }}
                </div>
              </a-descriptions-item>
            </a-descriptions>
            
            <!-- 标签 -->
            <div v-if="book.tags && book.tags.length > 0" class="tags-section">
              <div class="tags-label">标签:</div>
              <a-space wrap>
                <a-tag v-for="tag in book.tags" :key="tag" color="blue">
                  {{ tag }}
                </a-tag>
              </a-space>
            </div>
          </a-card>

          <!-- 内容统计 -->
          <a-card title="📊 内容统计" :bordered="false" class="stats-card">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ (book.content || '').length.toLocaleString() }}</div>
                <div class="stat-label">总字符数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ (book.word_count || 0).toLocaleString() }}</div>
                <div class="stat-label">总字数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ estimatedReadTime }}</div>
                <div class="stat-label">预计阅读时长</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ chapters.length || 0 }}</div>
                <div class="stat-label">章节数</div>
              </div>
            </div>
          </a-card>

          <!-- 相关项目 -->
          <a-card title="🎯 相关项目" :bordered="false" class="projects-card">
            <div v-if="loadingProjects" class="loading-projects">
              <a-spin size="small" />
              <span style="margin-left: 8px;">加载相关项目...</span>
            </div>
            
            <div v-else-if="relatedProjects.length > 0" class="projects-list">
              <div
                v-for="project in relatedProjects"
                :key="project.id"
                class="project-item"
              >
                <div class="project-name">{{ project.name }}</div>
                <div class="project-meta">
                  <span class="project-status">{{ getProjectStatusText(project.status) }}</span>
                  <span class="project-date">{{ formatDate(project.created_at) }}</span>
                </div>
              </div>
            </div>
            
            <div v-else class="no-projects">
              <a-empty
                description="暂无相关项目"
              >
                <a-button type="primary" @click="createProject" :disabled="!book.content">
                  ➕ 创建项目
                </a-button>
              </a-empty>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-content">
      <a-result
        status="404"
        title="书籍不存在"
        sub-title="抱歉，您访问的书籍不存在或已被删除"
      >
        <template #extra>
          <a-button type="primary" @click="goBack">返回列表</a-button>
        </template>
      </a-result>
    </div>

    <!-- 智能分析结果抽屉 -->
    <EditableAnalysisDrawer
      v-model:visible="analysisDrawerVisible"
      :chapterId="currentChapterId"
      @saved="handleAnalysisResultSaved"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { booksAPI } from '@/api'
import EditableAnalysisDrawer from '@/components/EditableAnalysisDrawer.vue'

const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(true)
const detectingChapters = ref(false)
const loadingProjects = ref(false)
const showFullContent = ref(false)
const preparingChapters = ref(new Set()) // 正在准备的章节ID集合
const chapterPreparationStatus = ref({}) // 章节智能准备状态
const activeTab = ref('chapters') // 默认显示章节列表

// 抽屉相关状态
const analysisDrawerVisible = ref(false)
const currentChapterId = ref(null)

const book = ref(null)
const chapters = ref([])
const relatedProjects = ref([])

// 计算属性
const previewContent = computed(() => {
  if (!book.value?.content) return ''
  return book.value.content.length > 1000 
    ? book.value.content.substring(0, 1000) + '...'
    : book.value.content
})

const estimatedReadTime = computed(() => {
  if (!book.value?.word_count) return '0 分钟'
  const minutes = Math.ceil(book.value.word_count / 300)
  if (minutes < 60) return `${minutes} 分钟`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}小时${remainingMinutes}分钟`
})

// 方法
const goBack = () => {
  router.push('/books')
}

const editBook = () => {
  router.push(`/books/edit/${route.params.id}`)
}

const createProject = () => {
  // 跳转到项目创建页面，传递书籍ID
  router.push(`/novel-reader/create?bookId=${route.params.id}`)
}

const getStatusColor = (status) => {
  const colors = {
    draft: 'orange',
    published: 'green',
    archived: 'gray'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档'
  }
  return texts[status] || status
}

// 项目状态文本转换
const getProjectStatusText = (status) => {
  const texts = {
    pending: '待开始',
    processing: '合成中',
    paused: '已暂停',
    completed: '已完成',
    partial_completed: '部分完成',
    failed: '失败',
    cancelled: '已取消',
    configured: '已配置'
  }
  return texts[status] || status
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const toggleFullContent = () => {
  showFullContent.value = !showFullContent.value
}

const handleTabChange = (key) => {
  activeTab.value = key
  console.log('[BookDetail] Tab切换到:', key)
}

const copyContent = async () => {
  if (!book.value?.content) {
    message.warning('暂无内容可复制')
    return
  }

  try {
    await navigator.clipboard.writeText(book.value.content)
    message.success('内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    message.error('复制失败')
  }
}

const downloadTxt = () => {
  if (!book.value?.content) {
    message.warning('暂无内容可下载')
    return
  }

  const blob = new Blob([book.value.content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${book.value.title}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  message.success('下载成功')
}

// 章节检测
const detectChapters = async () => {
  if (!book.value?.id) {
    message.warning('书籍信息不完整')
    return
  }

  detectingChapters.value = true
  try {
    console.log('[BookDetail] 开始检测章节，书籍ID:', book.value.id)
    
    // 使用后端API检测章节
    const response = await booksAPI.detectChapters(book.value.id, { force_reprocess: false })
    console.log('[BookDetail] 章节检测响应:', response)
    
    if (response.data && response.data.success) {
      message.success(response.data.message || '章节检测完成')
      // 重新加载章节列表和书籍信息
      await Promise.all([loadChapters(), loadBook()])
    }
  } catch (error) {
    console.error('[BookDetail] 章节检测失败:', error)
    console.error('[BookDetail] 错误详情:', error.response?.data)
    
    if (error.response?.status === 400) {
      // 如果已有章节，询问是否强制重新处理
      const errorMsg = error.response.data?.detail || '检测失败'
      if (errorMsg.includes('已有') && errorMsg.includes('章节')) {
        const confirmed = await new Promise((resolve) => {
          Modal.confirm({
            title: '检测到已有章节',
            content: `${errorMsg}，是否强制重新检测？这将覆盖现有章节数据。`,
            onOk: () => resolve(true),
            onCancel: () => resolve(false)
          })
        })
        
        if (confirmed) {
          try {
            console.log('[BookDetail] 开始强制重新检测章节')
            const forceResponse = await booksAPI.detectChapters(book.value.id, { force_reprocess: true })
            console.log('[BookDetail] 强制检测响应:', forceResponse)
            
            if (forceResponse.data && forceResponse.data.success) {
              message.success(forceResponse.data.message || '强制章节检测完成')
              // 重新加载章节列表和书籍信息
              await Promise.all([loadChapters(), loadBook()])
            }
          } catch (forceError) {
            console.error('[BookDetail] 强制章节检测失败:', forceError)
            message.error('强制章节检测失败: ' + (forceError.response?.data?.detail || '未知错误'))
          }
        }
      } else {
        message.error(errorMsg)
      }
    } else {
      message.error('章节检测失败: ' + (error.response?.data?.detail || '网络错误'))
    }
  } finally {
    detectingChapters.value = false
  }
}

// 加载章节列表
const loadChapters = async () => {
  if (!book.value?.id) return
  
  try {
    console.log('[BookDetail] 开始加载章节列表，书籍ID:', book.value.id)
    const response = await booksAPI.getBookChapters(book.value.id)
    console.log('[BookDetail] 章节API响应:', response)
    
    if (response.data && response.data.success) {
      // 转换章节数据格式
      const chaptersData = response.data.data || []
      console.log('[BookDetail] 原始章节数据:', chaptersData)
      
      chapters.value = chaptersData.map(chapter => ({
        id: chapter.id,
        number: chapter.chapter_number,
        title: chapter.chapter_title || `第${chapter.chapter_number}章`,
        wordCount: chapter.word_count || 0,
        status: chapter.analysis_status,
        content: chapter.content
      }))
      
      console.log('[BookDetail] 转换后的章节数据:', chapters.value)
      console.log('[BookDetail] 章节数量:', chapters.value.length)
      
      // 加载所有章节的智能准备状态
      await loadAllChapterPreparationStatus()
    } else {
      console.warn('[BookDetail] API响应格式异常:', response)
      chapters.value = []
    }
  } catch (error) {
    console.error('[BookDetail] 加载章节列表失败:', error)
    console.error('[BookDetail] 错误详情:', error.response?.data)
    
    // 重置章节数据
    chapters.value = []
    
    // 如果是404错误，说明没有章节数据
    if (error.response?.status === 404) {
      console.log('[BookDetail] 未找到章节数据，可能需要检测章节')
    } else {
      // 其他错误显示提示
      message.warning('加载章节列表失败，请尝试检测章节')
    }
  }
}

const scrollToChapter = (chapter) => {
  // 切换到原文预览tab
  activeTab.value = 'content'
  
  // 等待DOM更新后滚动到对应章节
  nextTick(() => {
    const chapterElement = document.getElementById(`chapter-${chapter.id}`)
    if (chapterElement) {
      chapterElement.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      })
      // 高亮显示该章节
      chapterElement.classList.add('chapter-highlight')
      setTimeout(() => {
        chapterElement.classList.remove('chapter-highlight')
      }, 2000)
    } else {
      message.info(`跳转到第${chapter.number}章：${chapter.title}`)
    }
  })
}

// 智能准备章节
const prepareChapterForSynthesis = async (chapter, force = false) => {
  if (!chapter?.id) {
    message.warning('章节信息不完整')
    return
  }

  // 检查是否正在准备
  if (preparingChapters.value.has(chapter.id)) {
    message.warning('该章节正在准备中，请稍候')
    return
  }

  // 添加到准备中的集合
  preparingChapters.value.add(chapter.id)

  try {
    console.log('[BookDetail] 开始智能准备章节:', chapter)
    
    // 调用智能准备API
    const response = await booksAPI.prepareChapterForSynthesis(chapter.id, { force })
    console.log('[BookDetail] 智能准备响应:', response)
    
    if (response.data && response.data.success) {
      const result = response.data.data
      
      // 显示准备结果
      Modal.success({
        title: '智能准备完成',
        content: `
          章节：${chapter.title}
          检测到 ${result.processing_info?.characters_found || result.synthesis_json?.characters?.length || 0} 个角色
          生成 ${result.synthesis_json?.synthesis_plan?.length || result.segments?.length || 0} 个语音片段
          自动添加旁白角色：${result.processing_info?.narrator_added ? '是' : '否'}
        `,
        width: 500
      })
      
      message.success('章节智能准备完成')
      
      // 刷新该章节的准备状态
      await loadChapterPreparationStatus(chapter.id)
    }
  } catch (error) {
    console.error('[BookDetail] 智能准备失败:', error)
    console.error('[BookDetail] 错误详情:', error.response?.data)
    
    const errorMsg = error.response?.data?.detail || '智能准备失败'
    message.error(errorMsg)
  } finally {
    // 从准备中的集合移除
    preparingChapters.value.delete(chapter.id)
  }
}

// 获取章节智能准备状态
const loadChapterPreparationStatus = async (chapterId) => {
  try {
    const response = await booksAPI.getPreparationStatus(chapterId)
    if (response.data && response.data.success) {
      chapterPreparationStatus.value[chapterId] = response.data.data
    }
  } catch (error) {
    console.error(`获取章节 ${chapterId} 准备状态失败:`, error)
  }
}

// 批量加载所有章节的准备状态
const loadAllChapterPreparationStatus = async () => {
  if (!chapters.value.length) return
  
  const promises = chapters.value.map(chapter => 
    loadChapterPreparationStatus(chapter.id)
  )
  
  await Promise.allSettled(promises)
}

// 打开智能分析抽屉
const openAnalysisDrawer = (chapter) => {
  console.log('[BookDetail] 打开智能分析抽屉:', chapter)
  currentChapterId.value = chapter.id
  analysisDrawerVisible.value = true
}

// 处理分析结果保存后的回调
const handleAnalysisResultSaved = (updatedData) => {
  console.log('[BookDetail] 智能分析结果已保存:', updatedData)
  message.success('智能分析结果已保存，章节数据已更新')
  
  // 可以在这里刷新章节的准备状态
  // 或者更新本地的章节数据
}

// 获取准备状态颜色
const getPreparationStatusColor = (status) => {
  if (!status) return 'default'
  
  if (status.preparation_complete) return 'green'
  if (status.analysis_status === 'analyzing') return 'blue'
  if (status.analysis_status === 'failed') return 'red'
  return 'orange'
}

// 获取准备状态文本
const getPreparationStatusText = (status) => {
  if (!status) return '未知'
  
  if (status.preparation_complete) return '已完成'
  if (status.analysis_status === 'analyzing') return '分析中'
  if (status.analysis_status === 'failed') return '失败'
  if (status.analysis_status === 'completed' && !status.preparation_complete) return '部分完成'
  return '待处理'
}

// 加载书籍详情
const loadBook = async () => {
  loading.value = true
  try {
    const response = await booksAPI.getBookDetail(route.params.id)
    if (response.data.success) {
      book.value = response.data.data
      
      // 加载章节列表
      await loadChapters()
      
      // 加载相关项目
      loadRelatedProjects()
    }
  } catch (error) {
    console.error('加载书籍详情失败:', error)
    message.error('加载书籍详情失败')
  } finally {
    loading.value = false
  }
}

// 加载相关项目
const loadRelatedProjects = async () => {
  loadingProjects.value = true
  try {
    // 暂时模拟数据，实际需要API支持
    relatedProjects.value = []
  } catch (error) {
    console.error('加载相关项目失败:', error)
  } finally {
    loadingProjects.value = false
  }
}

// 生命周期
onMounted(() => {
  loadBook()
})
</script>

<style scoped>
.book-detail-container {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.book-meta h1 {
  margin: 0 0 12px 0;
  color: #1f2937;
  font-size: 28px;
  font-weight: 600;
}

.meta-info {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.meta-info span {
  color: #6b7280;
  font-size: 14px;
}

.info-card, .content-card, .stats-card, .chapters-card, .projects-card, .content-tabs-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.content-tabs-card {
  min-height: 500px;
}

.content-tabs-card .ant-tabs-content-holder {
  padding: 16px 0;
}

.tags-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.tags-label {
  font-weight: 500;
  color: #374151;
}

.content-actions {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.content-stats {
  color: #666;
  font-size: 12px;
}

/* 章节内容列表样式 */
.chapters-content-list {
  overflow-y: auto;
}

.chapter-content-item {
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.chapter-content-item.chapter-highlight {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.chapter-content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f0f2f5;
  border-bottom: 1px solid #e8e8e8;
}

.chapter-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chapter-number {
  font-size: 12px;
  color: #1890ff;
  font-weight: 500;
}

.chapter-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.chapter-word-count {
  font-size: 12px;
  color: #9ca3af;
}

.chapter-content-text {
  padding: 16px;
}

.chapter-content-text .content-text {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
  color: #374151;
  font-family: 'Microsoft YaHei', sans-serif;
}

.no-chapter-content {
  text-align: center;
  padding: 20px;
}

.full-content-fallback {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.content-preview {
  position: relative;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
  color: #374151;
  font-family: 'Microsoft YaHei', sans-serif;
}

.full-content .content-text {
  max-height: none;
}

.content-preview:not(.full-content) .content-text {
  overflow: hidden;
}

.content-fade {
  position: relative;
  text-align: center;
  margin-top: 16px;
}

.fade-overlay {
  position: absolute;
  top: -60px;
  left: 0;
  right: 0;
  height: 60px;
  background: linear-gradient(to bottom, transparent, white);
  pointer-events: none;
}

.no-content {
  text-align: center;
  color: #9ca3af;
  padding: 40px 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
}

.detecting-chapters, .loading-projects {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #6b7280;
}

.chapters-list, .projects-list {
  overflow-y: auto;
}

.chapter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 12px;
  background: white;
  transition: all 0.2s ease;
}

.chapter-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.chapter-content {
  flex: 1;
  cursor: pointer;
}

/* 智能识别结果tab中的章节样式 */
.chapters-list .chapter-number {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.chapters-list .chapter-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.chapter-stats {
  font-size: 12px;
  color: #9ca3af;
}

.preparation-status {
  margin-top: 8px;
}

.chapter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.project-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.project-item:last-child {
  border-bottom: none;
}

.project-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.project-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
}

.no-chapters, .no-projects {
  padding: 20px;
}

.description {
  white-space: pre-wrap;
  line-height: 1.6;
}

.error-content {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
</style> 