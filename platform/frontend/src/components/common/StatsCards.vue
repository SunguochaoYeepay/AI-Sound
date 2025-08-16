<template>
  <div class="stats-grid">
    <div 
      v-for="stat in statsConfig" 
      :key="stat.key" 
      class="stat-card"
    >
      <div class="stat-icon" :style="getIconStyle(stat)">
        <component :is="stat.icon" />
      </div>
      <div class="stat-content">
        <div class="stat-value" :style="{ color: stat.color }">
          {{ getStatValue(stat) }}
        </div>
        <div class="stat-label">{{ stat.title }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  SoundOutlined,
  AppstoreOutlined,
  ClockCircleOutlined,
  DatabaseOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({})
  },
  statsConfig: {
    type: Array,
    required: true
  }
})

const getStatValue = (stat) => {
  const value = props.stats[stat.key] || 0
  return stat.formatter ? stat.formatter(value) : value
}

const getIconStyle = (stat) => {
  // 根据不同的统计类型设置不同的渐变背景
  const gradients = {
    total: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
    completed: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    processing: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    failed: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    default: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  }
  
  const gradient = gradients[stat.type] || gradients.default
  
  return {
    background: gradient
  }
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: white;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 10px 25px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
  font-size: 24px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .stat-card {
    padding: 20px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    font-size: 20px;
  }

  .stat-value {
    font-size: 24px;
  }
}

/* 暗黑模式适配 */
[data-theme='dark'] .stats-grid {
  background: transparent !important;
}

[data-theme='dark'] .stat-card {
  background: #1f1f1f !important;
  border-color: #434343 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

[data-theme='dark'] .stat-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

[data-theme='dark'] .stat-value {
  color: #fff !important;
}

[data-theme='dark'] .stat-label {
  color: #8c8c8c !important;
}
</style>
