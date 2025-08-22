<template>
  <div class="environment-analysis">
    <!-- 项目头部 -->
    <div class="project-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-with-back">
            <a-button type="link" @click="$router.go(-1)" class="back-button">
              <ArrowLeftOutlined />
              返回
            </a-button>
            <h1 class="page-title">
              <BulbOutlined class="title-icon" />
              环境音分析
            </h1>
          </div>
          <p class="page-description">
            选择书籍和章节，创建环境音分析项目
          </p>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧：书籍和章节选择器 -->
      <div class="selection-area">
        <!-- 书籍选择 -->
        <div class="book-selection">
          <div class="section-header">
            <h3>选择书籍</h3>
            <a-button @click="loadBooks" :loading="booksLoading" size="small" type="text">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </div>
          
          <div class="books-list">
            <div v-if="booksLoading" class="loading-state">
              <a-spin size="large" />
              <p>加载书籍中...</p>
            </div>
            
            <div v-else-if="books.length > 0" class="books-container">
              <div
                v-for="book in books"
                :key="book.id"
                :class="['book-item', { active: selectedBook?.id === book.id }]"
                @click="selectBook(book)"
              >
                <div class="book-info">
                  <div class="book-title">{{ book.title }}</div>
                  <div class="book-meta">
                    <span class="chapter-count">{{ book.chapter_count || 0 }} 章</span>
                    <span class="book-status">{{ book.status || '正常' }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="empty-books">
              <a-empty description="暂无书籍数据">
                <a-button type="primary" @click="loadBooks">重新加载</a-button>
              </a-empty>
            </div>
          </div>
        </div>

        <!-- 章节选择 -->
        <div v-if="selectedBook" class="chapter-selection">
          <div class="section-header">
            <h3>选择章节</h3>
            <a-button @click="loadChapters" :loading="chaptersLoading" size="small" type="text">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </div>
          
          <div class="chapters-list">
            <div v-if="chaptersLoading" class="loading-state">
              <a-spin size="large" />
              <p>加载章节中...</p>
            </div>
            
            <div v-else-if="chapters.length > 0" class="chapters-container">
              <div
                v-for="chapter in chapters"
                :key="chapter.id"
                :class="['chapter-item', { active: selectedChapter?.id === chapter.id }]"
                @click="selectChapter(chapter)"
              >
                <div class="chapter-info">
                  <div class="chapter-title">第{{ chapter.chapter_number }}章 {{ chapter.chapter_title }}</div>
                  <div class="chapter-meta">
                    <span class="word-count">{{ formatNumber(chapter.word_count || 0) }} 字</span>
                    <span class="chapter-status">{{ chapter.status || '正常' }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="empty-chapters">
              <a-empty description="暂无章节数据">
                <a-button type="primary" @click="loadChapters">重新加载</a-button>
              </a-empty>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：分析配置和操作 -->
      <div class="analysis-area">
        <div v-if="!selectedBook" class="empty-state">
          <a-empty description="请先选择书籍">
            <template #image>
              <BookOutlined style="font-size: 64px; color: #d9d9d9;" />
            </template>
          </a-empty>
        </div>
        
        <div v-else-if="!selectedChapter" class="chapter-prompt">
          <a-empty description="请选择要分析的章节">
            <template #image>
              <FileTextOutlined style="font-size: 64px; color: #d9d9d9;" />
            </template>
          </a-empty>
        </div>
        
        <div v-else class="analysis-config">
          <div class="config-header">
            <h3>分析配置</h3>
          </div>
          
          <div class="selected-info">
            <div class="info-item">
              <span class="label">书籍：</span>
              <span class="value">{{ selectedBook.title }}</span>
            </div>
            <div class="info-item">
              <span class="label">章节：</span>
              <span class="value">第{{ selectedChapter.chapter_number }}章 {{ selectedChapter.chapter_title }}</span>
            </div>
            <div class="info-item">
              <span class="label">字数：</span>
              <span class="value">{{ formatNumber(selectedChapter.word_count || 0) }} 字</span>
            </div>
          </div>
          
          <div class="analysis-options">
            <h4>分析选项</h4>
            <a-form :model="analysisOptions" layout="vertical">
              <a-form-item label="分析模式">
                <a-radio-group v-model:value="analysisOptions.mode">
                  <a-radio value="auto">智能分析</a-radio>
                  <a-radio value="manual">手动配置</a-radio>
                </a-radio-group>
              </a-form-item>
              
              <a-form-item label="环境音类型">
                <a-checkbox-group v-model:value="analysisOptions.environmentTypes">
                  <a-checkbox value="nature">自然环境</a-checkbox>
                  <a-checkbox value="urban">城市环境</a-checkbox>
                  <a-checkbox value="indoor">室内环境</a-checkbox>
                  <a-checkbox value="action">动作音效</a-checkbox>
                </a-checkbox-group>
              </a-form-item>
              
              <a-form-item label="分析精度">
                <a-select v-model:value="analysisOptions.precision">
                  <a-select-option value="high">高精度</a-select-option>
                  <a-select-option value="medium">中等精度</a-select-option>
                  <a-select-option value="low">低精度</a-select-option>
                </a-select>
              </a-form-item>
            </a-form>
          </div>
          
          <div class="analysis-actions">
            <a-space>
              <a-button 
                type="primary" 
                size="large"
                :loading="creatingProject"
                @click="createAnalysisProject"
              >
                创建分析项目
              </a-button>
              <a-button @click="resetSelection">
                重新选择
              </a-button>
            </a-space>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { 
  ArrowLeftOutlined, 
  BulbOutlined,
  ReloadOutlined,
  BookOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue'
import { readerAPI, booksAPI } from '@/api'

const router = useRouter()

// 数据状态
const books = ref([])
const chapters = ref([])
const selectedBook = ref(null)
const selectedChapter = ref(null)

// 加载状态
const booksLoading = ref(false)
const chaptersLoading = ref(false)
const creatingProject = ref(false)

// 分析选项
const analysisOptions = ref({
  mode: 'auto',
  environmentTypes: ['nature', 'urban', 'indoor', 'action'],
  precision: 'medium'
})

// 生命周期
onMounted(() => {
  loadBooks()
})

// 方法
const loadBooks = async () => {
  try {
    booksLoading.value = true
    const response = await booksAPI.getBooks()
    if (response.data.success) {
      books.value = response.data.data || []
    } else {
      message.error('加载书籍失败')
    }
  } catch (error) {
    console.error('加载书籍失败:', error)
    message.error('加载书籍失败: ' + error.message)
  } finally {
    booksLoading.value = false
  }
}

const selectBook = async (book) => {
  selectedBook.value = book
  selectedChapter.value = null
  chapters.value = []
  await loadChapters()
}

const loadChapters = async () => {
  if (!selectedBook.value) return
  
  try {
    chaptersLoading.value = true
    const response = await readerAPI.getChapters(selectedBook.value.id)
    if (response.data.success) {
      chapters.value = response.data.data || []
    } else {
      message.error('加载章节失败')
    }
  } catch (error) {
    console.error('加载章节失败:', error)
    message.error('加载章节失败: ' + error.message)
  } finally {
    chaptersLoading.value = false
  }
}

const selectChapter = (chapter) => {
  selectedChapter.value = chapter
}

const createAnalysisProject = async () => {
  if (!selectedBook.value || !selectedChapter.value) {
    message.warning('请先选择书籍和章节')
    return
  }
  
  try {
    creatingProject.value = true
    
    // 创建分析项目
    const projectData = {
      book_id: selectedBook.value.id,
      chapter_ids: [selectedChapter.value.id],
      analysis_options: analysisOptions.value,
      name: `环境音分析_${selectedBook.value.title}_第${selectedChapter.value.chapter_number}章`,
      description: `基于《${selectedBook.value.title}》第${selectedChapter.value.chapter_number}章的环境音分析`
    }
    
    // 这里应该调用创建项目的API
    // const response = await environmentGenerationAPI.createProject(projectData)
    
    // 暂时模拟创建成功
    message.success('分析项目创建成功')
    
    // 跳转到详情页面
    router.push({
      name: 'EnvironmentAnalysisDetail',
      params: {
        analysisId: 'new-analysis', // 使用analysisId参数
        bookId: selectedBook.value.id,
        chapterId: selectedChapter.value.id
      }
    })
    
  } catch (error) {
    console.error('创建分析项目失败:', error)
    message.error('创建分析项目失败: ' + error.message)
  } finally {
    creatingProject.value = false
  }
}

const resetSelection = () => {
  selectedBook.value = null
  selectedChapter.value = null
  chapters.value = []
}

const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}
</script>

<style scoped>
.environment-analysis {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.project-header {
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px var(--ant-box-shadow);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title-section {
  flex: 1;
}

.title-with-back {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.back-button {
  margin-right: 12px;
  color: var(--ant-text-color-secondary);
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--ant-text-color);
  display: flex;
  align-items: center;
}

.title-icon {
  margin-right: 8px;
  color: var(--ant-primary-color);
}

.page-description {
  margin: 0;
  color: var(--ant-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.main-content {
  display: flex;
  flex: 1;
  gap: 24px;
  padding: 0 ;
  overflow: hidden;
}

.selection-area {
  flex: 0 0 400px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
}

.analysis-area {
  flex: 1;
  background-color: var(--ant-component-background);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px var(--ant-box-shadow);
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--ant-text-color);
}

.books-list,
.chapters-list {
  max-height: 300px;
  overflow-y: auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: var(--ant-text-color-secondary);
}

.book-item,
.chapter-item {
  padding: 12px 16px;
  margin-bottom: 8px;
  border-radius: 6px;
  background-color: var(--ant-item-hover-bg);
  cursor: pointer;
  transition: all 0.2s ease;
}

.book-item:hover,
.chapter-item:hover {
  background-color: var(--ant-item-active-bg);
  transform: translateX(2px);
  transition: all 0.2s ease;
}

.book-item.active,
.chapter-item.active {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.15), rgba(24, 144, 255, 0.1));
  border: 1px solid var(--ant-primary-color);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.2);
  transform: translateX(4px);
  border-left: 3px solid var(--ant-primary-color);
}

.book-item.active .book-title,
.chapter-item.active .chapter-title {
  color: var(--ant-primary-color);
  font-weight: 600;
}

.book-item.active .book-meta,
.chapter-item.active .chapter-meta {
  color: rgba(24, 144, 255, 0.8);
  font-weight: 500;
}

.book-info,
.chapter-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.book-title,
.chapter-title {
  font-weight: 500;
  color: var(--ant-text-color);
}

.book-meta,
.chapter-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--ant-text-color-secondary);
}

.empty-books,
.empty-chapters {
  padding: 40px 0;
}

.empty-state,
.chapter-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--ant-text-color-secondary);
}

.config-header h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--ant-text-color);
}

.selected-info {
  background: var(--ant-item-hover-bg);
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  margin-bottom: 8px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item .label {
  font-weight: 500;
  color: var(--ant-text-color-secondary);
  min-width: 60px;
}

.info-item .value {
  color: var(--ant-text-color);
}

.analysis-options {
  margin-bottom: 24px;
}

.analysis-options h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--ant-text-color);
}

.analysis-actions {
  display: flex;
  justify-content: center;
  padding-top: 24px;
  border-top: 1px solid var(--ant-border-color-split);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
    gap: 16px;
    padding: 0 16px 16px;
  }
  
  .selection-area {
    flex: none;
    max-height: 300px;
  }
  
  .project-header {
    padding: 16px;
  }
  
  .analysis-area {
    padding: 16px;
  }
}
</style>
