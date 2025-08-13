<template>
  <div class="batch-action-toolbar">
    <a-card class="toolbar-card">
      <div class="toolbar-content">
        <!-- 左侧：选择操作 -->
        <div class="left-section">
          <a-space size="middle">
            <a-button 
              type="primary" 
              ghost 
              @click="$emit('select-all')"
              :disabled="totalTracks === 0"
            >
              <CheckSquareOutlined />
              全选
            </a-button>
            <a-button 
              @click="$emit('clear-selection')"
              :disabled="selectedTracks.size === 0"
            >
              <ClearOutlined />
              清除选择
            </a-button>
            <span class="selection-info">
              已选择 {{ selectedTracks.size }}/{{ totalTracks }} 个轨道
            </span>
          </a-space>
        </div>

        <!-- 中间：筛选操作 -->
        <div class="center-section">
          <a-space size="middle">
            <a-select
              v-model:value="filterType"
              placeholder="按类型筛选"
              style="width: 120px"
              @change="handleFilterChange"
            >
              <a-select-option value="all">全部</a-select-option>
              <a-select-option value="matched">已匹配</a-select-option>
              <a-select-option value="need-generation">需生成</a-select-option>
            </a-select>
            
            <a-select
              v-model:value="filterConfidence"
              placeholder="按置信度筛选"
              style="width: 140px"
              @change="handleFilterChange"
            >
              <a-select-option value="all">全部</a-select-option>
              <a-select-option value="high">高置信度 (>0.8)</a-select-option>
              <a-select-option value="medium">中置信度 (0.5-0.8)</a-select-option>
              <a-select-option value="low">低置信度 (<0.5)</a-select-option>
            </a-select>
            
            <a-input-search
              v-model:value="searchKeyword"
              placeholder="搜索关键词"
              style="width: 150px"
              @search="handleSearch"
              @change="handleSearch"
            />
          </a-space>
        </div>

        <!-- 右侧：批量操作 -->
        <div class="right-section">
          <a-space size="middle">
            <a-button 
              type="primary"
              @click="$emit('generate')"
              :disabled="selectedTracks.size === 0"
              :loading="generating"
            >
              <PlayCircleOutlined />
              生成选中环境音
              <span v-if="needGenerationCount > 0" class="count-badge">
                {{ needGenerationCount }}
              </span>
            </a-button>
          </a-space>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="stats-info" v-if="analysisResult">
        <a-row :gutter="16">
          <a-col :span="6">
            <div class="stat-item">
              <CheckCircleOutlined class="stat-icon success" />
              <span>已匹配: {{ matchedCount }}</span>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-item">
              <ClockCircleOutlined class="stat-icon warning" />
              <span>需生成: {{ needGenerationCount }}</span>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-item">
              <PercentageOutlined class="stat-icon info" />
              <span>匹配率: {{ matchRate }}%</span>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-item">
              <ClockCircleOutlined class="stat-icon" />
              <span>预估时间: {{ estimatedTime }}</span>
            </div>
          </a-col>
        </a-row>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { 
  CheckSquareOutlined,
  ClearOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  PercentageOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  selectedTracks: {
    type: Set,
    default: () => new Set()
  },
  totalTracks: {
    type: Number,
    default: 0
  },
  analysisResult: {
    type: Object,
    default: null
  },
  generating: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits([
  'generate',
  'select-all',
  'clear-selection',
  'filter-change',
  'search'
])

// 响应式数据
const filterType = ref('all')
const filterConfidence = ref('all')
const searchKeyword = ref('')

// 计算属性
const matchedCount = computed(() => {
  if (!props.analysisResult) return 0
  return props.analysisResult.matching_summary?.matched_tracks || 0
})

const needGenerationCount = computed(() => {
  if (!props.analysisResult) return 0
  return props.analysisResult.matching_summary?.need_generation_tracks || 0
})

const matchRate = computed(() => {
  if (!props.analysisResult) return 0
  return props.analysisResult.matching_summary?.match_rate || 0
})

const estimatedTime = computed(() => {
  const minutes = Math.ceil(needGenerationCount.value * 0.5)
  if (minutes < 60) {
    return `${minutes}分钟`
  } else {
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return `${hours}小时${remainingMinutes}分钟`
  }
})

// 方法
const handleFilterChange = () => {
  emit('filter-change', {
    type: filterType.value,
    confidence: filterConfidence.value
  })
}

const handleSearch = () => {
  emit('search', searchKeyword.value)
}

// 监听筛选变化
watch([filterType, filterConfidence], () => {
  handleFilterChange()
})
</script>

<style scoped>
.batch-action-toolbar {
  margin-bottom: 24px;
}

.toolbar-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px var(--ant-box-shadow);
}

.toolbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--ant-border-color-split);
  margin-bottom: 16px;
}

.left-section,
.center-section,
.right-section {
  display: flex;
  align-items: center;
}

.selection-info {
  color: var(--ant-text-color-secondary);
  font-size: 14px;
  margin-left: 8px;
}

.count-badge {
  background: #ff4d4f;
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 12px;
  margin-left: 4px;
}

.stats-info {
  padding-top: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--ant-text-color-secondary);
}

.stat-icon {
  font-size: 16px;
}

.stat-icon.success {
  color: var(--ant-success-color);
}

.stat-icon.warning {
  color: var(--ant-warning-color);
}

.stat-icon.info {
  color: var(--ant-primary-color);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .toolbar-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .left-section,
  .center-section,
  .right-section {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .toolbar-content {
    padding: 12px 0;
  }
  
  .center-section {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .stats-info .ant-col {
    margin-bottom: 8px;
  }
  
  .stat-item {
    font-size: 12px;
  }
}
</style>
