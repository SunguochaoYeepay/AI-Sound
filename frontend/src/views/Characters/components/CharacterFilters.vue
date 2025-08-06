<template>
  <div class="filter-section">
    <div class="filter-controls">
      <a-input-search
        v-model:value="searchQuery"
        placeholder="搜索角色..."
        style="width: 300px"
        size="large"
        @search="$emit('search')"
        @input="$emit('search')"
      />

      <a-select
        v-model:value="selectedBookId"
        placeholder="选择书籍"
        style="width: 200px"
        size="large"
        @change="$emit('book-change')"
        :loading="booksLoading"
        show-search
        allow-clear
      >
        <a-select-option value="">全部书籍</a-select-option>
        <a-select-option v-for="book in availableBooks" :key="book.id" :value="book.id">
          {{ book.title }} ({{ book.character_count || 0 }}个角色)
        </a-select-option>
      </a-select>

      <a-select
        v-model:value="typeFilter"
        placeholder="声音类型"
        style="width: 120px"
        size="large"
        @change="$emit('filter-change')"
      >
        <a-select-option value="">全部类型</a-select-option>
        <a-select-option value="male">男声</a-select-option>
        <a-select-option value="female">女声</a-select-option>
        <a-select-option value="child">童声</a-select-option>
        <a-select-option value="elder">老人声</a-select-option>
        <a-select-option value="custom">自定义</a-select-option>
      </a-select>

      <a-select
        v-model:value="statusFilter"
        placeholder="配置状态"
        style="width: 120px"
        size="large"
        @change="$emit('filter-change')"
      >
        <a-select-option value="">全部状态</a-select-option>
        <a-select-option value="configured">已配置</a-select-option>
        <a-select-option value="unconfigured">未配置</a-select-option>
        <a-select-option value="training">训练中</a-select-option>
      </a-select>

      <a-select
        v-model:value="avatarFilter"
        placeholder="头像设置"
        style="width: 120px; opacity: 1 !important;"
        size="large"
        @change="$emit('filter-change')"
        :disabled="false"
      >
        <a-select-option value="">全部头像</a-select-option>
        <a-select-option value="has_avatar">已设置</a-select-option>
        <a-select-option value="no_avatar">未设置</a-select-option>
      </a-select>

      <a-select
        v-model:value="audioFilter"
        placeholder="音频文件"
        style="width: 120px; opacity: 1 !important;"
        size="large"
        @change="$emit('filter-change')"
        :disabled="false"
      >
        <a-select-option value="">全部音频</a-select-option>
        <a-select-option value="has_audio">已设置</a-select-option>
        <a-select-option value="no_audio">未设置</a-select-option>
      </a-select>
    </div>

    <div class="view-controls">
      <div class="batch-controls">
        <a-button size="small" @click="$emit('select-all')" :disabled="totalCount === 0">
          全选
        </a-button>
        <a-button size="small" @click="$emit('clear-selection')" :disabled="selectedCount === 0">
          清空
        </a-button>
      </div>
      <a-radio-group v-model:value="viewMode" size="large" @change="$emit('view-change')">
        <a-radio-button value="grid">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3,11H11V3H3M3,21H11V13H3M13,21H21V13H13M13,3V11H21V3" />
          </svg>
        </a-radio-button>
        <a-radio-button value="list">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3,5H21V7H3V5M3,13V11H21V13H3M3,19V17H21V19H3Z" />
          </svg>
        </a-radio-button>
      </a-radio-group>
    </div>
  </div>
</template>

<script setup>
// Props
const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  },
  selectedBookId: {
    type: [String, Number],
    default: ''
  },
  typeFilter: {
    type: String,
    default: ''
  },
  statusFilter: {
    type: String,
    default: ''
  },
  avatarFilter: {
    type: String,
    default: ''
  },
  audioFilter: {
    type: String,
    default: ''
  },
  viewMode: {
    type: String,
    default: 'grid'
  },
  availableBooks: {
    type: Array,
    default: () => []
  },
  booksLoading: {
    type: Boolean,
    default: false
  },
  totalCount: {
    type: Number,
    default: 0
  },
  selectedCount: {
    type: Number,
    default: 0
  }
})

// Emits
const emit = defineEmits([
  'search',
  'book-change',
  'filter-change',
  'view-change',
  'select-all',
  'clear-selection'
])
</script>

<style scoped>
.filter-section {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.filter-controls {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.view-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.batch-controls {
  display: flex;
  gap: 8px;
}

/* 暗黑模式适配 */
[data-theme='dark'] .filter-section {
  background: #1f1f1f;
  border-color: #434343;
}

[data-theme='dark'] .view-controls {
  border-top-color: #374151;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-controls > * {
    width: 100% !important;
  }
  
  .view-controls {
    flex-direction: column;
    gap: 12px;
  }
}
</style> 