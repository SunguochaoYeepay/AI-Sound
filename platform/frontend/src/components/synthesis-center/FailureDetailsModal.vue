<template>
  <a-modal
    v-model:open="visible"
    title="合成失败详情"
    width="800px"
    :footer="null"
    @cancel="handleClose"
  >
    <div class="failure-details">
      <div class="overview-section">
        <a-alert
          message="暂无失败详情数据"
          type="info"
          show-icon
        />
      </div>
      <div class="action-buttons">
        <a-button @click="handleClose">关闭</a-button>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  projectId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['update:visible'])

const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.failure-details {
  max-height: 400px;
  overflow-y: auto;
}
.overview-section {
  margin-bottom: 16px;
}
.action-buttons {
  text-align: center;
  padding-top: 16px;
}
</style>
