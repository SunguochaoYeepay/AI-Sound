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
        <!-- 左侧：书籍信息和内容 -->
        <a-col :span="16">
          <!-- 基本信息 -->
          <a-card title="📖 书籍信息" :bordered="false" class="info-card">
            <a-descriptions :column="2" bordered>
              <a-descriptions-item label="标题" :span="2">{{ book.title }}</a-descriptions-item>
              <a-descriptions-item label="作者">{{ book.author || '未知' }}</a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="getStatusColor(book.status)">
                  {{ getStatusText(book.status) }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="字数">{{ (book.word_count || 0).toLocaleString() }}</a-descriptions-item>
              <a-descriptions-item label="章节数">{{ chapters.length || 0 }}</a-descriptions-item>
              <a-descriptions-item label="创建时间" :span="2">{{ formatDate(book.created_at) }}</a-descriptions-item>
              <a-descriptions-item label="更新时间" :span="2">{{ formatDate(book.updated_at) }}</a-descriptions-item>
              <a-descriptions-item label="描述" :span="2">
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

          <!-- 内容预览 -->
          <a-card title="📄 内容预览" :bordered="false" class="content-card">
            <div class="content-actions">
              <a-space>
                <a-button @click="toggleFullContent" :type="showFullContent ? 'primary' : 'default'">
                  {{ showFullContent ? '收起内容' : '展开全文' }}
                </a-button>
                <a-button @click="copyContent" :disabled="!book.content">
                  📋 复制全文
                </a-button>
                <a-button @click="downloadTxt" :disabled="!book.content">
                  💾 下载TXT
                </a-button>
              </a-space>
            </div>
            
            <div class="content-preview" :class="{ 'full-content': showFullContent }">
              <div v-if="book.content" class="content-text">
                {{ showFullContent ? book.content : previewContent }}
                <div v-if="!showFullContent && book.content && book.content.length > 1000" class="content-fade">
                  <div class="fade-overlay"></div>
                  <a-button type="link" @click="toggleFullContent">
                    点击展开全文 ({{ book.content.length.toLocaleString() }} 字符)
                  </a-button>
                </div>
              </div>
              <div v-else class="no-content">
                暂无内容
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 右侧：章节和统计 -->
        <a-col :span="8">
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

          <!-- 章节列表 -->
          <a-card title="📚 章节列表" :bordered="false" class="chapters-card">
            <div v-if="detectingChapters" class="detecting-chapters">
              <a-spin size="small" />
              <span style="margin-left: 8px;">正在检测章节...</span>
            </div>
            
            <div v-else-if="chapters.length > 0" class="chapters-list">
              <div
                v-for="(chapter, index) in chapters"
                :key="index"
                class="chapter-item"
                @click="scrollToChapter(chapter)"
              >
                <div class="chapter-number">第{{ chapter.number }}章</div>
                <div class="chapter-title">{{ chapter.title }}</div>
                <div class="chapter-stats">{{ chapter.wordCount }} 字</div>
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
                  <span class="project-status">{{ project.status }}</span>
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { booksAPI } from '@/api'

const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(true)
const detectingChapters = ref(false)
const loadingProjects = ref(false)
const showFullContent = ref(false)

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

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const toggleFullContent = () => {
  showFullContent.value = !showFullContent.value
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
  if (!book.value?.content) {
    message.warning('暂无内容，无法检测章节')
    return
  }

  detectingChapters.value = true
  try {
    // 简单的章节检测逻辑
    const content = book.value.content
    const lines = content.split('\n')
    const detectedChapters = []
    
    const chapterPatterns = [
      /^第[一二三四五六七八九十百千万\d]+章\s*[：:：]?(.*)$/,
      /^第[一二三四五六七八九十百千万\d]+节\s*[：:：]?(.*)$/,
      /^Chapter\s+\d+\s*[：:：]?(.*)$/i,
      /^\d+[\.、]\s*(.*)$/,
      /^[一二三四五六七八九十百千万]+[、\.]\s*(.*)$/
    ]
    
    let currentChapter = 1
    let chapterStart = 0
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      if (!line) continue
      
      let isChapter = false
      let chapterTitle = line
      
      for (const pattern of chapterPatterns) {
        const match = pattern.exec(line)
        if (match) {
          isChapter = true
          chapterTitle = match[1]?.trim() || line
          break
        }
      }
      
      if (isChapter && currentChapter > 1) {
        // 保存上一章节
        const chapterContent = lines.slice(chapterStart, i).join('\n')
        detectedChapters[detectedChapters.length - 1].wordCount = chapterContent.replace(/\s/g, '').length
        chapterStart = i
      }
      
      if (isChapter) {
        detectedChapters.push({
          number: currentChapter,
          title: chapterTitle,
          start: chapterStart,
          end: 0,
          wordCount: 0,
          line: i
        })
        currentChapter++
      }
    }
    
    // 处理最后一章
    if (detectedChapters.length > 0) {
      const lastChapterContent = lines.slice(chapterStart).join('\n')
      detectedChapters[detectedChapters.length - 1].wordCount = lastChapterContent.replace(/\s/g, '').length
    }
    
    // 如果没有检测到章节，创建默认章节
    if (detectedChapters.length === 0) {
      detectedChapters.push({
        number: 1,
        title: '全文',
        start: 0,
        end: content.length,
        wordCount: content.replace(/\s/g, '').length,
        line: 0
      })
    }
    
    chapters.value = detectedChapters
    message.success(`检测到 ${detectedChapters.length} 个章节`)
    
  } catch (error) {
    console.error('章节检测失败:', error)
    message.error('章节检测失败')
  } finally {
    detectingChapters.value = false
  }
}

const scrollToChapter = (chapter) => {
  // 滚动到内容区域对应章节
  if (!showFullContent.value) {
    showFullContent.value = true
  }
  
  // 简单实现：暂时只提示
  message.info(`跳转到第${chapter.number}章：${chapter.title}`)
}

// 加载书籍详情
const loadBook = async () => {
  loading.value = true
  try {
    const response = await booksAPI.getBookDetail(route.params.id)
    if (response.data.success) {
      book.value = response.data.data
      
      // 自动检测章节
      await detectChapters()
      
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

.info-card, .content-card, .stats-card, .chapters-card, .projects-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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
  max-height: 400px;
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
  max-height: 400px;
  overflow-y: auto;
}

.chapter-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.chapter-item:hover {
  background-color: #f8fafc;
}

.chapter-item:last-child {
  border-bottom: none;
}

.chapter-number {
  font-size: 12px;
  color: #6b7280;
  min-width: 70px;
}

.chapter-title {
  flex: 1;
  font-size: 14px;
  margin: 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chapter-stats {
  font-size: 12px;
  color: #9ca3af;
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