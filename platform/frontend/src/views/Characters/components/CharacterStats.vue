<template>
  <div class="stats-grid">
    <div class="stat-card">
      <div
        class="stat-icon"
        style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
          <path
            d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
          />
        </svg>
      </div>
      <div class="stat-content">
        <div class="stat-value">{{ totalCount }}</div>
        <div class="stat-label">角色总数</div>
      </div>
    </div>

    <div class="stat-card">
      <div
        class="stat-icon"
        style="background: linear-gradient(135deg, #10b981 0%, #059669 100%)"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
        </svg>
      </div>
      <div class="stat-content">
        <div class="stat-value">{{ configuredCount }}</div>
        <div class="stat-label">已配置声音</div>
      </div>
    </div>

    <div class="stat-card">
      <div
        class="stat-icon"
        style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
          <path
            d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
          />
          <path
            d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"
          />
        </svg>
      </div>
      <div class="stat-content">
        <div class="stat-value">{{ todayUsage }}</div>
        <div class="stat-label">今日使用次数</div>
      </div>
    </div>

    <div class="stat-card">
      <div
        class="stat-icon"
        style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
          <path
            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
          />
        </svg>
      </div>
      <div class="stat-content">
        <div class="stat-value">{{ ((averageQuality || 0) * 2).toFixed(1) }}</div>
        <div class="stat-label">平均质量评分</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  totalCount: {
    type: Number,
    default: 0
  },
  configuredCount: {
    type: Number,
    default: 0
  },
  todayUsage: {
    type: Number,
    default: 0
  },
  averageQuality: {
    type: Number,
    default: 0
  }
})
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