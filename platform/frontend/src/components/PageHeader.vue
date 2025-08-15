<template>
  <div class="page-header">
    <div class="header-content">
      <div class="title-section">
        <h1 class="page-title">{{ title }}</h1>
        <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="actions-section">
        <slot name="actions"></slot>
      </div>
    </div>
    <div v-if="$slots.content" class="content-section">
      <slot name="content"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
  interface Props {
    title: string
    subtitle?: string
  }

  const props = withDefaults(defineProps<Props>(), {
    subtitle: ''
  })
</script>

<style scoped>
  .page-header {
    margin-bottom: 24px;
    padding: 20px 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .title-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 500;
    color: white;
    line-height: 28px;
  }

  .page-subtitle {
    margin: 0;
    color: rgba(255, 255, 255, 0.85);
    font-size: 14px;
    line-height: 1.5;
  }

  .actions-section {
    display: flex;
    gap: 16px;
  }

  .content-section {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
</style>
