<template>
  <div class="page-container-with-stats">
    <!-- 搜索筛选区域 -->
    <SearchFilterSection
      :search-value="searchValue"
      :search-placeholder="searchPlaceholder"
      :filters="filters"
      @search="$emit('search', $event)"
      @filter-change="$emit('filter-change', $event)"
      @refresh="$emit('refresh')"
    />

    <!-- 统计卡片区域 -->
    <StatsCards
      v-if="showStats && stats"
      :stats="stats"
      :stats-config="statsConfig"
    />

    <!-- 列表头部 -->
    <ListHeader
      :title="title"
      :title-icon="titleIcon"
      :count="data.length"
      :count-text="countText"
      :count-unit="countUnit"
      :actions="actions"
      @action="$emit('action', $event)"
    />

    <!-- 数据列表 -->
    <DataListView
      :data="data"
      :loading="loading"
      :loading-tip="loadingTip"
      :table-columns="tableColumns"
      :show-pagination="showPagination"
      :pagination="pagination"
      :empty-title="emptyTitle"
      :empty-description="emptyDescription"
      :empty-action="emptyAction"
      @item-click="$emit('item-click', $event)"
      @edit="$emit('edit', $event)"
      @view="$emit('view', $event)"
      @delete="$emit('delete', $event)"
      @empty-action="$emit('empty-action')"
      @page-change="$emit('page-change', $event)"
    >
      <template
        v-for="(_, name) in $slots"
        :key="name"
        #[name]="slotData"
      >
        <slot :name="name" v-bind="slotData" />
      </template>
    </DataListView>
  </div>
</template>

<script setup>
import SearchFilterSection from './SearchFilterSection.vue'
import StatsCards from './StatsCards.vue'
import ListHeader from './ListHeader.vue'
import DataListView from './DataListView.vue'

defineProps({
  // 搜索筛选相关
  searchValue: String,
  searchPlaceholder: String,
  filters: Array,
  
  // 统计相关
  showStats: {
    type: Boolean,
    default: true
  },
  stats: Object,
  statsConfig: Array,
  
  // 列表头部相关
  title: String,
  titleIcon: String,
  countText: String,
  countUnit: String,
  actions: Array,
  
  // 数据列表相关
  data: Array,
  loading: Boolean,
  loadingTip: String,
  tableColumns: Array,
  showPagination: Boolean,
  pagination: Object,
  emptyTitle: String,
  emptyDescription: String,
  emptyAction: Object
})

defineEmits([
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
</script>

<style scoped>
.page-container-with-stats {
  display: flex;
  flex-direction: column;
}
</style>
