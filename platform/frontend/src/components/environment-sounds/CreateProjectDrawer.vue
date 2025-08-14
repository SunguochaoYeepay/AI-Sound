<template>
  <a-drawer
    :open="open"
    title="新建环境音分析项目"
    width="600px"
    placement="right"
    @close="handleClose"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      layout="vertical"
      @finish="handleSubmit"
    >
      <!-- 项目名称 -->
      <a-form-item label="项目名称" name="name">
        <a-input
          v-model:value="formData.name"
          placeholder="请输入项目名称"
          allow-clear
        />
      </a-form-item>

      <!-- 项目描述 -->
      <a-form-item label="项目描述" name="description">
        <a-textarea
          v-model:value="formData.description"
          placeholder="请输入项目描述"
          :rows="3"
          allow-clear
        />
      </a-form-item>

      <!-- 选择书籍 -->
      <a-form-item label="选择书籍" name="book_id">
        <a-select
          v-model:value="formData.book_id"
          placeholder="请选择要分析的书籍"
          allow-clear
          :loading="loading"
          @change="handleBookChange"
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

      <!-- 分析选项 -->
      <a-form-item label="分析选项">
        <a-space direction="vertical" style="width: 100%">
          <a-checkbox v-model:checked="formData.auto_analyze">
            自动分析书籍内容
          </a-checkbox>
          <a-checkbox v-model:checked="formData.create_tracks">
            自动创建环境音轨道
          </a-checkbox>
        </a-space>
      </a-form-item>


    </a-form>

    <!-- 抽屉底部操作 -->
    <template #footer>
      <a-space>
        <a-button @click="handleClose">取消</a-button>
        <a-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          创建项目
        </a-button>
      </a-space>
    </template>
  </a-drawer>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { environmentGenerationAPI } from '@/api'

// Props
const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  books: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:open', 'create'])

// 响应式数据
const formRef = ref()
const submitting = ref(false)

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  book_id: null,
  auto_analyze: true,
  create_tracks: true
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '项目名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '项目描述不能超过 200 个字符', trigger: 'blur' }
  ],
  book_id: [
    { required: true, message: '请选择要分析的书籍', trigger: 'change' }
  ]
}

// 监听书籍变化
const handleBookChange = async (bookId) => {
  if (!bookId) {
    return
  }
  
  // 可以在这里加载书籍详情信息
  console.log('选择的书籍ID:', bookId)
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    // 构建创建项目的数据 - 基于书籍，不指定章节
    const projectData = {
      name: formData.name,
      description: formData.description,
      book_id: formData.book_id,
      // 移除 chapter_ids，让后端分析整本书
      options: {
        auto_analyze: formData.auto_analyze,
        create_tracks: formData.create_tracks
      }
    }

    // 调用创建项目API
    const response = await environmentGenerationAPI.createProject(projectData)
    
    if (response.data.success) {
      message.success('项目创建成功')
      emit('create', response.data.data)
      handleClose()
    } else {
      message.error('项目创建失败')
    }
  } catch (error) {
    console.error('创建项目失败:', error)
    message.error('创建项目失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

// 关闭抽屉
const handleClose = () => {
  // 重置表单
  formRef.value?.resetFields()
  Object.assign(formData, {
    name: '',
    description: '',
    book_id: null,
    auto_analyze: true,
    create_tracks: true
  })
  
  emit('update:open', false)
}

// 监听open变化，重置表单
watch(() => props.open, (newVal) => {
  if (!newVal) {
    handleClose()
  }
})
</script>

<style scoped>
.ant-drawer-body {
  padding: 24px;
}

.ant-form-item {
  margin-bottom: 24px;
}

.ant-form-item-label {
  font-weight: 500;
}

.ant-select {
  width: 100%;
}

.ant-checkbox-wrapper {
  margin-bottom: 8px;
}
</style>
