<template>
  <div v-if="visible" class="error-message-display">
    <a-alert
      :message="title"
      :description="description"
      :type="type"
      show-icon
      closable
      @close="handleClose"
      class="error-alert"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  error: {
    type: Object,
    default: null
  },
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const title = ref('')
const description = ref('')
const type = ref('error')

// 监听错误信息变化
watch(() => props.error, (newError) => {
  if (newError) {
    // 构建错误标题
    let errorTitle = newError.error || newError.message || '操作失败'
    
    // 如果有章节ID，添加到标题中
    if (newError.chapter_id && newError.chapter_id !== '未知') {
      errorTitle = `章节[${newError.chapter_id}]: ${errorTitle}`
    }
    
    title.value = errorTitle
    
    // 构建描述信息
    const suggestion = newError.suggestion || '请检查数据完整性'
    if (suggestion && suggestion !== '请检查数据完整性') {
      description.value = suggestion
    } else {
      description.value = ''
    }
    
    // 设置消息类型
    type.value = 'error'
  }
}, { immediate: true })

const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
.error-message-display {
  margin-bottom: 16px;
}

.error-alert {
  border-radius: 8px;
}

/* 暗黑模式适配 */
[data-theme='dark'] .error-alert {
  background-color: rgba(255, 77, 79, 0.1);
  border-color: rgba(255, 77, 79, 0.3);
}
</style>
