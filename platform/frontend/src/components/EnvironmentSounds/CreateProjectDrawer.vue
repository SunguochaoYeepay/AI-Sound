<template>
  <a-drawer
    v-model:open="visible"
    title="创建环境音项目"
    placement="right"
    :width="500"
    :destroy-on-close="true"
    :mask-closable="false"
  >
    <div class="create-project-form">
      <a-form
        :model="formState"
        :rules="rules"
        layout="vertical"
        ref="formRef"
      >
        <a-form-item label="项目名称" name="name">
          <a-input
            v-model:value="formState.name"
            placeholder="请输入项目名称"
            :maxlength="50"
          />
        </a-form-item>

        <a-form-item label="项目描述" name="description">
          <a-textarea
            v-model:value="formState.description"
            placeholder="请描述项目用途和预期效果"
            :rows="4"
            :maxlength="200"
            show-count
          />
        </a-form-item>

        <a-form-item label="关联书籍" name="bookId">
          <a-select
            v-model:value="formState.bookId"
            placeholder="选择关联书籍（可选）"
            allow-clear
            :loading="loadingBooks"
            @focus="loadBooks"
          >
            <a-select-option
              v-for="book in books"
              :key="book.id"
              :value="book.id"
            >
              {{ book.title }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="关联章节" name="chapterIds" v-if="formState.bookId">
          <a-select
            v-model:value="formState.chapterIds"
            placeholder="选择关联章节（可选）"
            mode="multiple"
            allow-clear
            :loading="loadingChapters"
            @focus="loadChapters"
          >
            <a-select-option
              v-for="chapter in chapters"
              :key="chapter.id"
              :value="chapter.id"
            >
              {{ chapter.title }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="环境类型" name="environmentType">
          <a-select
            v-model:value="formState.environmentType"
            placeholder="选择环境类型"
          >
            <a-select-option value="natural">自然环境</a-select-option>
            <a-select-option value="urban">城市环境</a-select-option>
            <a-select-option value="indoor">室内环境</a-select-option>
            <a-select-option value="fantasy">幻想环境</a-select-option>
            <a-select-option value="historical">历史环境</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="音效风格" name="style">
          <a-select
            v-model:value="formState.style"
            placeholder="选择音效风格"
          >
            <a-select-option value="realistic">写实</a-select-option>
            <a-select-option value="atmospheric">氛围</a-select-option>
            <a-select-option value="dramatic">戏剧化</a-select-option>
            <a-select-option value="minimal">极简</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="预期时长（秒）" name="duration">
          <a-input-number
            v-model:value="formState.duration"
            :min="10"
            :max="300"
            :step="5"
            style="width: 100%"
          />
        </a-form-item>

        <a-form-item label="音效元素" name="soundElements">
          <a-checkbox-group v-model:value="formState.soundElements">
            <a-checkbox value="ambient">环境音</a-checkbox>
            <a-checkbox value="effects">特效音</a-checkbox>
            <a-checkbox value="music">背景音乐</a-checkbox>
            <a-checkbox value="voice">人声</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-form>
    </div>

    <div class="drawer-footer">
      <a-button @click="handleCancel" style="margin-right: 8px">
        取消
      </a-button>
      <a-button
        type="primary"
        @click="handleSubmit"
        :loading="loading"
        :disabled="loading"
      >
        创建项目
      </a-button>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, reactive, watch, defineEmits, defineExpose } from 'vue'
import { message } from 'ant-design-vue'
import { api } from '@/api'

const visible = ref(false)
const loading = ref(false)
const loadingBooks = ref(false)
const loadingChapters = ref(false)
const books = ref([])
const chapters = ref([])
const formRef = ref()

const formState = reactive({
  name: '',
  description: '',
  bookId: undefined,
  chapterIds: [],
  environmentType: 'natural',
  style: 'realistic',
  duration: 60,
  soundElements: ['ambient']
})

const rules = {
  name: [
    { required: true, message: '请输入项目名称' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符' }
  ],
  description: [
    { max: 200, message: '描述不能超过 200 个字符' }
  ],
  environmentType: [
    { required: true, message: '请选择环境类型' }
  ],
  style: [
    { required: true, message: '请选择音效风格' }
  ],
  duration: [
    { required: true, type: 'number', min: 10, max: 300, message: '时长必须在 10-300 秒之间' }
  ]
}

const emit = defineEmits(['success'])

const loadBooks = async () => {
  if (books.value.length > 0) return
  
  loadingBooks.value = true
  try {
    const response = await api.get('/books')
    books.value = response.data || []
  } catch (error) {
    console.error('加载书籍失败:', error)
    message.error('加载书籍失败')
  } finally {
    loadingBooks.value = false
  }
}

const loadChapters = async () => {
  if (!formState.bookId) {
    chapters.value = []
    return
  }
  
  loadingChapters.value = true
  try {
    const response = await api.get(`/books/${formState.bookId}/chapters`)
    chapters.value = response.data || []
  } catch (error) {
    console.error('加载章节失败:', error)
    message.error('加载章节失败')
  } finally {
    loadingChapters.value = false
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    loading.value = true
    const response = await api.post('/environment-sounds', formState)
    
    message.success('环境音项目创建成功')
    emit('success', response.data)
    handleClose()
  } catch (error) {
    console.error('创建项目失败:', error)
    if (error.response?.data?.message) {
      message.error(error.response.data.message)
    } else {
      message.error('创建项目失败')
    }
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  handleClose()
}

const handleClose = () => {
  visible.value = false
  formRef.value?.resetFields()
  
  // 重置表单状态
  Object.assign(formState, {
    name: '',
    description: '',
    bookId: undefined,
    chapterIds: [],
    environmentType: 'natural',
    style: 'realistic',
    duration: 60,
    soundElements: ['ambient']
  })
}

const open = () => {
  visible.value = true
}

// 监听书籍变化，清空章节选择
watch(() => formState.bookId, (newBookId) => {
  if (!newBookId) {
    formState.chapterIds = []
    chapters.value = []
  } else {
    loadChapters()
  }
})

// 暴露方法给父组件
defineExpose({
  open
})
</script>

<style scoped>
.create-project-form {
  padding: 0;
}

.drawer-footer {
  position: absolute;
  bottom: 0;
  width: 100%;
  border-top: 1px solid #e8e8e8;
  padding: 16px 24px;
  background: #fff;
  text-align: right;
}

.create-project-form :deep(.ant-form) {
  padding-bottom: 80px;
}

/* 暗黑模式适配 */
[data-theme='dark'] .create-project-form :deep(.ant-form-item-label > label) {
  color: #d1d5db !important;
}

[data-theme='dark'] .drawer-footer {
  background: #1f1f1f !important;
  border-top-color: #434343 !important;
}
</style>