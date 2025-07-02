<template>
  <a-modal
    :open="open"
    title="创建新项目"
    @ok="handleOk"
    @cancel="handleCancel"
    @update:open="$emit('update:open', $event)"
  >
    <a-form :model="form" layout="vertical">
      <a-form-item label="项目标题" required>
        <a-input v-model:value="form.title" placeholder="输入项目标题" />
      </a-form-item>
      <a-form-item label="项目描述">
        <a-textarea v-model:value="form.description" placeholder="项目描述（可选）" :rows="3" />
      </a-form-item>
      <a-form-item label="作者">
        <a-input v-model:value="form.author" placeholder="作者名称" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { reactive } from 'vue'
import { message } from 'ant-design-vue'

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
  title: '',
  description: '',
  author: 'AI-Sound'
})

// 处理确认
function handleOk() {
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

// 处理取消
function handleCancel() {
  resetForm()
  emit('update:open', false)
}

// 重置表单
function resetForm() {
  form.title = ''
  form.description = ''
  form.author = 'AI-Sound'
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