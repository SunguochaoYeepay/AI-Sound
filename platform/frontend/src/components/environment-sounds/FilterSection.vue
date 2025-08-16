<template>
  <div class="filter-section">
    <a-card class="filter-card" :bordered="false">
      <a-form layout="inline" :model="filters">
        <!-- 搜索框 -->
        <a-form-item label="搜索">
          <a-input
            v-model:value="filters.search"
            placeholder="搜索项目名称或描述"
            allow-clear
            style="width: 200px"
            @press-enter="handleSearch"
          />
        </a-form-item>

        <!-- 状态筛选 -->
        <a-form-item label="状态">
          <a-select
            v-model:value="filters.status"
            placeholder="选择状态"
            allow-clear
            style="width: 120px"
            @change="handleSearch"
          >
            <a-select-option value="pending">待处理</a-select-option>
            <a-select-option value="processing">处理中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
          </a-select>
        </a-form-item>

        <!-- 日期范围 -->
        <a-form-item label="创建时间">
          <a-range-picker
            v-model:value="filters.dateRange"
            style="width: 240px"
            @change="handleSearch"
          />
        </a-form-item>

        <!-- 操作按钮 -->
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <SearchOutlined />
              搜索
            </a-button>
            <a-button @click="handleReset">
              <ReloadOutlined />
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons-vue'

// Props
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

// Emits
const emit = defineEmits(['search', 'reset'])

// 方法
const handleSearch = () => {
  emit('search')
}

const handleReset = () => {
  // 重置所有筛选条件
  Object.keys(props.filters).forEach(key => {
    if (Array.isArray(props.filters[key])) {
      props.filters[key] = []
    } else {
      props.filters[key] = null
    }
  })
  emit('reset')
}
</script>

<style scoped>
.filter-section {
  margin-bottom: 24px;
}

.filter-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-card :deep(.ant-card-body) {
  padding: 16px;
}

.filter-card :deep(.ant-form-item) {
  margin-bottom: 16px;
  margin-right: 16px;
}

.filter-card :deep(.ant-form-item-label) {
  font-weight: 500;
  color: #333;
}

/* 暗黑模式适配 */
[data-theme='dark'] .filter-card {
  background: #1f1f1f;
  border-color: #434343;
}

[data-theme='dark'] .filter-card :deep(.ant-form-item-label) {
  color: #d1d5db;
}
</style>
