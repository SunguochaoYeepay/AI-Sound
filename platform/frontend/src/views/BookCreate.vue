<template>
  <div class="book-create-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>{{ isEditing ? '✏️ 编辑书籍' : '📝 创建新书籍' }}</h1>
        <p>{{ isEditing ? '修改书籍信息和内容' : '添加新的小说、图书内容到您的资料库' }}</p>
      </div>
      <div class="header-actions">
        <a-button @click="goBack">
          ← 返回
        </a-button>
      </div>
    </div>

    <div class="create-content">
      <a-row :gutter="24">
        <!-- 左侧：基本信息和内容输入 -->
        <a-col :span="16">
          <!-- 基本信息 -->
          <a-card title="📖 基本信息" :bordered="false" class="form-card">
            <a-form :model="bookForm" :rules="bookRules" ref="bookFormRef" layout="vertical">
              <a-row :gutter="16">
                <a-col :span="16">
                  <a-form-item label="书籍标题" name="title" has-feedback>
                    <a-input
                      v-model:value="bookForm.title"
                      placeholder="请输入书籍标题"
                      size="large"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="状态" name="status">
                    <a-select
                      v-model:value="bookForm.status"
                      size="large"
                    >
                      <a-select-option value="draft">草稿</a-select-option>
                      <a-select-option value="published">已发布</a-select-option>
                      <a-select-option value="archived">已归档</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>

              <a-row :gutter="16">
                <a-col :span="12">
                  <a-form-item label="作者" name="author">
                    <a-input
                      v-model:value="bookForm.author"
                      placeholder="请输入作者姓名"
                      size="large"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="标签">
                    <div class="tags-input">
                      <a-tag
                        v-for="tag in bookForm.tags"
                        :key="tag"
                        closable
                        @close="removeTag(tag)"
                      >
                        {{ tag }}
                      </a-tag>
                      <a-input
                        v-if="tagInputVisible"
                        ref="tagInputRef"
                        type="text"
                        size="small"
                        :style="{ width: '78px' }"
                        v-model:value="tagInputValue"
                        @blur="handleTagInputConfirm"
                        @keyup.enter="handleTagInputConfirm"
                      />
                      <a-tag v-else @click="showTagInput" style="background: #fff; border-style: dashed;">
                        <PlusOutlined /> 新标签
                      </a-tag>
                    </div>
                  </a-form-item>
                </a-col>
              </a-row>

              <a-form-item label="书籍描述" name="description">
                <a-textarea
                  v-model:value="bookForm.description"
                  placeholder="请输入书籍描述（可选）"
                  :rows="3"
                  show-count
                  :maxlength="500"
                />
              </a-form-item>
            </a-form>
          </a-card>

          <!-- 内容输入 -->
          <a-card title="📄 书籍内容" :bordered="false" class="form-card">
            <a-tabs v-model:activeKey="contentInputMethod" @change="onContentMethodChange">
              <a-tab-pane key="file" tab="📁 文件上传">
                <div class="upload-section">
                  <a-upload-dragger
                    v-model:fileList="fileList"
                    name="file"
                    :multiple="false"
                    :beforeUpload="beforeUpload"
                    @remove="handleFileRemove"
                    accept=".txt,.md"
                    :showUploadList="true"
                  >
                    <p class="ant-upload-drag-icon">
                      <InboxOutlined style="font-size: 48px; color: #06b6d4;" />
                    </p>
                    <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
                    <p class="ant-upload-hint">
                      支持 .txt 和 .md 格式文件，单次只能上传一个文件
                    </p>
                  </a-upload-dragger>
                  
                  <div v-if="fileContent" class="file-preview">
                    <div class="preview-header">
                      <span>📄 文件预览</span>
                      <span class="file-stats">{{ fileStats.chars }} 字符，约 {{ fileStats.words }} 字</span>
                    </div>
                    <div class="preview-content">
                      {{ fileContent.substring(0, 500) }}{{ fileContent.length > 500 ? '...' : '' }}
                    </div>
                  </div>
                </div>
              </a-tab-pane>

              <a-tab-pane key="input" tab="✏️ 直接输入">
                <div class="input-section">
                  <a-textarea
                    v-model:value="bookForm.content"
                    placeholder="请输入或粘贴书籍内容..."
                    :rows="20"
                    show-count
                    class="content-textarea"
                  />
                </div>
              </a-tab-pane>
            </a-tabs>
          </a-card>
        </a-col>

        <!-- 右侧：预览和操作 -->
        <a-col :span="8">
          <!-- 内容统计 -->
          <a-card title="📊 内容统计" :bordered="false" class="stats-card">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ contentStats.totalChars.toLocaleString() }}</div>
                <div class="stat-label">总字符数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ contentStats.totalWords.toLocaleString() }}</div>
                <div class="stat-label">总字数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ contentStats.estimatedMinutes }}</div>
                <div class="stat-label">预计阅读时长</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ contentStats.estimatedChapters }}</div>
                <div class="stat-label">预估章节数</div>
              </div>
            </div>
          </a-card>

          <!-- 章节预览 -->
          <a-card title="📚 章节预览" :bordered="false" class="preview-card" v-if="detectedChapters.length > 0">
            <div class="chapters-list">
              <div
                v-for="(chapter, index) in detectedChapters.slice(0, 5)"
                :key="index"
                class="chapter-item"
              >
                <div class="chapter-number">第{{ chapter.number }}章</div>
                <div class="chapter-title">{{ chapter.title }}</div>
                <div class="chapter-stats">{{ chapter.wordCount }} 字</div>
              </div>
              <div v-if="detectedChapters.length > 5" class="more-chapters">
                还有 {{ detectedChapters.length - 5 }} 个章节...
              </div>
            </div>
          </a-card>

          <!-- 操作按钮 -->
          <a-card title="🚀 操作" :bordered="false" class="action-card">
            <a-space direction="vertical" style="width: 100%;" :size="16">
              <a-button
                type="primary"
                size="large"
                block
                :loading="saving"
                @click="saveBook"
                :disabled="!canSave"
              >
                <template #icon>
                  <SaveOutlined />
                </template>
                {{ isEditing ? '保存修改' : '创建书籍' }}
              </a-button>
              
              <a-button
                size="large"
                block
                @click="previewContent"
                :disabled="!currentContent"
              >
                <template #icon>
                  <EyeOutlined />
                </template>
                预览内容
              </a-button>
              
              <a-button
                size="large"
                block
                @click="detectChapters"
                :loading="detectingChapters"
                :disabled="!currentContent"
              >
                <template #icon>
                  <BookOutlined />
                </template>
                检测章节
              </a-button>
            </a-space>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 内容预览弹窗 -->
    <a-modal
      v-model:open="previewModal.visible"
      title="📖 内容预览"
      width="80%"
      :footer="null"
    >
      <div class="content-preview">
        {{ previewModal.content }}
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  InboxOutlined,
  SaveOutlined,
  EyeOutlined,
  BookOutlined
} from '@ant-design/icons-vue'
import { booksAPI } from '@/api'

const router = useRouter()
const route = useRoute()

// 响应式数据
const saving = ref(false)
const loading = ref(false)
const detectingChapters = ref(false)

const bookFormRef = ref()
const tagInputRef = ref()

const isEditing = computed(() => !!route.params.id)

const bookForm = reactive({
  title: '',
  author: '',
  description: '',
  content: '',
  tags: [],
  status: 'draft'
})

const bookRules = {
  title: [
    { required: true, message: '请输入书籍标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
  ]
}

// 标签输入
const tagInputVisible = ref(false)
const tagInputValue = ref('')

// 内容输入方式
const contentInputMethod = ref('input')
const fileList = ref([])
const fileContent = ref('')

// 检测到的章节
const detectedChapters = ref([])

// 预览弹窗
const previewModal = reactive({
  visible: false,
  content: ''
})

// 计算属性
const currentContent = computed(() => {
  return contentInputMethod.value === 'file' ? fileContent.value : bookForm.content
})

const contentStats = computed(() => {
  const content = currentContent.value || ''
  const totalChars = content.length
  const totalWords = content.replace(/\s/g, '').length
  const estimatedMinutes = Math.ceil(totalWords / 300) // 假设每分钟阅读300字
  const estimatedChapters = Math.max(1, Math.ceil(totalWords / 3000)) // 假设每章3000字
  
  return {
    totalChars,
    totalWords,
    estimatedMinutes: estimatedMinutes + ' 分钟',
    estimatedChapters
  }
})

const fileStats = computed(() => {
  const content = fileContent.value || ''
  return {
    chars: content.length,
    words: content.replace(/\s/g, '').length
  }
})

const canSave = computed(() => {
  return bookForm.title.trim() && currentContent.value.trim()
})

// 方法
const goBack = () => {
  router.push('/books')
}

// 标签管理
const removeTag = (removedTag) => {
  bookForm.tags = bookForm.tags.filter(tag => tag !== removedTag)
}

const showTagInput = () => {
  tagInputVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const handleTagInputConfirm = () => {
  const inputValue = tagInputValue.value.trim()
  if (inputValue && !bookForm.tags.includes(inputValue)) {
    bookForm.tags.push(inputValue)
  }
  tagInputVisible.value = false
  tagInputValue.value = ''
}

// 文件处理
const beforeUpload = (file) => {
  const isValidType = file.name.toLowerCase().endsWith('.txt') || file.name.toLowerCase().endsWith('.md')
  if (!isValidType) {
    message.error('只支持 .txt 和 .md 格式文件')
    return false
  }

  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    message.error('文件大小不能超过 50MB')
    return false
  }

  // 读取文件内容
  const reader = new FileReader()
  reader.onload = (e) => {
    fileContent.value = e.target.result
    message.success('文件读取成功')
  }
  reader.onerror = () => {
    message.error('文件读取失败')
  }
  reader.readAsText(file, 'UTF-8')

  return false // 阻止自动上传
}

const handleFileRemove = () => {
  fileContent.value = ''
  return true
}

const onContentMethodChange = (key) => {
  contentInputMethod.value = key
}

// 章节检测
const detectChapters = async () => {
  if (!currentContent.value) {
    message.warning('请先输入内容')
    return
  }

  // 如果是编辑模式且有书籍ID，使用后端API检测
  if (isEditing.value && route.params.id) {
    detectingChapters.value = true
    try {
      console.log('[BookCreate] 使用后端API检测章节，书籍ID:', route.params.id)
      const response = await booksAPI.detectChapters(route.params.id, { force_reprocess: true })
      
      if (response.data && response.data.success) {
        message.success(response.data.message || '章节检测完成')
        // 更新检测到的章节数据用于预览
        if (response.data.chapters) {
          detectedChapters.value = response.data.chapters.map(ch => ({
            number: ch.number,
            title: ch.title,
            wordCount: ch.word_count
          }))
        }
      }
    } catch (error) {
      console.error('[BookCreate] 后端章节检测失败:', error)
      message.error('章节检测失败: ' + (error.response?.data?.detail || '未知错误'))
    } finally {
      detectingChapters.value = false
    }
    return
  }

  // 创建模式使用前端检测逻辑
  detectingChapters.value = true
  try {
    // 简单的章节检测逻辑（前端实现）
    const content = currentContent.value
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
          end: 0,
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
    
    // 如果没有检测到章节，创建默认章节
    if (chapters.length === 0) {
      chapters.push({
        number: 1,
        title: '全文',
        start: 0,
        end: content.length,
        wordCount: content.replace(/\s/g, '').length
      })
    }
    
    detectedChapters.value = chapters
    message.success(`检测到 ${chapters.length} 个章节`)
    
  } catch (error) {
    console.error('章节检测失败:', error)
    message.error('章节检测失败')
  } finally {
    detectingChapters.value = false
  }
}

// 内容预览
const previewContent = () => {
  previewModal.content = currentContent.value
  previewModal.visible = true
}

// 保存书籍
const saveBook = async () => {
  try {
    await bookFormRef.value.validate()
  } catch (error) {
    message.error('请检查表单内容')
    return
  }

  if (!currentContent.value.trim()) {
    message.error('请输入书籍内容')
    return
  }

  saving.value = true
  try {
    const bookData = {
      title: bookForm.title,
      author: bookForm.author,
      description: bookForm.description,
      content: currentContent.value,
      tags: bookForm.tags,
      status: bookForm.status
    }

    // 如果是文件上传，添加文件信息
    if (contentInputMethod.value === 'file' && fileList.value.length > 0) {
      bookData.text_file = fileList.value[0].originFileObj
    }

    let response
    if (isEditing.value) {
      response = await booksAPI.updateBook(route.params.id, bookData)
    } else {
      response = await booksAPI.createBook(bookData)
    }

    if (response.data.success) {
      message.success(isEditing.value ? '书籍更新成功' : '书籍创建成功')
      router.push('/books')
    }
  } catch (error) {
    console.error('保存书籍失败:', error)
    const errorMsg = error.response?.data?.detail || '保存失败'
    message.error(errorMsg)
  } finally {
    saving.value = false
  }
}

// 加载书籍数据（编辑模式）
const loadBook = async () => {
  if (!isEditing.value) return

  loading.value = true
  try {
    const response = await booksAPI.getBookDetail(route.params.id)
    if (response.data.success) {
      const book = response.data.data
      bookForm.title = book.title
      bookForm.author = book.author
      bookForm.description = book.description
      bookForm.content = book.content
      bookForm.tags = book.tags || []
      bookForm.status = book.status
      
      // 不自动检测章节，避免覆盖已有的后端章节数据
      // await detectChapters()
    }
  } catch (error) {
    console.error('加载书籍数据失败:', error)
    message.error('加载书籍数据失败')
    router.push('/books')
  } finally {
    loading.value = false
  }
}

// 监听内容变化，自动检测章节
watch(currentContent, async (newContent) => {
  if (newContent && newContent.length > 100) {
    // 延迟检测，避免频繁触发
    setTimeout(() => {
      if (currentContent.value === newContent) {
        detectChapters()
      }
    }, 2000)
  }
}, { debounce: 1000 })

// 生命周期
onMounted(() => {
  if (isEditing.value) {
    loadBook()
  }
})
</script>

<style scoped>
.book-create-container {
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

.create-content {
  margin-bottom: 24px;
}

.form-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stats-card, .preview-card, .action-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.tags-input {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.upload-section {
  margin-bottom: 16px;
}

.file-preview {
  margin-top: 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 500;
}

.file-stats {
  font-size: 12px;
  color: #6b7280;
}

.preview-content {
  padding: 16px;
  max-height: 200px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.content-textarea {
  font-family: 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  line-height: 1.6;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
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

.chapters-list {
  max-height: 300px;
  overflow-y: auto;
}

.chapter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.chapter-item:last-child {
  border-bottom: none;
}

.chapter-number {
  font-size: 12px;
  color: #6b7280;
  min-width: 60px;
}

.chapter-title {
  flex: 1;
  font-size: 14px;
  margin: 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chapter-stats {
  font-size: 12px;
  color: #9ca3af;
}

.more-chapters {
  text-align: center;
  padding: 8px 0;
  color: #6b7280;
  font-size: 12px;
}

.content-preview {
  max-height: 60vh;
  overflow-y: auto;
  white-space: pre-wrap;
  font-family: 'Microsoft YaHei', sans-serif;
  line-height: 1.6;
  padding: 16px;
  background: #f8fafc;
  border-radius: 6px;
}
</style> 