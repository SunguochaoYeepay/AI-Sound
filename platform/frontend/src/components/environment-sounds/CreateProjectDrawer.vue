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

      <!-- 第一步：选择书籍 -->
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

      <!-- 第二步：选择书籍分析项目 -->
      <a-form-item 
        v-if="formData.book_id" 
        label="选择书籍分析项目" 
        name="novel_project_id"
      >
        <a-select
          v-model:value="formData.novel_project_id"
          placeholder="请选择该书籍的书籍分析项目"
          allow-clear
          :loading="projectsLoading"
          @change="handleProjectChange"
        >
          <a-select-option
            v-for="project in novelProjects"
            :key="project.id"
            :value="project.id"
          >
            {{ project.name || '未命名项目' }} (ID: {{ project.id }})
          </a-select-option>
        </a-select>
        <div class="form-help-text">
          <InfoCircleOutlined />
          选择已完成的书籍分析项目，环境音分析将直接使用该项目的分析结果
        </div>
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
import { InfoCircleOutlined } from '@ant-design/icons-vue'
import { environmentGenerationAPI, readerAPI } from '@/api'

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
const projectsLoading = ref(false)
const novelProjects = ref([])

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  book_id: null,
  novel_project_id: null
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
  ],
  novel_project_id: [
    { required: true, message: '请选择书籍分析项目', trigger: 'change' }
  ]
}

// 监听书籍变化
const handleBookChange = async (bookId) => {
  if (!bookId) {
    // 清空书籍分析项目选择
    formData.novel_project_id = null
    novelProjects.value = []
    return
  }
  
  console.log('选择的书籍ID:', bookId)
  
  // 加载该书籍的书籍分析项目列表
  try {
    projectsLoading.value = true
    const response = await readerAPI.getProjects({ book_id: bookId })
    
    if (response.data.success) {
      // 处理API返回的数据结构
      const responseData = response.data.data
      let projects = []
      
      if (Array.isArray(responseData)) {
        // 直接是数组
        projects = responseData
      } else if (responseData && Array.isArray(responseData.projects)) {
        // 是包含projects字段的对象
        projects = responseData.projects
      } else {
        projects = []
      }
      
      novelProjects.value = projects
      
      console.log('加载到书籍分析项目:', novelProjects.value.length, '个')
      console.log('项目数据详情:', novelProjects.value)
      
      // 检查每个项目的字段
      novelProjects.value.forEach((project, index) => {
        console.log(`项目 ${index + 1}:`, {
          id: project.id,
          name: project.name,
          book_id: project.book_id,
          status: project.status
        })
      })
      
      if (novelProjects.value.length === 0) {
        message.warning('该书籍还没有书籍分析项目，请先进行书籍分析')
      }
    } else {
      message.error('加载书籍分析项目失败')
      novelProjects.value = []
    }
  } catch (error) {
    console.error('加载书籍分析项目失败:', error)
    message.error('加载书籍分析项目失败')
    novelProjects.value = []
  } finally {
    projectsLoading.value = false
  }
}

// 监听书籍分析项目变化
const handleProjectChange = (projectId) => {
  console.log('选择的书籍分析项目ID:', projectId)
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    // 构建创建项目的数据 - 关联书籍分析项目
    const projectData = {
      name: formData.name,
      description: formData.description,
      book_id: formData.book_id,
      novel_project_id: formData.novel_project_id,  // 关联书籍分析项目
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
    book_id: null,
    novel_project_id: null
  })
  
  // 清空书籍分析项目列表
  novelProjects.value = []
  
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

.form-help-text {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f6f8fa;
  border-radius: 4px;
  color: #666;
  font-size: 12px;
  line-height: 1.4;
}

.form-help-text .anticon {
  margin-right: 4px;
  color: #1890ff;
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
