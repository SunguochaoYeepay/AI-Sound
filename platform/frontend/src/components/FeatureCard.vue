<template>
  <div class="feature-card" @click="$emit('click')" :style="{ '--color': color }">
    <div class="feature-icon">
      <div v-html="iconSvg"></div>
    </div>
    <div class="feature-content">
      <h3>{{ title }}</h3>
      <p>{{ description }}</p>
    </div>
    <div class="feature-arrow">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M9.29 15.88L13.17 12 9.29 8.12c-.39-.39-.39-1.02 0-1.41.39-.39 1.02-.39 1.41 0l4.59 4.59c.39.39.39 1.02 0 1.41L10.7 17.3c-.39.39-1.02.39-1.41 0-.38-.39-.39-1.03 0-1.42z"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    required: true
  },
  color: {
    type: String,
    default: '#06b6d4'
  }
})

defineEmits(['click'])

const iconSvg = computed(() => {
  const icons = {
    microphone: `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
      <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
    </svg>`,
    star: `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
    </svg>`,
    book: `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
    </svg>`,
    project: `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
    </svg>`
  }
  
  return icons[props.icon] || icons.microphone
})
</script>

<style scoped>
.feature-card {
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--color);
  transform: scaleX(0);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border-color: var(--color);
}

.feature-card:hover::before {
  transform: scaleX(1);
}

.feature-card:hover .feature-icon {
  background: var(--color);
  transform: scale(1.1);
}

.feature-card:hover .feature-arrow {
  transform: translateX(4px);
  color: var(--color);
}

.feature-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: rgba(var(--color-rgb, 6, 182, 212), 0.1);
  color: var(--color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.feature-content p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.feature-arrow {
  position: absolute;
  top: 24px;
  right: 24px;
  color: #434343;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 暗黑模式适配 */
[data-theme="dark"] .feature-card {
  background: #1f1f1f !important;
  border-color: #434343 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .feature-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

[data-theme="dark"] .feature-content h3 {
  color: #fff !important;
}

[data-theme="dark"] .feature-content p {
  color: #8c8c8c !important;
}

[data-theme="dark"] .feature-arrow {
  color: #666 !important;
}

[data-theme="dark"] .feature-card:hover .feature-arrow {
  color: var(--color) !important;
}
</style> 