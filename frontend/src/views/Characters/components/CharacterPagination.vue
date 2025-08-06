<template>
  <div v-if="total > 0" class="pagination-wrapper">
    <a-pagination
      v-model:current="current"
      v-model:page-size="pageSize"
      :total="total"
      :show-size-changer="showSizeChanger"
      :show-quick-jumper="showQuickJumper"
      :show-total="showTotal"
      @change="handleChange"
      @show-size-change="handleShowSizeChange"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  current: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 20
  },
  total: {
    type: Number,
    default: 0
  },
  showSizeChanger: {
    type: Boolean,
    default: true
  },
  showQuickJumper: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['change', 'show-size-change'])

// Computed
const showTotal = computed(() => {
  return (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

// Methods
const handleChange = (page, pageSize) => {
  emit('change', page, pageSize)
}

const handleShowSizeChange = (current, size) => {
  emit('show-size-change', current, size)
}
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 32px;
  padding: 24px 0;
  border-top: 1px solid #f0f0f0;
  background: #fff;
  width: 100%;
  min-width: 100%;
  box-sizing: border-box;
}

.pagination-wrapper .ant-pagination {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 确保分页组件占满容器宽度 */
.pagination-wrapper .ant-pagination-total {
  flex: 1;
  text-align: left;
}

.pagination-wrapper .ant-pagination-options {
  flex: 1;
  text-align: right;
}

.pagination-wrapper .ant-pagination-prev,
.pagination-wrapper .ant-pagination-next,
.pagination-wrapper .ant-pagination-item {
  margin: 0 4px;
}

/* 暗黑模式下的分页组件样式 */
[data-theme='dark'] .pagination-wrapper {
  border-top-color: #434343;
  background: #1f1f1f;
  width: 100%;
  min-width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .pagination-wrapper {
    padding: 16px 0;
  }
  
  .pagination-wrapper .ant-pagination {
    flex-direction: column;
    gap: 12px;
  }
  
  .pagination-wrapper .ant-pagination-total,
  .pagination-wrapper .ant-pagination-options {
    text-align: center;
  }
}
</style> 