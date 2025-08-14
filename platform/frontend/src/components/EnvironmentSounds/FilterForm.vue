<template>
  <div class="filter-section">
    <a-form layout="inline" :model="filters" @finish="handleSearch">
      <a-form-item label="项目名称">
        <a-input
          v-model:value="filters.name"
          placeholder="输入项目名称"
          allow-clear
        />
      </a-form-item>
      
      <a-form-item label="状态">
        <a-select
          v-model:value="filters.status"
          placeholder="选择状态"
          style="width: 120px"
          allow-clear
        >
          <a-select-option value="">全部</a-select-option>
          <a-select-option value="pending">待处理</a-select-option>
          <a-select-option value="processing">处理中</a-select-option>
          <a-select-option value="completed">已完成</a-select-option>
          <a-select-option value="failed">失败</a-select-option>
        </a-select>
      </a-form-item>
      
      <a-form-item label="书籍">
        <a-select
          v-model:value="filters.bookId"
          placeholder="选择书籍"
          style="width: 150px"
          allow-clear
        >
          <a-select-option value="">全部</a-select-option>
          <a-select-option
            v-for="book in books"
            :key="book.id"
            :value="book.id"
          >
            {{ book.title }}
          </a-select-option>
        </a-select>
      </a-form-item>
      
      <a-form-item>
        <a-button type="primary" html-type="submit">
          <template #icon><SearchOutlined /></template>
          搜索
        </a-button>
      </a-form-item>
      
      <a-form-item>
        <a-button @click="handleReset">
          <template #icon><ClearOutlined /></template>
          重置
        </a-button>
      </a-form-item>
    </a-form>
  </div>
</template>

<script setup>
import { defineEmits, defineProps } from 'vue'
import { SearchOutlined, ClearOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  filters: {
    type: Object,
    required: true
  },
  books: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['search', 'reset'])

const handleSearch = () => {
  emit('search', props.filters)
}

const handleReset = () => {
  emit('reset')
}
</script>

<style scoped>
.filter-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-section :deep(.ant-form-inline) {
    display: block;
  }
  
  .filter-section :deep(.ant-form-item) {
    margin-bottom: 16px;
  }
}

/* 暗黑模式适配 */
[data-theme='dark'] .filter-section {
  background: #2d2d2d !important;
  border: 1px solid #434343 !important;
}
</style>