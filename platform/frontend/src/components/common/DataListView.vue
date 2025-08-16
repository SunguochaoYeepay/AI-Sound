<template>
  <div class="data-list-view">
    <a-spin :spinning="loading" :tip="loadingTip">
      <!-- 空状态 -->
      <div v-if="data.length === 0 && !loading" class="empty-state">
        <div class="empty-content">
          <component :is="emptyIcon" v-if="emptyIcon" class="empty-icon" />
          <h3>{{ emptyTitle }}</h3>
          <p>{{ emptyDescription }}</p>
          <slot name="empty-actions">
            <a-button v-if="emptyAction" type="primary" @click="handleEmptyAction">
              {{ emptyAction.text }}
            </a-button>
          </slot>
        </div>
      </div>

      <!-- 列表视图 -->
      <div class="list-view">
        <slot name="list-table" :data="data">
          <!-- 默认表格 -->
          <a-table
            :columns="tableColumns"
            :data-source="data"
            :pagination="false"
            :row-key="getItemKey"
            size="large"
            @row="(record) => ({ onClick: () => handleItemClick(record) })"
          >
            <template #bodyCell="{ column, record, index }">
              <slot 
                :name="`table-${column.key}`" 
                :column="column" 
                :record="record" 
                :index="index"
              >
                <!-- 默认单元格内容 -->
                <template v-if="column.key === 'title'">
                  <div style="display: flex; align-items: center; gap: 12px">
                    <div class="table-avatar">
                      {{ getItemAvatar(record) }}
                    </div>
                    <div>
                      <div style="font-weight: 500">{{ getItemTitle(record) }}</div>
                      <div style="font-size: 12px; color: #6b7280">{{ getItemDescription(record) }}</div>
                    </div>
                  </div>
                </template>

                <template v-else-if="column.key === 'actions'">
                  <div style="display: flex; gap: 8px">
                    <slot name="table-actions" :record="record">
                      <a-button type="text" size="small" @click.stop="handleEdit(record)">
                        编辑
                      </a-button>
                      <a-button type="text" size="small" @click.stop="handleView(record)">
                        查看
                      </a-button>
                      <a-button type="text" size="small" danger @click.stop="handleDelete(record)">
                        删除
                      </a-button>
                    </slot>
                  </div>
                </template>
              </slot>
            </template>
          </a-table>
        </slot>
      </div>
    </a-spin>

    <!-- 分页 -->
    <div v-if="showPagination && pagination.total > 0" class="pagination-section">
      <a-pagination
        v-model:current="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :show-size-changer="true"
        :show-quick-jumper="true"
        :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
        @change="handlePageChange"
        @showSizeChange="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { EditOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  // 数据相关
  data: {
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
  'item-click', 
  'edit', 
  'view', 
  'delete', 
  'empty-action',
  'page-change'
])

// 方法
const getItemKey = (item) => {
  return item[props.itemKey] || item.id
}

const getItemIndex = (item) => {
  return props.data.findIndex(i => getItemKey(i) === getItemKey(item))
}

const getItemTitle = (item) => {
  return item[props.itemTitle] || item.title || '无标题'
}

const getItemDescription = (item) => {
  return item[props.itemDescription] || item.description || '暂无描述'
}

const getItemAvatar = (item) => {
  const value = item[props.itemAvatar] || item.title || '?'
  return typeof value === 'string' ? value.charAt(0) : '?'
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

const handlePageChange = (page, pageSize) => {
  emit('page-change', { page, pageSize })
}
</script>

<style scoped>
.data-list-view {
  min-height: 200px;
}

.empty-state {
  text-align: center;
  padding: 80px 0;
}

.empty-content {
  max-width: 400px;
  margin: 0 auto;
}

.empty-icon {
  font-size: 80px;
  color: #d1d5db;
  margin-bottom: 16px;
}

.empty-content h3 {
  margin: 16px 0 8px 0;
  color: #374151;
  font-size: 18px;
  font-weight: 500;
}

.empty-content p {
  color: #6b7280;
  margin-bottom: 24px;
}

.default-card {
  height: 100%;
  cursor: pointer;
  transition: all 0.3s ease;
}

.default-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.table-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--primary-color), #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  font-size: 16px;
}

.pagination-section {
  display: flex;
  justify-content: center;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-top: 24px;
}

/* 暗黑模式适配 */
[data-theme='dark'] .empty-content h3 {
  color: #fff !important;
}

[data-theme='dark'] .empty-content p {
  color: #8c8c8c !important;
}

[data-theme='dark'] .default-card {
  background: #1f1f1f !important;
  border-color: #434343 !important;
}

[data-theme='dark'] .default-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5) !important;
}

[data-theme='dark'] .pagination-section {
  background: #1f1f1f !important;
  border: 1px solid #434343 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

[data-theme='dark'] .list-view :deep(.ant-table) {
  background: #1f1f1f !important;
}

[data-theme='dark'] .list-view :deep(.ant-table-thead > tr > th) {
  background: #2d2d2d !important;
  border-bottom-color: #434343 !important;
  color: #fff !important;
}

[data-theme='dark'] .list-view :deep(.ant-table-tbody > tr > td) {
  background: #1f1f1f !important;
  border-bottom-color: #434343 !important;
  color: #d1d5db !important;
}

[data-theme='dark'] .list-view :deep(.ant-table-tbody > tr:hover > td) {
  background: #2d2d2d !important;
}
</style>