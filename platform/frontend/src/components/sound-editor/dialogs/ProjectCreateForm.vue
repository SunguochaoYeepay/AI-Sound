<template>
  <a-modal
    :open="open"
    title="创建新项目"
    width="600px"
    @ok="handleOk"
    @cancel="handleCancel"
    @update:open="$emit('update:open', $event)"
  >
    <a-form :model="form" layout="vertical">
      <a-form-item label="项目来源" required>
        <a-radio-group v-model:value="form.sourceType" @change="handleSourceTypeChange">
          <a-radio-button value="book">从书籍导入</a-radio-button>
          <a-radio-button value="manual">手动创建</a-radio-button>
        </a-radio-group>
      </a-form-item>

      <!-- 从书籍导入 -->
      <template v-if="form.sourceType === 'book'">
        <a-form-item label="选择书籍" required>
          <a-select
            v-model:value="form.bookId"
            placeholder="请选择书籍"
            :loading="booksLoading"
            @change="handleBookChange"
            show-search
            :filter-option="filterBookOption"
          >
            <a-select-option v-for="book in books" :key="book.id" :value="book.id">
              {{ book.title }} - {{ book.author }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="选择章节" required v-if="form.bookId">
          <a-select
            v-model:value="form.chapterId"
            placeholder="请选择章节"
            :loading="chaptersLoading"
            @change="handleChapterChange"
          >
            <a-select-option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">
              第{{ chapter.chapter_number }}章 - {{ chapter.title }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="项目标题" required>
          <a-input v-model:value="form.title" placeholder="默认使用章节标题" />
        </a-form-item>
      </template>

      <!-- 手动创建 -->
      <template v-else>
        <a-form-item label="项目标题" required>
          <a-input v-model:value="form.title" placeholder="输入项目标题" />
        </a-form-item>
        <a-form-item label="项目描述">
          <a-textarea v-model:value="form.description" placeholder="项目描述（可选）" :rows="3" />
        </a-form-item>
        <a-form-item label="作者">
          <a-input v-model:value="form.author" placeholder="作者名称" />
        </a-form-item>
      </template>
    </a-form>
  </a-modal>
</template>

<script setup>
  import { reactive, ref, watch } from 'vue'
  import { message } from 'ant-design-vue'
  import { booksAPI } from '../../../api'

  // Props
  const props = defineProps({
    open: {
      type: Boolean,
      default: false
    }
  })

  // Emits
  const emit = defineEmits(['update:open', 'success'])

  // 表单数据
  const form = reactive({
    sourceType: 'book', // 默认从书籍导入
    bookId: null,
    chapterId: null,
    title: '',
    description: '',
    author: 'AI-Sound'
  })

  // 书籍和章节数据
  const books = ref([])
  const chapters = ref([])
  const booksLoading = ref(false)
  const chaptersLoading = ref(false)
  const selectedBook = ref(null)
  const selectedChapter = ref(null)

  // 监听对话框打开
  watch(() => props.open, (newVal) => {
    if (newVal) {
      loadBooks()
    }
  })

  // 加载书籍列表
  async function loadBooks() {
    try {
      booksLoading.value = true
      const response = await booksAPI.getBooks({ page: 1, page_size: 100 })
      if (response.success) {
        books.value = response.data.items || []
      }
    } catch (error) {
      console.error('加载书籍失败:', error)
      message.error('加载书籍列表失败')
    } finally {
      booksLoading.value = false
    }
  }

  // 处理项目来源切换
  function handleSourceTypeChange(e) {
    // 切换时重置相关字段
    if (e.target.value === 'manual') {
      form.bookId = null
      form.chapterId = null
      form.title = ''
      form.description = ''
    }
  }

  // 处理书籍选择
  async function handleBookChange(bookId) {
    try {
      chaptersLoading.value = true
      form.chapterId = null
      chapters.value = []
      
      selectedBook.value = books.value.find(b => b.id === bookId)
      
      const response = await booksAPI.getBookChapters(bookId)
      if (response.success) {
        chapters.value = response.data || []
      }
    } catch (error) {
      console.error('加载章节失败:', error)
      message.error('加载章节列表失败')
    } finally {
      chaptersLoading.value = false
    }
  }

  // 处理章节选择
  function handleChapterChange(chapterId) {
    selectedChapter.value = chapters.value.find(c => c.id === chapterId)
    // 自动填充项目标题
    if (selectedChapter.value && !form.title) {
      form.title = `${selectedBook.value?.title} - ${selectedChapter.value.title}`
    }
  }

  // 书籍搜索过滤
  function filterBookOption(input, option) {
    const book = books.value.find(b => b.id === option.value)
    if (!book) return false
    return book.title.toLowerCase().includes(input.toLowerCase()) ||
           book.author.toLowerCase().includes(input.toLowerCase())
  }

  // 处理确认
  function handleOk() {
    if (form.sourceType === 'book') {
      if (!form.bookId) {
        message.error('请选择书籍')
        return
      }
      if (!form.chapterId) {
        message.error('请选择章节')
        return
      }
      if (!form.title.trim()) {
        message.error('请输入项目标题')
        return
      }

      const projectData = {
        title: form.title,
        description: form.description || `基于《${selectedBook.value?.title}》第${selectedChapter.value?.chapter_number}章`,
        author: selectedBook.value?.author || form.author,
        bookId: form.bookId,
        chapterId: form.chapterId,
        bookTitle: selectedBook.value?.title,
        chapterTitle: selectedChapter.value?.title,
        chapterNumber: selectedChapter.value?.chapter_number
      }

      emit('success', projectData)
      resetForm()
      emit('update:open', false)
    } else {
      // 手动创建模式
      if (!form.title.trim()) {
        message.error('请输入项目标题')
        return
      }

      const projectData = {
        title: form.title,
        description: form.description,
        author: form.author
      }

      emit('success', projectData)
      resetForm()
      emit('update:open', false)
    }
  }

  // 处理取消
  function handleCancel() {
    resetForm()
    emit('update:open', false)
  }

  // 重置表单
  function resetForm() {
    form.sourceType = 'book'
    form.bookId = null
    form.chapterId = null
    form.title = ''
    form.description = ''
    form.author = 'AI-Sound'
    chapters.value = []
    selectedBook.value = null
    selectedChapter.value = null
  }
</script>

<style scoped>
  :deep(.ant-modal-content) {
    background: #2a2a2a;
    color: #fff;
  }

  :deep(.ant-modal-header) {
    background: #333;
    border-bottom: 1px solid #444;
  }

  :deep(.ant-modal-title) {
    color: #fff;
  }

  :deep(.ant-modal-close-x) {
    color: #999;
  }

  :deep(.ant-modal-close-x:hover) {
    color: #fff;
  }
</style>
