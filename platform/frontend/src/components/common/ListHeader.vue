<template>
  <div class="list-header">
    <div class="list-title-section">
      <h2 class="list-title">
        <component :is="titleIcon" v-if="titleIcon" class="title-icon" />
        {{ title }}
      </h2>
             <span class="list-count">{{ countText || `共 ${count} ${countUnit}` }}</span>
    </div>
    <div class="list-actions">
      <!-- 操作按钮 -->
      <template v-for="action in actions" :key="action.key">
        <a-button
          :type="action.type || 'default'"
          :size="action.size || 'large'"
          :loading="action.loading"
          :disabled="action.disabled"
          @click="handleAction(action)"
        >
          <component :is="action.icon" v-if="action.icon" />
          {{ action.text }}
        </a-button>
      </template>



      <!-- 自定义插槽 -->
      <slot name="extra-actions"></slot>
    </div>
  </div>
</template>

<script setup>


// Props
const props = defineProps({
  // 标题相关
  title: {
    type: String,
    required: true
  },
  titleIcon: {
    type: [String, Object],
    default: null
  },
  
  // 计数相关
  count: {
    type: Number,
    default: 0
  },
  countText: {
    type: String,
    default: ''
  },
  countUnit: {
    type: String,
    default: '条'
  },
  
  // 操作按钮
  actions: {
    type: Array,
    default: () => []
  },
  

})

// Emits
const emit = defineEmits(['action'])



// 方法
const handleAction = (action) => {
  emit('action', action)
}


</script>

<style scoped>
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
}

.list-title-section {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
}

.list-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
  color: var(--primary-color);
}

.list-count {
  color: #6b7280;
  font-size: 14px;
}

.list-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* 暗黑模式适配 */
[data-theme='dark'] .list-header {
  border-bottom-color: #434343 !important;
}

[data-theme='dark'] .list-title {
  color: #fff !important;
}

[data-theme='dark'] .list-count {
  color: #8c8c8c !important;
}
</style>
