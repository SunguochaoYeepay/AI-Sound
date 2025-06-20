<template>
  <div class="log-monitor">
    <!-- 页面头部 -->
    <div class="page-header">
      <a-page-header 
        title="日志监控" 
        sub-title="系统日志实时监控与分析"
        @back="$router.back()"
      >
        <template #extra>
          <a-space>
            <a-button 
              type="primary" 
              :icon="h(ReloadOutlined)"
              @click="fetchLogs"
              :loading="loading"
            >
              刷新
            </a-button>
            <a-button 
              :icon="h(DownloadOutlined)"
              @click="exportLogs"
            >
              导出
            </a-button>
            <a-button 
              :icon="h(ClearOutlined)"
              @click="showClearModal = true"
            >
              清理
            </a-button>
          </a-space>
        </template>
      </a-page-header>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="[24, 24]" class="stats-row">
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic
            title="总日志数"
            :value="stats.total"
            :loading="statsLoading"
          >
            <template #prefix>
              <FileTextOutlined style="color: #1890ff" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic
            title="错误率"
            :value="stats.error_rate"
            suffix="%"
            :loading="statsLoading"
          >
            <template #prefix>
              <ExclamationCircleOutlined 
                :style="{ color: stats.error_rate > 5 ? '#ff4d4f' : '#52c41a' }" 
              />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic
            title="最近错误"
            :value="stats.recent_errors"
            :loading="statsLoading"
          >
            <template #prefix>
              <BugOutlined style="color: #fa8c16" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic
            title="自动刷新"
            :value="autoRefreshInterval"
            suffix="秒"
          >
            <template #prefix>
              <ClockCircleOutlined 
                :style="{ color: autoRefresh ? '#52c41a' : '#d9d9d9' }" 
              />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 过滤器 -->
    <a-card class="filter-card" title="过滤条件">
      <a-form layout="inline" :model="filters" @finish="applyFilters">
        <a-form-item label="日志级别">
          <a-select
            v-model:value="filters.level"
            placeholder="选择级别"
            style="width: 120px"
            allowClear
          >
            <a-select-option 
              v-for="level in availableLevels" 
              :key="level" 
              :value="level"
            >
              <a-tag :color="getLevelColor(level)">{{ getLevelText(level) }}</a-tag>
            </a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="模块">
          <a-select
            v-model:value="filters.module"
            placeholder="选择模块"
            style="width: 120px"
            allowClear
          >
            <a-select-option 
              v-for="module in availableModules" 
              :key="module" 
              :value="module"
            >
              {{ getModuleText(module) }}
            </a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="时间范围">
          <a-range-picker
            v-model:value="filters.timeRange"
            show-time
            format="YYYY-MM-DD HH:mm:ss"
            style="width: 300px"
          />
        </a-form-item>
        
        <a-form-item label="关键词">
          <a-input
            v-model:value="filters.keyword"
            placeholder="搜索关键词"
            style="width: 200px"
            allowClear
          />
        </a-form-item>
        
        <a-form-item>
          <a-button type="primary" html-type="submit">搜索</a-button>
        </a-form-item>
        
        <a-form-item>
          <a-button @click="resetFilters">重置</a-button>
        </a-form-item>
        
        <a-form-item>
          <a-switch
            v-model:checked="autoRefresh"
            checked-children="自动刷新"
            un-checked-children="手动刷新"
            @change="toggleAutoRefresh"
          />
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 日志表格 -->
    <a-card class="log-table-card" title="日志列表">
      <template #extra>
        <a-space>
          <span class="table-info">
            共 {{ pagination.total }} 条记录
          </span>
          <a-button 
            size="small" 
            type="link"
            @click="scrollToTop"
          >
            回到顶部
          </a-button>
        </a-space>
      </template>
      
      <a-table
        :dataSource="logs"
        :columns="columns"
        :loading="loading"
        :pagination="tablePagination"
        :scroll="{ x: 1200 }"
        size="small"
        @change="handleTableChange"
        row-key="id"
      >
        <!-- 自定义列渲染 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'level'">
            <a-tag :color="getLevelColor(record.level)">
              {{ getLevelText(record.level) }}
            </a-tag>
          </template>
          
          <template v-else-if="column.dataIndex === 'module'">
            <a-tag color="blue">{{ getModuleText(record.module) }}</a-tag>
          </template>
          
          <template v-else-if="column.dataIndex === 'message'">
            <div class="log-message">
              <a-tooltip :title="record.message">
                <span>{{ truncateText(record.message, 100) }}</span>
              </a-tooltip>
              <a-button
                v-if="record.details"
                type="link"
                size="small"
                @click="showLogDetail(record)"
              >
                详情
              </a-button>
            </div>
          </template>
          
          <template v-else-if="column.dataIndex === 'created_at'">
            <a-tooltip :title="formatTime(record.created_at)">
              {{ formatRelativeTime(record.created_at) }}
            </a-tooltip>
          </template>
          
          <template v-else-if="column.dataIndex === 'actions'">
            <a-space>
              <a-button 
                type="link" 
                size="small"
                @click="showLogDetail(record)"
              >
                查看
              </a-button>
              <a-button 
                v-if="record.level === 'error' || record.level === 'critical'"
                type="link" 
                size="small"
                danger
                @click="reportError(record)"
              >
                报告
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 日志详情弹窗 -->
    <a-modal
      v-model:open="detailModalVisible"
      title="日志详情"
      width="800px"
      :footer="null"
    >
      <div v-if="selectedLog" class="log-detail">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="ID">{{ selectedLog.id }}</a-descriptions-item>
          <a-descriptions-item label="级别">
            <a-tag :color="getLevelColor(selectedLog.level)">
              {{ getLevelText(selectedLog.level) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="模块">
            <a-tag color="blue">{{ getModuleText(selectedLog.module) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="时间">
            {{ formatTime(selectedLog.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="用户ID" :span="2">
            {{ selectedLog.user_id || '无' }}
          </a-descriptions-item>
          <a-descriptions-item label="IP地址" :span="2">
            {{ selectedLog.ip_address || '无' }}
          </a-descriptions-item>
        </a-descriptions>
        
        <a-divider>消息内容</a-divider>
        <div class="log-content">
          <pre>{{ selectedLog.message }}</pre>
        </div>
        
        <a-divider v-if="selectedLog.details">详细信息</a-divider>
        <div v-if="selectedLog.details" class="log-details">
          <a-typography-paragraph>
            <pre>{{ formatJsonDetails(selectedLog.details) }}</pre>
          </a-typography-paragraph>
        </div>
      </div>
    </a-modal>

    <!-- 清理日志确认弹窗 -->
    <a-modal
      v-model:open="showClearModal"
      title="清理日志"
      @ok="clearLogs"
      :confirmLoading="clearLoading"
    >
      <p>确定要清理旧日志吗？</p>
      <a-form-item label="保留天数">
        <a-input-number
          v-model:value="clearDays"
          :min="1"
          :max="365"
          style="width: 120px"
        />
        <span class="ml-2">天内的日志将被保留</span>
      </a-form-item>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, h } from 'vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import {
  ReloadOutlined,
  DownloadOutlined,
  ClearOutlined,
  FileTextOutlined,
  ExclamationCircleOutlined,
  BugOutlined,
  ClockCircleOutlined
} from '@ant-design/icons-vue'
import { logApi } from '../api/logs'

// 扩展dayjs
dayjs.extend(relativeTime)

// 响应式数据
const loading = ref(false)
const statsLoading = ref(false)
const clearLoading = ref(false)
const logs = ref([])
const stats = ref({
  total: 0,
  by_level: {},
  by_module: {},
  recent_errors: 0,
  error_rate: 0
})

const pagination = reactive({
  current: 1,
  pageSize: 50,
  total: 0
})

const filters = reactive({
  level: undefined,
  module: undefined,
  timeRange: undefined,
  keyword: undefined
})

const availableLevels = ref(['debug', 'info', 'warning', 'error', 'critical'])
const availableModules = ref(['system', 'tts', 'database', 'api', 'websocket', 'auth', 'file', 'synthesis', 'analysis'])

const autoRefresh = ref(false)
const autoRefreshInterval = ref(10)
const autoRefreshTimer = ref(null)

const detailModalVisible = ref(false)
const selectedLog = ref(null)
const showClearModal = ref(false)
const clearDays = ref(30)

// 表格列定义
const columns = [
  {
    title: '时间',
    dataIndex: 'created_at',
    width: 120,
    sorter: true
  },
  {
    title: '级别',
    dataIndex: 'level',
    width: 80,
    filters: availableLevels.value.map(level => ({
      text: getLevelText(level),
      value: level
    }))
  },
  {
    title: '模块',
    dataIndex: 'module',
    width: 100,
    filters: availableModules.value.map(module => ({
      text: getModuleText(module),
      value: module
    }))
  },
  {
    title: '消息',
    dataIndex: 'message',
    ellipsis: true
  },
  {
    title: '用户',
    dataIndex: 'user_id',
    width: 100
  },
  {
    title: '操作',
    dataIndex: 'actions',
    width: 120,
    fixed: 'right'
  }
]

// 计算属性
const tablePagination = computed(() => ({
  current: pagination.current,
  pageSize: pagination.pageSize,
  total: pagination.total,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
}))

// 方法
function getLevelColor(level) {
  const colors = {
    debug: 'default',
    info: 'blue',
    warning: 'orange',
    error: 'red',
    critical: 'purple'
  }
  return colors[level] || 'default'
}

function getLevelText(level) {
  const texts = {
    debug: '调试',
    info: '信息',
    warning: '警告',
    error: '错误',
    critical: '严重'
  }
  return texts[level] || level
}

function getModuleText(module) {
  const texts = {
    system: '系统',
    tts: 'TTS',
    database: '数据库',
    api: 'API',
    websocket: 'WebSocket',
    auth: '认证',
    file: '文件',
    synthesis: '合成',
    analysis: '分析'
  }
  return texts[module] || module
}

function formatTime(timestamp) {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

function formatRelativeTime(timestamp) {
  return dayjs(timestamp).fromNow()
}

function truncateText(text, maxLength) {
  if (!text) return ''
  return text.length > maxLength ? text.slice(0, maxLength) + '...' : text
}

function formatJsonDetails(details) {
  try {
    const parsed = JSON.parse(details)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return details
  }
}

async function fetchLogs() {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...filters
    }
    
    // 处理时间范围
    if (filters.timeRange && filters.timeRange.length === 2) {
      params.start_time = filters.timeRange[0].toISOString()
      params.end_time = filters.timeRange[1].toISOString()
    }
    
    const response = await logApi.getLogs(params)
    if (response.success) {
      logs.value = response.data.logs
      pagination.total = response.data.pagination.total
    }
  } catch (error) {
    message.error('获取日志失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  statsLoading.value = true
  try {
    const response = await logApi.getStats({ hours: 24 })
    if (response.success) {
      stats.value = response.data
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  } finally {
    statsLoading.value = false
  }
}

async function fetchMetadata() {
  try {
    const [levelsRes, modulesRes] = await Promise.all([
      logApi.getLevels(),
      logApi.getModules()
    ])
    
    if (levelsRes.success) {
      availableLevels.value = levelsRes.data
    }
    if (modulesRes.success) {
      availableModules.value = modulesRes.data
    }
  } catch (error) {
    console.error('获取元数据失败:', error)
  }
}

function applyFilters() {
  pagination.current = 1
  fetchLogs()
}

function resetFilters() {
  Object.keys(filters).forEach(key => {
    filters[key] = undefined
  })
  pagination.current = 1
  fetchLogs()
}

function handleTableChange(pag, filterInfo, sorter) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchLogs()
}

function showLogDetail(log) {
  selectedLog.value = log
  detailModalVisible.value = true
}

function toggleAutoRefresh(enabled) {
  if (enabled) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

function startAutoRefresh() {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
  }
  
  autoRefreshTimer.value = setInterval(() => {
    fetchLogs()
    fetchStats()
  }, autoRefreshInterval.value * 1000)
}

function stopAutoRefresh() {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
    autoRefreshTimer.value = null
  }
}

async function exportLogs() {
  try {
    const params = { ...filters, format: 'csv', limit: 5000 }
    
    if (filters.timeRange && filters.timeRange.length === 2) {
      params.start_time = filters.timeRange[0].toISOString()
      params.end_time = filters.timeRange[1].toISOString()
    }
    
    await logApi.exportLogs(params)
    message.success('日志导出成功')
  } catch (error) {
    message.error('导出失败: ' + error.message)
  }
}

async function clearLogs() {
  clearLoading.value = true
  try {
    const response = await logApi.clearLogs({ days: clearDays.value })
    if (response.success) {
      message.success(response.message)
      showClearModal.value = false
      fetchLogs()
      fetchStats()
    }
  } catch (error) {
    message.error('清理失败: ' + error.message)
  } finally {
    clearLoading.value = false
  }
}

function reportError(log) {
  // TODO: 实现错误报告功能
  message.info('错误报告功能待实现')
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    fetchMetadata(),
    fetchLogs(),
    fetchStats()
  ])
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.log-monitor {
  padding: 24px;
}

.page-header {
  background: #fff;
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.log-table-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-info {
  color: #666;
  font-size: 12px;
}

.log-message {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.log-detail {
  max-height: 600px;
  overflow-y: auto;
}

.log-content,
.log-details {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.ml-2 {
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .log-monitor {
    padding: 12px;
  }
  
  .stats-row .ant-col {
    margin-bottom: 12px;
  }
}
</style>