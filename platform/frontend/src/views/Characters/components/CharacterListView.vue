<template>
  <div class="list-view">
    <a-table
      :columns="tableColumns"
      :data-source="characters"
      :pagination="pagination"
      row-key="id"
      size="large"
      @change="handleTableChange"
      @row="(record) => ({ onClick: () => $emit('select', record) })"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <div style="display: flex; align-items: center; gap: 12px">
            <div
              class="table-avatar"
              :style="{ background: record.avatarUrl ? 'transparent' : record.color }"
            >
              <img
                v-if="record.avatarUrl"
                :src="record.avatarUrl"
                :alt="record.name"
                class="avatar-image"
              />
              <span v-else>{{ record.name.charAt(0) }}</span>
            </div>
            <div>
              <div style="font-weight: 500">{{ record.name }}</div>
              <div style="font-size: 12px; color: #6b7280">{{ record.description }}</div>
            </div>
          </div>
        </template>

        <template v-if="column.key === 'quality'">
          <a-rate v-model:value="record.quality" disabled allow-half />
        </template>

        <template v-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>

        <template v-if="column.key === 'actions'">
          <div style="display: flex; gap: 8px">
            <a-button type="text" size="small" @click.stop="$emit('play', record)">
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8,5.14V19.14L19,12.14L8,5.14Z" />
                </svg>
              </template>
            </a-button>
            <a-button type="text" size="small" @click.stop="$emit('edit', record)">
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path
                    d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"
                  />
                </svg>
              </template>
            </a-button>
            <a-button
              type="text"
              size="small"
              danger
              @click.stop="$emit('delete', record)"
            >
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path
                    d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"
                  />
                </svg>
              </template>
            </a-button>
          </div>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getTableColumns } from '../config/tableColumns'

// Props
const props = defineProps({
  characters: {
    type: Array,
    required: true
  },
  pagination: {
    type: Object,
    required: true
  }
})

// Emits
const emit = defineEmits([
  'select',
  'play', 
  'edit',
  'delete',
  'table-change'
])

// 工具函数定义
const getStatusColor = (status) => {
  const colors = {
    active: 'success',
    training: 'processing',
    inactive: 'default',
    configured: 'success',
    unconfigured: 'warning'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    active: '可用',
    training: '训练中',
    inactive: '未激活',
    configured: '已配置',
    unconfigured: '待配置'
  }
  return texts[status] || '未知'
}

const getVoiceTypeLabel = (type) => {
  const typeMap = {
    'male': '男声',
    'female': '女声', 
    'child': '童声',
    'elder': '老人声',
    'custom': '自定义'
  }
  return typeMap[type] || '未知'
}

// 表格列定义
const tableColumns = computed(() => 
  getTableColumns(getStatusColor, getStatusText, getVoiceTypeLabel)
)

// 表格分页变化处理
const handleTableChange = (paginationInfo) => {
  emit('table-change', paginationInfo)
}
</script>

<style scoped>
.list-view {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.table-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  font-size: 16px;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
</style>
