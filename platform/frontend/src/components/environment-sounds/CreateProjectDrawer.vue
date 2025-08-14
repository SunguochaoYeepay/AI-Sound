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

      <!-- 项目说明 -->
      <a-form-item label="项目说明">
        <a-alert
          message="项目创建说明"
          description="项目创建后，您需要在详情页面选择具体章节，然后手动触发分析。这样可以避免一次性分析整本书的所有章节，提高效率。"
          type="info"
          show-icon
        />
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
  book_id: null
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

    // 构建创建项目的数据 - 仅创建项目，不进行任何分析
    const projectData = {
      name: formData.name,
      description: formData.description,
      book_id: formData.book_id,
      // 不进行任何分析，用户需要在详情页面手动选择章节并分析
      analysis_options: {
        auto_analyze: false,  // 不自动分析
        create_tracks: false  // 不自动创建轨道
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
    book_id: null
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
