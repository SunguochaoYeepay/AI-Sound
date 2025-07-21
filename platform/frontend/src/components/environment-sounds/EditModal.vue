<template>
  <a-modal
    :open="props.visible"
    title="编辑环境音"
    width="800px"
    :confirm-loading="loading"
    @ok="handleUpdate"
    @cancel="handleCancel"
  >
    <a-form ref="formRef" :model="formData" :rules="rules" layout="vertical" class="edit-form">
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="环境音名称" name="name" required>
            <a-input
              v-model:value="formData.name"
              placeholder="请输入环境音名称"
              :maxlength="100"
              show-count
            />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="分类" name="category_id" required>
            <a-select
              v-model:value="formData.category_id"
              placeholder="请选择分类"
              :options="categoryOptions"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item label="描述" name="description">
        <a-textarea
          v-model:value="formData.description"
          placeholder="请输入环境音描述"
          :rows="3"
          :maxlength="500"
          show-count
        />
      </a-form-item>

      <a-form-item label="生成提示词" name="prompt" required>
        <a-textarea
          v-model:value="formData.prompt"
          placeholder="请输入用于生成环境音的提示词"
          :rows="4"
          :maxlength="1000"
          show-count
        />
      </a-form-item>

      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="音频时长(秒)" name="duration" required>
            <a-input-number
              v-model:value="formData.duration"
              :min="1"
              :max="60"
              :step="0.5"
              placeholder="时长"
              style="width: 100%"
            />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="推理步数" name="steps">
            <a-input-number
              v-model:value="formData.steps"
              :min="10"
              :max="100"
              placeholder="步数"
              style="width: 100%"
            />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="引导强度" name="cfg_scale">
            <a-input-number
              v-model:value="formData.cfg_scale"
              :min="1"
              :max="20"
              :step="0.1"
              placeholder="引导强度"
              style="width: 100%"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item label="标签" name="tag_ids">
        <a-select
          v-model:value="formData.tag_ids"
          mode="multiple"
          placeholder="请选择标签"
          :options="tagOptions"
          :max-tag-count="10"
        />
      </a-form-item>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="设置" name="is_featured">
            <a-checkbox v-model:checked="formData.is_featured"> 设为精选 </a-checkbox>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="状态" name="is_public">
            <a-checkbox v-model:checked="formData.is_public"> 公开显示 </a-checkbox>
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 音频信息展示 -->
      <a-divider orientation="left">音频信息</a-divider>
      <a-row :gutter="16" v-if="props.sound">
        <a-col :span="6">
          <a-statistic title="播放次数" :value="props.sound.play_count || 0" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="下载次数" :value="props.sound.download_count || 0" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="收藏次数" :value="props.sound.favorite_count || 0" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="文件大小" :value="formatFileSize(props.sound.file_size)" />
        </a-col>
      </a-row>

      <a-row :gutter="16" v-if="props.sound" style="margin-top: 16px">
        <a-col :span="12">
          <div class="info-item">
            <span class="label">创建时间：</span>
            <span>{{ formatDateTime(props.sound.created_at) }}</span>
          </div>
        </a-col>
        <a-col :span="12">
          <div class="info-item">
            <span class="label">更新时间：</span>
            <span>{{ formatDateTime(props.sound.updated_at) }}</span>
          </div>
        </a-col>
      </a-row>

      <div
        v-if="props.sound && props.sound.generation_time"
        class="info-item"
        style="margin-top: 8px"
      >
        <span class="label">生成耗时：</span>
        <span>{{ props.sound.generation_time }}秒</span>
      </div>
    </a-form>
  </a-modal>
</template>

<script setup>
  import { ref, reactive, computed, watch } from 'vue'
  import { message } from 'ant-design-vue'
  import apiClient from '@/api/config'

  // Props
  const props = defineProps({
    visible: {
      type: Boolean,
      default: false
    },
    sound: {
      type: Object,
      default: null
    },
    categories: {
      type: Array,
      default: () => []
    },
    tags: {
      type: Array,
      default: () => []
    }
  })

  // Emits
  const emit = defineEmits(['update:visible', 'updated'])

  // 响应式数据
  const loading = ref(false)
  const formRef = ref()

  // 表单数据
  const formData = reactive({
    name: '',
    description: '',
    prompt: '',
    duration: 10,
    steps: 50,
    cfg_scale: 4.5,
    category_id: null,
    tag_ids: [],
    is_featured: false,
    is_public: true
  })

  // 表单验证规则
  const rules = {
    name: [
      { required: true, message: '请输入环境音名称', trigger: 'blur' },
      { max: 100, message: '名称不能超过100个字符', trigger: 'blur' }
    ],
    prompt: [
      { required: true, message: '请输入生成提示词', trigger: 'blur' },
      { max: 1000, message: '提示词不能超过1000个字符', trigger: 'blur' }
    ],
    duration: [
      { required: true, message: '请输入音频时长', trigger: 'blur' },
      { type: 'number', min: 1, max: 60, message: '时长必须在1-60秒之间', trigger: 'blur' }
    ],
    category_id: [{ required: true, message: '请选择分类', trigger: 'change' }]
  }

  // 计算属性
  const categoryOptions = computed(() => {
    return props.categories.map((cat) => ({
      label: cat.name,
      value: cat.id
    }))
  })

  const tagOptions = computed(() => {
    return props.tags.map((tag) => ({
      label: tag.name,
      value: tag.id
    }))
  })

  // 监听弹窗显示状态
  watch(
    () => props.visible,
    (newVal) => {
      if (newVal && props.sound) {
        // 初始化表单数据
        Object.assign(formData, {
          name: props.sound.name || '',
          description: props.sound.description || '',
          prompt: props.sound.prompt || '',
          duration: props.sound.duration || 10,
          steps: props.sound.steps || 50,
          cfg_scale: props.sound.cfg_scale || 4.5,
          category_id: props.sound.category_id || null,
          tag_ids: props.sound.tag_ids || [],
          is_featured: props.sound.is_featured || false,
          is_public: props.sound.is_public !== false // 默认为true
        })
      }
    }
  )

  // 方法
  const handleUpdate = async () => {
    try {
      await formRef.value.validate()
      loading.value = true

      const updateData = { ...formData }

      // 如果标签为空数组，删除该字段
      if (updateData.tag_ids.length === 0) {
        delete updateData.tag_ids
      }

      await apiClient.put(`/environment-sounds/${props.sound.id}`, updateData)

      message.success('环境音更新成功')
      emit('updated')
    } catch (error) {
      console.error('更新环境音失败:', error)
      if (error.response?.data?.detail) {
        message.error(`更新失败: ${error.response.data.detail}`)
      } else {
        message.error('更新失败，请重试')
      }
    } finally {
      loading.value = false
    }
  }

  const handleCancel = () => {
    emit('update:visible', false)
  }

  // 工具方法
  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B'
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }
</script>

<style scoped>
  .edit-form {
    margin-top: 16px;
  }

  .info-item {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }

  .info-item .label {
    font-weight: 500;
    color: #666;
    margin-right: 8px;
    min-width: 80px;
  }

  :deep(.ant-statistic-title) {
    font-size: 12px;
    color: #999;
  }

  :deep(.ant-statistic-content) {
    font-size: 16px;
    color: #333;
  }
</style>
