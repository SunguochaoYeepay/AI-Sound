<template>
  <div class="book-chapter-selector">
    <div class="selector-header">
      <h2 class="selector-title">从书籍导入资源</h2>
      <p class="selector-description">选择书籍章节，导入对话音频和环境音效到编辑器项目</p>
    </div>

    <!-- 步骤导航 -->
    <a-steps :current="currentStep" size="small" class="selector-steps">
      <a-step title="选择书籍" />
      <a-step title="选择章节" />
      <a-step title="选择资源" />
      <a-step title="创建项目" />
    </a-steps>

    <!-- 步骤1: 选择书籍 -->
    <div v-if="currentStep === 0" class="step-content">
      <div class="step-header">
        <h3>选择一本书籍</h3>
        <a-input-search
          v-model:value="bookSearchTerm"
          placeholder="搜索书籍名称..."
          style="width: 300px"
          @search="searchBooks"
        />
      </div>

      <a-spin :spinning="loadingBooks">
        <div v-if="books.length === 0" class="empty-state">
          <p>暂无可用书籍</p>
        </div>
        <div v-else class="books-grid">
          <div
            v-for="book in books"
            :key="book.id"
            class="book-card"
            :class="{ 'selected': selectedBook?.id === book.id }"
            @click="selectBook(book)"
          >
            <div class="book-info">
              <h4 class="book-title">{{ book.title }}</h4>
              <p class="book-author">{{ book.author }}</p>
              <div class="book-stats">
                <span class="stat-item">{{ book.chapter_count }}章</span>
                <span class="stat-item">{{ book.word_count }}字</span>
                <span class="stat-item">{{ book.character_count }}角色</span>
              </div>
            </div>
            <div class="book-status">
              <a-tag :color="book.status === 'completed' ? 'green' : 'blue'">
                {{ book.status === 'completed' ? '已完成' : '进行中' }}
              </a-tag>
            </div>
          </div>
        </div>
      </a-spin>
    </div>

    <!-- 步骤2: 选择章节 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="step-header">
        <h3>选择章节</h3>
        <div class="header-actions">
          <a-button type="link" @click="selectAllChapters">全选</a-button>
          <a-button type="link" @click="deselectAllChapters">取消全选</a-button>
        </div>
      </div>

      <a-spin :spinning="loadingChapters">
        <div v-if="chapters.length === 0" class="empty-state">
          <p>暂无可用章节</p>
        </div>
        <div v-else class="chapters-list">
          <a-checkbox-group v-model:value="selectedChapterIds">
            <div v-for="chapter in chapters" :key="chapter.id" class="chapter-item">
              <a-checkbox :value="chapter.id">
                <div class="chapter-info">
                  <div class="chapter-title">第{{ chapter.chapter_number }}章: {{ chapter.title }}</div>
                  <div class="chapter-stats">
                    <span class="stat-item">{{ chapter.word_count }}字</span>
                    <span v-if="chapter.audio_files_count > 0" class="stat-item has-resource">
                      {{ chapter.audio_files_count }}个音频
                    </span>
                    <span v-if="chapter.environment_configs_count > 0" class="stat-item has-resource">
                      {{ chapter.environment_configs_count }}个环境音配置
                    </span>
                  </div>
                </div>
              </a-checkbox>
            </div>
          </a-checkbox-group>
        </div>
      </a-spin>
    </div>

    <!-- 步骤3: 选择资源 -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="step-header">
        <h3>选择资源</h3>
      </div>

      <a-spin :spinning="loadingResources">
        <div v-if="!chapterResources" class="empty-state">
          <p>暂无可用资源</p>
        </div>
        <div v-else class="resources-container">
          <!-- 对话音频资源 -->
          <div class="resource-section">
            <div class="section-header">
              <h4>对话音频 ({{ chapterResources.dialogue_audio?.length || 0 }}个)</h4>
              <div class="header-actions">
                <a-button type="link" size="small" @click="selectAllDialogueAudio">全选</a-button>
                <a-button type="link" size="small" @click="deselectAllDialogueAudio">取消全选</a-button>
              </div>
            </div>
            
            <div v-if="!chapterResources.dialogue_audio?.length" class="empty-resource">
              <p>所选章节没有对话音频</p>
            </div>
            <div v-else class="resource-list">
              <a-checkbox-group v-model:value="selectedResources.dialogue_audio">
                <div v-for="audio in chapterResources.dialogue_audio" :key="audio.id" class="resource-item">
                  <a-checkbox :value="audio.id">
                    <div class="resource-info">
                      <div class="resource-name">{{ audio.original_name || audio.filename }}</div>
                      <div class="resource-meta">
                        <span class="meta-item">第{{ audio.chapter_number }}章</span>
                        <span class="meta-item">{{ formatDuration(audio.duration) }}</span>
                        <span class="meta-item">{{ formatFileSize(audio.file_size) }}</span>
                      </div>
                    </div>
                  </a-checkbox>
                </div>
              </a-checkbox-group>
            </div>
          </div>

          <!-- 环境音配置资源 -->
          <div class="resource-section">
            <div class="section-header">
              <h4>环境音配置 ({{ chapterResources.environment_configs?.length || 0 }}个)</h4>
              <div class="header-actions">
                <a-button type="link" size="small" @click="selectAllEnvironmentConfigs">全选</a-button>
                <a-button type="link" size="small" @click="deselectAllEnvironmentConfigs">取消全选</a-button>
              </div>
            </div>
            
            <div v-if="!chapterResources.environment_configs?.length" class="empty-resource">
              <p>所选章节没有环境音配置</p>
            </div>
            <div v-else class="resource-list">
              <a-checkbox-group v-model:value="selectedResources.environment_configs">
                <div v-for="config in chapterResources.environment_configs" :key="config.session_id" class="resource-item">
                  <a-checkbox :value="config.session_id">
                    <div class="resource-info">
                      <div class="resource-name">第{{ config.chapter_number }}章环境音配置</div>
                      <div class="resource-meta">
                        <span class="meta-item">{{ config.track_count }}个轨道</span>
                        <span class="meta-item">{{ formatDuration(config.total_duration) }}</span>
                      </div>
                    </div>
                  </a-checkbox>
                </div>
              </a-checkbox-group>
            </div>
          </div>
        </div>
      </a-spin>
    </div>

    <!-- 步骤4: 创建项目 -->
    <div v-if="currentStep === 3" class="step-content">
      <div class="step-header">
        <h3>创建项目</h3>
      </div>

      <a-form :model="projectForm" layout="vertical">
        <a-form-item label="项目名称" required>
          <a-input
            v-model:value="projectForm.name"
            placeholder="输入项目名称"
            :maxlength="50"
          />
        </a-form-item>
        
        <a-form-item label="项目描述">
          <a-textarea
            v-model:value="projectForm.description"
            placeholder="输入项目描述（可选）"
            :rows="3"
            :maxlength="200"
          />
        </a-form-item>

        <div class="resource-summary">
          <h4>资源摘要</h4>
          <div class="summary-content">
            <p><strong>书籍:</strong> {{ selectedBook?.title }}</p>
            <p><strong>选中章节:</strong> {{ selectedChapterIds.length }}章</p>
            <p><strong>对话音频:</strong> {{ selectedResources.dialogue_audio.length }}个</p>
            <p><strong>环境音配置:</strong> {{ selectedResources.environment_configs.length }}个</p>
            <p><strong>估计总时长:</strong> {{ formatDuration(estimatedTotalDuration) }}</p>
          </div>
        </div>
      </a-form>
    </div>

    <!-- 导航按钮 -->
    <div class="step-actions">
      <a-button v-if="currentStep > 0" @click="prevStep">上一步</a-button>
      <a-button
        v-if="currentStep < 3"
        type="primary"
        @click="nextStep"
        :disabled="!canProceed"
      >
        下一步
      </a-button>
      <a-button
        v-else
        type="primary"
        @click="createProject"
        :loading="creatingProject"
      >
        创建项目
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  getAvailableBooks,
  getBookChapters,
  getChapterResources,
  createProjectFromChapters
} from '@/api/sound-editor/bookIntegration'

const router = useRouter()
const emit = defineEmits(['created'])

// 步骤状态
const currentStep = ref(0)
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0: return !!selectedBook.value
    case 1: return selectedChapterIds.value.length > 0
    case 2: return selectedResources.value.dialogue_audio.length > 0 || 
                   selectedResources.value.environment_configs.length > 0
    case 3: return !!projectForm.value.name
    default: return false
  }
})

// 书籍选择状态
const books = ref([])
const selectedBook = ref(null)
const bookSearchTerm = ref('')
const loadingBooks = ref(false)

// 章节选择状态
const chapters = ref([])
const selectedChapterIds = ref([])
const loadingChapters = ref(false)

// 资源选择状态
const chapterResources = ref(null)
const selectedResources = ref({
  dialogue_audio: [],
  environment_configs: []
})
const loadingResources = ref(false)

// 项目创建状态
const projectForm = ref({
  name: '',
  description: ''
})
const creatingProject = ref(false)
const estimatedTotalDuration = ref(0)

// 初始化加载书籍列表
const initSelector = async () => {
  loadingBooks.value = true
  try {
    const response = await getAvailableBooks()
    if (response && response.success) {
      books.value = response.data || []
    } else {
      message.error('加载书籍列表失败')
    }
  } catch (error) {
    console.error('加载书籍列表失败:', error)
    message.error('加载书籍列表失败')
  } finally {
    loadingBooks.value = false
  }
}

// 搜索书籍
const searchBooks = () => {
  if (!bookSearchTerm.value) {
    return
  }
  
  const searchTerm = bookSearchTerm.value.toLowerCase()
  books.value = books.value.filter(book => 
    book.title.toLowerCase().includes(searchTerm) || 
    book.author.toLowerCase().includes(searchTerm)
  )
}

// 选择书籍
const selectBook = async (book) => {
  selectedBook.value = book
  selectedChapterIds.value = []
  chapterResources.value = null
  
  // 自动加载章节
  await loadChapters(book.id)
}

// 加载章节
const loadChapters = async (bookId) => {
  loadingChapters.value = true
  try {
    const response = await getBookChapters(bookId)
    if (response && response.success) {
      chapters.value = response.data || []
    } else {
      message.error('加载章节列表失败')
    }
  } catch (error) {
    console.error('加载章节列表失败:', error)
    message.error('加载章节列表失败')
  } finally {
    loadingChapters.value = false
  }
}

// 全选/取消全选章节
const selectAllChapters = () => {
  selectedChapterIds.value = chapters.value.map(chapter => chapter.id)
}

const deselectAllChapters = () => {
  selectedChapterIds.value = []
}

// 加载章节资源
const loadChapterResources = async () => {
  if (!selectedBook.value || selectedChapterIds.value.length === 0) {
    return
  }
  
  loadingResources.value = true
  try {
    const response = await getChapterResources(selectedBook.value.id, selectedChapterIds.value)
    if (response && response.success) {
      chapterResources.value = response.data || {}
      
      // 默认全选资源
      if (chapterResources.value.dialogue_audio) {
        selectedResources.value.dialogue_audio = chapterResources.value.dialogue_audio.map(audio => audio.id)
      }
      
      if (chapterResources.value.environment_configs) {
        selectedResources.value.environment_configs = chapterResources.value.environment_configs.map(config => config.session_id)
      }
      
      // 更新估计总时长
      if (chapterResources.value.resource_summary) {
        estimatedTotalDuration.value = chapterResources.value.resource_summary.estimated_total_duration || 0
      }
      
      // 设置默认项目名称
      projectForm.value.name = `《${selectedBook.value.title}》音频编辑`
      projectForm.value.description = `基于《${selectedBook.value.title}》的${selectedChapterIds.value.length}个章节创建的音频项目`
    } else {
      message.error('加载章节资源失败')
    }
  } catch (error) {
    console.error('加载章节资源失败:', error)
    message.error('加载章节资源失败')
  } finally {
    loadingResources.value = false
  }
}

// 全选/取消全选资源
const selectAllDialogueAudio = () => {
  if (chapterResources.value && chapterResources.value.dialogue_audio) {
    selectedResources.value.dialogue_audio = chapterResources.value.dialogue_audio.map(audio => audio.id)
  }
}

const deselectAllDialogueAudio = () => {
  selectedResources.value.dialogue_audio = []
}

const selectAllEnvironmentConfigs = () => {
  if (chapterResources.value && chapterResources.value.environment_configs) {
    selectedResources.value.environment_configs = chapterResources.value.environment_configs.map(config => config.session_id)
  }
}

const deselectAllEnvironmentConfigs = () => {
  selectedResources.value.environment_configs = []
}

// 步骤导航
const nextStep = async () => {
  if (currentStep.value === 1 && selectedChapterIds.value.length > 0) {
    // 从步骤2到步骤3时，加载章节资源
    await loadChapterResources()
  }
  
  currentStep.value++
}

const prevStep = () => {
  currentStep.value--
}

// 创建项目
const createProject = async () => {
  if (!projectForm.value.name) {
    message.error('请输入项目名称')
    return
  }
  
  creatingProject.value = true
  try {
    const response = await createProjectFromChapters(
      projectForm.value.name,
      selectedBook.value.id,
      selectedChapterIds.value,
      selectedResources.value
    )
    
    if (response && response.success) {
      message.success('项目创建成功')
      
      // 发送创建成功事件
      emit('created', {
        projectId: response.data.project_id,
        summary: response.data.resource_summary
      })
      
      // 导航到编辑器页面
      router.push(`/sound-editor/edit/${response.data.project_id}`)
    } else {
      message.error(response?.message || '创建项目失败')
    }
  } catch (error) {
    console.error('创建项目失败:', error)
    message.error('创建项目失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    creatingProject.value = false
  }
}

// 工具函数
const formatDuration = (seconds) => {
  if (!seconds || seconds <= 0) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

// 初始化
initSelector()
</script>

<style scoped>
.book-chapter-selector {
  padding: 20px;
}

.selector-header {
  margin-bottom: 20px;
}

.selector-title {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.selector-description {
  margin: 0;
  color: #666;
}

.selector-steps {
  margin-bottom: 30px;
}

.step-content {
  margin-bottom: 30px;
  min-height: 300px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.step-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #999;
}

.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.book-card {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
}

.book-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.book-card.selected {
  border-color: #1890ff;
  background-color: #e6f7ff;
}

.book-title {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
}

.book-author {
  margin: 0 0 8px 0;
  color: #666;
}

.book-stats {
  display: flex;
  gap: 12px;
}

.stat-item {
  font-size: 12px;
  color: #666;
}

.chapters-list {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  max-height: 400px;
  overflow-y: auto;
}

.chapter-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.chapter-item:last-child {
  border-bottom: none;
}

.chapter-info {
  margin-left: 8px;
}

.chapter-title {
  font-weight: 500;
}

.chapter-stats {
  margin-top: 4px;
  display: flex;
  gap: 12px;
}

.has-resource {
  color: #1890ff;
}

.resources-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.resource-section {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.empty-resource {
  text-align: center;
  padding: 20px 0;
  color: #999;
}

.resource-list {
  max-height: 300px;
  overflow-y: auto;
}

.resource-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.resource-item:last-child {
  border-bottom: none;
}

.resource-info {
  margin-left: 8px;
}

.resource-name {
  font-weight: 500;
}

.resource-meta {
  margin-top: 4px;
  display: flex;
  gap: 12px;
}

.meta-item {
  font-size: 12px;
  color: #666;
}

.resource-summary {
  margin-top: 20px;
  background-color: #f5f5f5;
  border-radius: 6px;
  padding: 16px;
}

.resource-summary h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
}

.summary-content p {
  margin: 8px 0;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
}
</style> 