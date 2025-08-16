<template>
  <a-modal
    :open="visible"
    title="确认删除"
    @ok="handleConfirm"
    @cancel="handleCancel"
  >
    <p>确定要删除 "{{ book?.title || '该项目' }}" 吗？</p>
    <p v-if="book?.synthesisProjects?.length > 0" style="color: red">
      ⚠️ 该项目有 {{ book.synthesisProjects.length }} 个关联的子项目，删除后这些项目也会被删除。
    </p>
    <a-checkbox v-model:checked="forceValue" @change="handleForceChange">
      强制删除（包括关联的子项目）
    </a-checkbox>
  </a-modal>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  book: {
    type: Object,
    default: null
  },
  force: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:visible', 'confirm', 'cancel', 'update:force'])

// 计算属性
const forceValue = computed({
  get: () => props.force,
  set: (value) => emit('update:force', value)
})

// 方法
const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('update:visible', false)
  emit('cancel')
}

const handleForceChange = (checked) => {
  emit('update:force', checked)
}
</script>
