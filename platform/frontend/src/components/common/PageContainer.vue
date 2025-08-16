<template>
  <div class="page-container">
    <!-- 搜索筛选区域 -->
    <SearchFilterSection
      v-if="showSearch"
      :search-placeholder="searchPlaceholder"
      :search-value="searchValue"
      :filters="filters"
      :show-refresh="showRefresh"
      :loading="loading"
      @search="handleSearch"
      @filter-change="handleFilterChange"
      @refresh="handleRefresh"
    >
      <template #extra-filters>
        <slot name="extra-filters"></slot>
      </template>
    </SearchFilterSection>

    <!-- 列表标题区域 -->
    <ListHeader
      :title="title"
      :title-icon="titleIcon"
      :count="data.length"
      :count-text="countText"
      :count-unit="countUnit"
      :actions="actions"
      @action="handleAction"
    >
      <template #extra-actions>
        <slot name="extra-actions"></slot>
      </template>
    </ListHeader>

    <!-- 数据列表视图 -->
    <DataListView
      :data="data"
      :loading="loading"
      :loading-tip="loadingTip"
      :empty-icon="emptyIcon"
      :empty-title="emptyTitle"
      :empty-description="emptyDescription"
      :empty-action="emptyAction"
      :table-columns="tableColumns"
      :show-pagination="showPagination"
      :pagination="pagination"
      :item-key="itemKey"
      :item-title="itemTitle"
      :item-description="itemDescription"
      :item-avatar="itemAvatar"
      @item-click="handleItemClick"
      @edit="handleEdit"
      @view="handleView"
      @delete="handleDelete"
      @empty-action="handleEmptyAction"
      @page-change="handlePageChange"
    >
      <!-- 网格视图插槽 -->
      <template #grid-item="{ item, index }">
        <slot name="grid-item" :item="item" :index="index"></slot>
      </template>
      
      <template #grid-actions="{ item }">
        <slot name="grid-actions" :item="item"></slot>
      </template>
      
      <template #grid-title="{ item }">
        <slot name="grid-title" :item="item"></slot>
      </template>
      
      <template #grid-description="{ item }">
        <slot name="grid-description" :item="item"></slot>
      </template>

      <!-- 列表视图插槽 -->
      <template #list-table="{ data }">
        <slot name="list-table" :data="data"></slot>
      </template>
      
      <template #table-actions="{ record }">
        <slot name="table-actions" :record="record"></slot>
      </template>

      <!-- 空状态插槽 -->
      <template #empty-actions>
        <slot name="empty-actions"></slot>
      </template>
    </DataListView>

    <!-- 自定义内容插槽 -->
    <slot name="content"></slot>
  </div>
</template>

<script setup>

import SearchFilterSection from './SearchFilterSection.vue'
import ListHeader from './ListHeader.vue'
import DataListView from './DataListView.vue'

// Props
const props = defineProps({
  // 页面标题
  title: {
    type: String,
    required: true
  },
  titleIcon: {
    type: [String, Object],
    default: null
  },
  
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
  filters: {
    type: Array,
    default: () => []
  },
  showRefresh: {
    type: Boolean,
    default: true
  },
  
  // 数据相关
  data: {
    type: Array,
    default: () => []
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
  

  
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  },
  loadingTip: {
    type: String,
    default: '加载中...'
  },
  
  // 空状态
  emptyIcon: {
    type: [String, Object],
    default: null
  },
  emptyTitle: {
    type: String,
    default: '暂无数据'
  },
  emptyDescription: {
    type: String,
    default: '当前没有数据'
  },
  emptyAction: {
    type: Object,
    default: null
  },
  
  // 表格配置
  tableColumns: {
    type: Array,
    default: () => []
  },
  
  // 分页配置
  showPagination: {
    type: Boolean,
    default: false
  },
  pagination: {
    type: Object,
    default: () => ({
      page: 1,
      pageSize: 20,
      total: 0
    })
  },
  
  // 数据字段映射
  itemKey: {
    type: String,
    default: 'id'
  },
  itemTitle: {
    type: String,
    default: 'title'
  },
  itemDescription: {
    type: String,
    default: 'description'
  },
  itemAvatar: {
    type: String,
    default: 'title'
  }
})

// Emits
const emit = defineEmits([
  'search',
  'filter-change', 
  'refresh',
  'action',

  'item-click',
  'edit',
  'view',
  'delete',
  'empty-action',
  'page-change'
])



// 事件处理方法
const handleSearch = (value) => {
  emit('search', value)
}

const handleFilterChange = (filters) => {
  emit('filter-change', filters)
}

const handleRefresh = () => {
  emit('refresh')
}

const handleAction = (action) => {
  emit('action', action)
}



const handleItemClick = (item) => {
  emit('item-click', item)
}

const handleEdit = (item) => {
  emit('edit', item)
}

const handleView = (item) => {
  emit('view', item)
}

const handleDelete = (item) => {
  emit('delete', item)
}

const handleEmptyAction = () => {
  emit('empty-action')
}

const handlePageChange = (pagination) => {
  emit('page-change', pagination)
}
</script>

<style scoped>
.page-container {
  background: #f5f5f5;
  min-height: 100vh;
}

/* 暗黑模式适配 */
[data-theme='dark'] .page-container {
  background: #141414 !important;
}
</style>