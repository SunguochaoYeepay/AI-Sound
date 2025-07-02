<template>
  <a-modal
    :open="open"
    title="导入JSON格式"
    width="800px"
    @ok="handleOk"
    @cancel="handleCancel"
    @update:open="$emit('update:open', $event)"
  >
    <ImportJsonFormComponent v-model="importData" />
  </a-modal>
</template>

<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import ImportJsonFormComponent from '../import/ImportJsonForm.vue'

// Props
const props = defineProps({
  open: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:open', 'success'])

// 导入数据
const importData = ref({})

// 处理确认
function handleOk() {
  if (!importData.value.data) {
    message.error('请先选择要导入的JSON数据')
    return
  }

  emit('success', importData.value)
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
  importData.value = {}
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