<template>
  <div class="novel-project-create-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>{{ isEditing ? '编辑项目' : '创建新项目' }}</h1>
        <p>{{ isEditing ? '修改项目配置和设置' : '选择书籍内容，配置角色朗读项目' }}</p>
      </div>
      <div class="header-actions">
        <a-button @click="goBack">
          ← 返回
        </a-button>
      </div>
    </div>

    <div class="create-content-refactored">
      <a-row :gutter="24">
        <!-- 左侧：基本信息和书籍选择 -->
        <a-col :span="14">
          <!-- 基本信息 -->
          <a-card title="📝 项目基本信息" :bordered="false" class="config-card">
            <a-form :model="projectForm" :rules="projectRules" ref="projectFormRef" layout="vertical">
              <a-row :gutter="16">
                <a-col :span="16">
                  <a-form-item label="项目名称" name="name" required>
                    <a-input 
                      v-model:value="projectForm.name"
                      placeholder="如：西游记朗读版"
                      size="large"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="项目类型" name="type">
                    <a-select 
                      v-model:value="projectForm.type"
                      placeholder="类型"
                      size="large"
                    >
                      <a-select-option value="novel">小说</a-select-option>
                      <a-select-option value="story">故事</a-select-option>
                      <a-select-option value="dialogue">对话</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>

              <a-form-item label="项目描述（可选）" name="description">
                <a-textarea 
                  v-model:value="projectForm.description"
                  placeholder="简要描述项目内容..."
                  :rows="3"
                  :maxlength="200"
                  show-count
                />
              </a-form-item>
            </a-form>
          </a-card>

          <!-- 书籍选择 -->
          <a-card title="📚 选择书籍内容" :bordered="false" class="config-card">
            <div v-if="!selectedBook" class="book-selection">
              <!-- 从URL参数预选书籍或手动选择 -->
              <div v-if="preSelectedBook" class="pre-selected-book">
                <a-alert
                  :message="`检测到预选书籍：${preSelectedBook.title}`"
                  type="info"
                  show-icon
                  style="margin-bottom: 16px;"
                />
                <div class="book-preview-card">
                  <div class="book-info">
                    <h3>{{ preSelectedBook.title }}</h3>
                    <p class="book-meta">
                      作者：{{ preSelectedBook.author || '未知' }} | 
                      字数：{{ (preSelectedBook.word_count || 0).toLocaleString() }} | 
                      状态：{{ getStatusText(preSelectedBook.status) }}
                    </p>
                    <p class="book-description">{{ preSelectedBook.description || '暂无描述' }}</p>
                  </div>
                  <div class="book-actions">
                    <a-space>
                      <a-button type="primary" @click="selectBook(preSelectedBook)">
                        ✅ 使用此书籍
                      </a-button>
                      <a-button @click="showBookSelector">
                        🔄 重新选择
                      </a-button>
                    </a-space>
                  </div>
                </div>
              </div>

              <div v-else class="manual-selection">
                <!-- 搜索 -->
                <div class="book-search">
                  <a-input
                    v-model:value="bookSearch.keyword"
                    placeholder="搜索书籍标题、作者（仅显示已发布书籍）..."
                    size="large"
                    @change="handleBookSearch"
                  >
                    <template #prefix>
                      <SearchOutlined />
                    </template>
                  </a-input>
                  <p style="margin-top: 8px; color: #666; font-size: 12px;">
                    💡 提示：项目创建仅支持已发布状态的书籍，草稿和归档书籍不会显示
                  </p>
                </div>

                <!-- 书籍列表 -->
                <div v-if="booksLoading" class="books-loading">
                  <a-spin size="large" tip="加载书籍列表...">
                    <div style="height: 200px;"></div>
                  </a-spin>
                </div>

                <div v-else-if="availableBooks.length > 0" class="books-grid">
                  <div
                    v-for="book in availableBooks"
                    :key="book.id"
                    class="book-item"
                    @click="selectBook(book)"
                  >
                    <div class="book-item-content">
                      <h4>{{ book.title }}</h4>
                      <p class="book-meta">
                        {{ book.author || '未知作者' }} · {{ (book.word_count || 0).toLocaleString() }}字
                      </p>
                      <p class="book-desc">{{ book.description || '暂无描述' }}</p>
                      <div class="book-status">
                        <a-tag :color="getStatusColor(book.status)">
                          {{ getStatusText(book.status) }}
                        </a-tag>
                        <span class="book-date">{{ formatDate(book.updated_at) }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-else-if="!booksLoading" class="no-books">
                  <a-empty description="暂无可用书籍">
                    <a-button type="primary" @click="goToCreateBook">
                      📝 创建新书籍
                    </a-button>
                  </a-empty>
                </div>
              </div>
            </div>

            <!-- 已选择的书籍 -->
            <div v-else class="selected-book">
              <div class="selected-book-card">
                <div class="selected-book-header">
                  <h3>✅ 已选择书籍</h3>
                  <a-button type="link" @click="unselectBook">
                    🔄 重新选择
                  </a-button>
                </div>
                <div class="selected-book-info">
                  <h4>{{ selectedBook.title }}</h4>
                  <div class="book-stats">
                    <div class="stat-item">
                      <span class="stat-label">作者</span>
                      <span class="stat-value">{{ selectedBook.author || '未知' }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">字数</span>
                      <span class="stat-value">{{ (selectedBook.word_count || 0).toLocaleString() }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">状态</span>
                      <span class="stat-value">
                        <a-tag :color="getStatusColor(selectedBook.status)">
                          {{ getStatusText(selectedBook.status) }}
                        </a-tag>
                      </span>
                    </div>
                  </div>
                  <p class="book-description">{{ selectedBook.description || '暂无描述' }}</p>
                </div>
                
                <!-- 章节预览 -->
                <div v-if="bookChapters.length > 0" class="chapters-preview">
                  <h5>📚 章节预览 ({{ bookChapters.length }}章)</h5>
                  <div class="chapters-list">
                    <div
                      v-for="(chapter, index) in bookChapters.slice(0, 3)"
                      :key="index"
                      class="chapter-preview"
                    >
                      <span class="chapter-number">第{{ chapter.number }}章</span>
                      <span class="chapter-title">{{ chapter.title }}</span>
                      <span class="chapter-words">{{ chapter.wordCount }}字</span>
                    </div>
                    <div v-if="bookChapters.length > 3" class="more-chapters">
                      还有 {{ bookChapters.length - 3 }} 个章节...
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 右侧：预览和操作 -->
        <a-col :span="10">

          <!-- 项目统计预览 -->
          <a-card v-if="selectedBook" title="📊 项目预览" :bordered="false" class="config-card">
            <div class="project-stats">
              <div class="stat-grid">
                <div class="stat-item">
                  <div class="stat-value">{{ (selectedBook.word_count || 0).toLocaleString() }}</div>
                  <div class="stat-label">总字数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ estimatedSegments }}</div>
                  <div class="stat-label">预计分段</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ estimatedDuration }}</div>
                  <div class="stat-label">预计时长</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ bookChapters.length || 0 }}</div>
                  <div class="stat-label">章节数</div>
                </div>
              </div>
            </div>
          </a-card>

          <!-- 快速操作 -->
          <a-card title="🚀 快速创建" :bordered="false" class="config-card">
            <div class="quick-actions">
                <a-button 
                  type="primary" 
                  size="large" 
                  block 
                  @click="createProject" 
                  :loading="creating"
                  :disabled="!canCreate"
                >
                  {{ isEditing ? '💾 保存修改' : '✨ 创建项目' }}
                </a-button>
            </div>

            <!-- 创建提示 -->
            <a-alert 
              v-if="!canCreate" 
              :message="getCreateHint()" 
              type="warning" 
              show-icon 
              style="margin-top: 16px;"
            />

            <div v-if="canCreate" class="create-preview">
              <a-divider style="margin: 16px 0;" />
              <h4 style="margin-bottom: 8px;">📋 创建预览</h4>
              <div class="preview-item">
                <span class="preview-label">项目名称:</span>
                <span class="preview-value">{{ projectForm.name }}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">选择书籍:</span>
                <span class="preview-value">{{ selectedBook?.title }}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">文本长度:</span>
                <span class="preview-value">{{ (selectedBook?.word_count || 0).toLocaleString() }} 字</span>
              </div>

            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import { readerAPI, booksAPI } from '@/api'

const router = useRouter()
const route = useRoute()

// 响应式数据
const creating = ref(false)
const booksLoading = ref(false)
const projectFormRef = ref()

const isEditing = computed(() => !!route.params.id)

// 项目表单
const projectForm = reactive({
  name: '',
  type: 'novel',
  description: ''
})

const projectRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '项目名称长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

// 项目设置 - 简化后使用默认值
const projectSettings = reactive({
  segmentMode: 'paragraph',
  audioQuality: 'high',
  enableSmartDetection: true,
  enableBgMusic: false
})

// 书籍相关数据
const availableBooks = ref([])
const selectedBook = ref(null)
const preSelectedBook = ref(null)
const bookChapters = ref([])

const bookSearch = reactive({
  keyword: '',
  status: ''
})

// 计算属性
const canCreate = computed(() => {
  return projectForm.name.trim() && selectedBook.value
})

const estimatedSegments = computed(() => {
  if (!selectedBook.value?.word_count) return 0
  // 使用固定的段落分段方式
  const wordsPerSegment = 200
  return Math.ceil(selectedBook.value.word_count / wordsPerSegment)
})

const estimatedDuration = computed(() => {
  if (!selectedBook.value?.word_count) return '0分钟'
  const minutes = Math.ceil(selectedBook.value.word_count / 300) // 假设每分钟300字
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}小时${remainingMinutes}分钟`
})

// 方法
const goBack = () => {
  router.push('/novel-reader')
}

const goToCreateBook = () => {
  router.push('/books/create')
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
  return date.toLocaleDateString('zh-CN')
}



const getCreateHint = () => {
  if (!projectForm.name.trim()) return '请输入项目名称'
  if (!selectedBook.value) return '请选择书籍'
  return '准备就绪'
}

// 书籍管理
const loadBooks = async () => {
  booksLoading.value = true
  try {
    const params = {
      page: 1,
      page_size: 50,
      status: 'published' // 只显示已发布的书籍
    }
    
    if (bookSearch.keyword) {
      params.search = bookSearch.keyword
    }
    
    // 项目创建页面只允许选择已发布的书籍，忽略用户的状态筛选
    // if (bookSearch.status) {
    //   params.status = bookSearch.status
    // }
    
    const response = await booksAPI.getBooks(params)
    if (response.data.success) {
      // 修复：直接使用data数组，而不是data.items
      availableBooks.value = response.data.data || []
    }
  } catch (error) {
    console.error('加载书籍列表失败:', error)
    message.error('加载书籍列表失败')
  } finally {
    booksLoading.value = false
  }
}

const handleBookSearch = async () => {
  await loadBooks()
}

const selectBook = async (book) => {
  selectedBook.value = book
  
  // 自动设置项目名称（如果未填写）
  if (!projectForm.name.trim()) {
    projectForm.name = `${book.title} - 朗读版`
  }
  
  // 检测章节
  await detectBookChapters(book)
}

const unselectBook = () => {
  selectedBook.value = null
  bookChapters.value = []
}

const showBookSelector = () => {
  preSelectedBook.value = null
  loadBooks()
}

// 章节检测
const detectBookChapters = async (book) => {
  if (!book.content) {
    bookChapters.value = []
    return
  }

  try {
    // 简单的章节检测逻辑
    const content = book.content
    const lines = content.split('\n')
    const chapters = []
    
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
        chapters[chapters.length - 1].wordCount = chapterContent.replace(/\s/g, '').length
        chapterStart = i
      }
      
      if (isChapter) {
        chapters.push({
          number: currentChapter,
          title: chapterTitle,
          start: chapterStart,
          wordCount: 0
        })
        currentChapter++
      }
    }
    
    // 处理最后一章
    if (chapters.length > 0) {
      const lastChapterContent = lines.slice(chapterStart).join('\n')
      chapters[chapters.length - 1].wordCount = lastChapterContent.replace(/\s/g, '').length
    }
    
    bookChapters.value = chapters
    
  } catch (error) {
    console.error('章节检测失败:', error)
    bookChapters.value = []
  }
}

// 项目创建
const createProject = async () => {
  try {
    await projectFormRef.value.validate()
  } catch (error) {
    message.error('请检查表单内容')
    return
  }



  creating.value = true
  try {
    const projectData = {
      name: projectForm.name,
      description: projectForm.description,
      book_id: selectedBook.value?.id || null,
      initial_characters: [], // 初始化为空，后续在合成阶段配置
      settings: {
        segment_mode: projectSettings.segmentMode,
        audio_quality: projectSettings.audioQuality,
        enable_smart_detection: projectSettings.enableSmartDetection,
        enable_bg_music: projectSettings.enableBgMusic
      }
    }

    let response
    if (isEditing.value) {
      response = await readerAPI.updateProject(route.params.id, projectData)
    } else {
      response = await readerAPI.createProject(projectData)
    }

    if (response.data.success) {
      message.success(isEditing.value ? '项目更新成功' : '项目创建成功')
      router.push('/novel-reader')
    }
  } catch (error) {
    console.error('项目创建失败:', error)
    // 优先使用后端返回的具体错误信息
    const errorMsg = error.response?.data?.message || 
                     error.response?.data?.detail || 
                     error.message || 
                     '项目创建失败'
    message.error(`创建失败：${errorMsg}`)
  } finally {
    creating.value = false
  }
}



// 检查URL参数中的书籍ID
const checkPreSelectedBook = async () => {
  const bookId = route.query.bookId
  if (bookId) {
    try {
      const response = await booksAPI.getBookDetail(bookId)
      if (response.data.success) {
        preSelectedBook.value = response.data.data
      }
    } catch (error) {
      console.error('加载预选书籍失败:', error)
      // 如果加载失败，继续正常流程
      loadBooks()
    }
  } else {
    loadBooks()
  }
}

// 加载项目数据（编辑模式）
const loadProject = async () => {
  if (!isEditing.value) return

  try {
    console.log('=== 开始加载项目数据 ===')
    const response = await readerAPI.getProjectDetail(route.params.id)
    console.log('项目详情API响应:', response.data)
    
    if (response.data.success) {
      const project = response.data.data
      console.log('项目数据:', project)
      
      projectForm.name = project.name
      projectForm.description = project.description
      projectForm.type = project.type
      
      // 加载关联的书籍 - 支持多种字段格式
      const bookId = project.book_id || project.bookId
      console.log('书籍ID:', bookId)
      
      if (bookId) {
        // 如果项目数据中已经包含了book信息，直接使用
        if (project.book) {
          console.log('使用项目中的书籍数据:', project.book)
          selectedBook.value = project.book
          await detectBookChapters(selectedBook.value)
        } else {
          // 否则通过API获取书籍详情
          console.log('通过API获取书籍详情...')
          try {
            const bookResponse = await booksAPI.getBookDetail(bookId)
            if (bookResponse.data.success) {
              console.log('书籍API响应:', bookResponse.data)
              selectedBook.value = bookResponse.data.data
              await detectBookChapters(selectedBook.value)
            }
          } catch (bookError) {
            console.error('获取书籍详情失败:', bookError)
            message.warning('无法加载关联的书籍信息')
          }
        }
      } else {
        console.log('项目没有关联书籍')
      }
      
      // 项目设置保持默认值（简化后不需要加载）
      
      console.log('=== 项目数据加载完成 ===')
      console.log('selectedBook:', selectedBook.value)
    }
  } catch (error) {
    console.error('加载项目数据失败:', error)
    message.error('加载项目数据失败')
    router.push('/novel-reader')
  }
}

// 生命周期
onMounted(() => {
  if (isEditing.value) {
    loadProject()
    // 编辑模式下也需要加载书籍列表，以便用户重新选择
    loadBooks()
  } else {
    checkPreSelectedBook()
  }
})
</script>

<style scoped>
.novel-project-create-container {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-content h1 {
  margin: 0;
  color: #1f2937;
  font-size: 24px;
}

.header-content p {
  margin: 8px 0 0 0;
  color: #6b7280;
}

.create-content-refactored {
  margin-bottom: 24px;
}

.config-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 书籍选择样式 */
.book-selection {
  min-height: 200px;
}

.pre-selected-book .book-preview-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  background: #f8fafc;
}

.book-info h3 {
  margin: 0 0 8px 0;
  color: #1f2937;
}

.book-meta {
  margin: 4px 0;
  color: #6b7280;
  font-size: 14px;
}

.book-description {
  margin: 8px 0;
  color: #374151;
  line-height: 1.5;
}

.book-actions {
  margin-top: 16px;
  text-align: right;
}

.book-search {
  margin-bottom: 16px;
}

.books-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.books-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.book-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.book-item:hover {
  border-color: #06b6d4;
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.15);
}

.book-item-content h4 {
  margin: 0 0 8px 0;
  color: #1f2937;
}

.book-desc {
  margin: 8px 0;
  color: #6b7280;
  font-size: 13px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.book-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.book-date {
  font-size: 12px;
  color: #9ca3af;
}

/* 已选择书籍样式 */
.selected-book-card {
  border: 2px solid #06b6d4;
  border-radius: 8px;
  padding: 20px;
  background: linear-gradient(135deg, #f0fdff 0%, #f8fafc 100%);
}

.selected-book-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.selected-book-header h3 {
  margin: 0;
  color: #0891b2;
}

.selected-book-info h4 {
  margin: 0 0 12px 0;
  color: #1f2937;
  font-size: 18px;
}

.book-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin: 12px 0;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-weight: 600;
  color: #1f2937;
}

.chapters-preview {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.chapters-preview h5 {
  margin: 0 0 12px 0;
  color: #374151;
}

.chapters-list {
  background: white;
  border-radius: 6px;
  padding: 12px;
}

.chapter-preview {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}

.chapter-preview:last-child {
  border-bottom: none;
}

.chapter-number {
  font-size: 12px;
  color: #6b7280;
  min-width: 60px;
}

.chapter-title {
  flex: 1;
  font-size: 13px;
  margin: 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chapter-words {
  font-size: 12px;
  color: #9ca3af;
}

.more-chapters {
  text-align: center;
  padding: 8px 0;
  color: #6b7280;
  font-size: 12px;
}

/* 项目统计样式 */
.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-grid .stat-item {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  text-align: center;
}

.stat-grid .stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.stat-grid .stat-label {
  font-size: 12px;
  color: #6b7280;
}

/* 预览样式 */
.create-preview {
  margin-top: 16px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}

.preview-item:last-child {
  border-bottom: none;
}

.preview-label {
  font-size: 13px;
  color: #6b7280;
}

.preview-value {
  font-size: 13px;
  color: #1f2937;
  font-weight: 500;
}

.no-books {
  padding: 40px 20px;
  text-align: center;
}
</style> 