<template>
  <a-drawer
    :open="open"
    title="🔍 检测到的问题"
    placement="right"
    width="400"
    :closable="true"
    @close="$emit('close')"
  >
    <div class="issues-drawer-content">
      <div v-if="loading" class="loading-container">
        <a-spin size="large" />
        <p>加载中...</p>
      </div>
      <div v-else-if="detectedIssues.length > 0" class="issue-list">
        <div v-for="(issue, index) in detectedIssues" :key="index" class="issue-item">
          <div class="issue-header">
            <a-tag :color="getIssueColor(issue.type)">{{ issue.type }}</a-tag>
            <span class="issue-time">{{ issue.time }}</span>
          </div>
          <div class="issue-description">{{ issue.description }}</div>
        </div>
      </div>
      <div v-else class="empty-content">
        <p>暂无问题</p>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
// Props
const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  detectedIssues: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['close'])

// Methods
const getIssueColor = (type) => {
  const colors = {
    'error': 'red',
    'warning': 'orange',
    'info': 'blue',
    'success': 'green'
  }
  return colors[type] || 'default'
}
</script>

<style scoped>
@import '@/assets/styles/storyboard.css';
</style>
