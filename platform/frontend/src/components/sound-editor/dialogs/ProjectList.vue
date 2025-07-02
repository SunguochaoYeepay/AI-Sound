<template>
  <a-modal
    :open="open"
    title="选择项目"
    width="800px"
    :footer="null"
    @update:open="$emit('update:open', $event)"
  >
    <ProjectListComponent @select="handleSelect" @delete="handleDelete" />
  </a-modal>
</template>

<script setup>
import ProjectListComponent from '../project/ProjectList.vue'

// Props
const props = defineProps({
  open: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:open', 'select', 'delete'])

// 处理项目选择
function handleSelect(projectId) {
  emit('select', projectId)
  emit('update:open', false)
}

// 处理项目删除
function handleDelete(projectId) {
  emit('delete', projectId)
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