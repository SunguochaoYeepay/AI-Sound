<template>
  <div class="search-filter-section">
    <div class="search-controls">
      <div class="search-filters">
        <!-- 搜索框 -->
        <a-input-search
          v-if="showSearch"
          v-model:value="searchValue"
          :placeholder="searchPlaceholder"
          style="width: 300px"
          size="large"
          @search="handleSearch"
          @pressEnter="handleSearch"
        />

        <!-- 动态筛选器 -->
        <template v-for="filter in filters" :key="filter.key">
          <a-select
            v-if="filter.type === 'select'"
            v-model:value="filterValues[filter.key]"
            :placeholder="filter.placeholder"
            :style="{ width: filter.width || '120px' }"
            size="large"
            :allowClear="filter.allowClear !== false"
            @change="handleFilterChange"
          >
            <a-select-option
              v-for="option in filter.options"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </a-select-option>
          </a-select>

          <a-input
            v-else-if="filter.type === 'input'"
            v-model:value="filterValues[filter.key]"
            :placeholder="filter.placeholder"
            :style="{ width: filter.width || '150px' }"
            size="large"
            @pressEnter="handleFilterChange"
          />
        </template>

        <!-- 刷新按钮 -->
        <a-button
          v-if="showRefresh"
          @click="handleRefresh"
          :loading="loading"
          size="large"
        >
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新
        </a-button>



        <!-- 自定义插槽 -->
        <slot name="extra-filters"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ReloadOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  // 搜索相关
  showSearch: {
    type: Boolean,
    default: true
  },
  searchPlaceholder: {
    type: String,
    default: '搜索...'
  },
  searchValue: {
    type: String,
    default: ''
  },
  
  // 筛选器配置
  filters: {
    type: Array,
    default: () => []
  },
  

  
  // 刷新相关
  showRefresh: {
    type: Boolean,
    default: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['search', 'filter-change', 'refresh'])

// 响应式数据
const searchValue = ref(props.searchValue)
const filterValues = reactive({})

// 初始化筛选器值
props.filters.forEach(filter => {
  filterValues[filter.key] = filter.defaultValue || undefined
})

// 监听搜索值变化
watch(searchValue, (newVal) => {
  emit('search', newVal)
})

// 方法
const handleSearch = () => {
  emit('search', searchValue.value)
}

const handleFilterChange = () => {
  emit('filter-change', { ...filterValues })
}

const handleRefresh = () => {
  emit('refresh')
}


</script>

<style scoped>
.search-filter-section {
  margin-bottom: 24px;
  padding: 20px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.search-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-filters {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.search-filters .ant-btn {
  color: white;
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
}

.search-filters .ant-btn:hover {
  color: white;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.2);
}

.search-filters .ant-btn-primary {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.search-filters .ant-btn-primary:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.7);
}

/* 暗黑模式适配 */
[data-theme='dark'] .search-filter-section {
  background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}
</style>
