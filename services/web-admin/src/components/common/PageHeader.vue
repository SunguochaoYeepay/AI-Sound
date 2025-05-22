<template>
  <div class="page-header">
    <div class="title-section">
      <h1 class="title">{{ title }}</h1>
      <div v-if="subtitle" class="subtitle">{{ subtitle }}</div>
    </div>
    <div v-if="$slots.action" class="action-section">
      <slot name="action"></slot>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'PageHeader',
  props: {
    title: {
      type: String,
      required: true
    },
    subtitle: {
      type: String,
      default: ''
    }
  }
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.title {
  font-size: 20px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  margin: 0;
}

.subtitle {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 8px;
}
</style> 