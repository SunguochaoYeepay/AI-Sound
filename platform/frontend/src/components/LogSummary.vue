<template>
  <div class="log-summary">
    <a-card title="系统日志概览" :hoverable="true">
      <template #extra>
        <a-space>
          <a-button 
            type="link" 
            size="small"
            @click="$router.push('/logs')"
          >
            查看详情
          </a-button>
          <a-button
            type="link"
            size="small"
            :icon="h(ReloadOutlined)"
            @click="refresh"
            :loading="loading"
          />
        </a-space>
      </template>
      
      <!-- 统计指标 -->
      <a-row :gutter="[16, 16]" class="metrics-row">
        <a-col :span="8">
          <div class="metric-item">
            <div class="metric-value">{{ stats.recent_errors }}</div>
            <div class="metric-label">最近错误</div>
            <div 
              class="metric-trend"
              :class="{ 'trend-danger': stats.recent_errors > 10 }"
            >
              <ExclamationCircleOutlined v-if="stats.recent_errors > 0" />
            </div>
          </div>
        </a-col>
        
        <a-col :span="8">
          <div class="metric-item">
            <div class="metric-value">{{ stats.error_rate }}%</div>
            <div class="metric-label">错误率</div>
            <div 
              class="metric-trend"
              :class="{ 'trend-danger': stats.error_rate > 5 }"
            >
              <ArrowUpOutlined v-if="stats.error_rate > 5" />
              <ArrowDownOutlined v-else />
            </div>
          </div>
        </a-col>
        
        <a-col :span="8">
          <div class="metric-item">
            <div class="metric-value">{{ formatNumber(stats.total) }}</div>
            <div class="metric-label">总日志数</div>
            <div class="metric-trend">
              <FileTextOutlined />
            </div>
          </div>
        </a-col>
      </a-row>
      
      <!-- 级别分布 -->
      <a-divider>日志级别分布</a-divider>
      <div class="level-distribution">
        <div 
          v-for="(count, level) in stats.by_level" 
          :key="level"
          class="level-item"
        >
          <a-tag :color="getLevelColor(level)" class="level-tag">
            {{ getLevelText(level) }}
          </a-tag>
          <span class="level-count">{{ count }}</span>
          <div class="level-bar">
            <div 
              class="level-progress"
              :style="{ 
                width: `${(count / stats.total * 100).toFixed(1)}%`,
                backgroundColor: getLevelProgressColor(level)
              }"
            />
          </div>
        </div>
      </div>
      
      <!-- 最近错误日志 -->
      <template v-if="recentErrors.length > 0">
        <a-divider>最近错误</a-divider>
        <div class="recent-errors">
          <div 
            v-for="error in recentErrors.slice(0, 3)" 
            :key="error.id"
            class="error-item"
            @click="showErrorDetail(error)"
          >
            <div class="error-header">
              <a-tag color="red" size="small">{{ getLevelText(error.level) }}</a-tag>
              <span class="error-time">{{ formatRelativeTime(error.created_at) }}</span>
            </div>
            <div class="error-message">
              {{ truncateText(error.message, 60) }}
            </div>
            <div class="error-module">
              <a-tag color="blue" size="small">{{ getModuleText(error.module) }}</a-tag>
            </div>
          </div>
        </div>
      </template>
      
      <!-- 模块活动 -->
      <a-divider>模块活动</a-divider>
      <div class="module-activity">
        <a-row :gutter="[8, 8]">
          <a-col 
            v-for="(count, module) in stats.by_module" 
            :key="module"
            :span="6"
          >
            <div class="module-item">
              <a-tag color="blue" size="small">{{ getModuleText(module) }}</a-tag>
              <span class="module-count">{{ count }}</span>
            </div>
          </a-col>
        </a-row>
      </div>
    </a-card>

    <!-- 错误详情弹窗 -->
    <a-modal
      v-model:open="errorDetailVisible"
      title="错误详情"
      width="600px"
      :footer="null"
    >
      <div v-if="selectedError" class="error-detail">
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="时间">
            {{ formatTime(selectedError.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="级别">
            <a-tag :color="getLevelColor(selectedError.level)">
              {{ getLevelText(selectedError.level) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="模块">
            <a-tag color="blue">{{ getModuleText(selectedError.module) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="消息">
            <div class="error-content">{{ selectedError.message }}</div>
          </a-descriptions-item>
          <a-descriptions-item v-if="selectedError.details" label="详情">
            <div class="error-details">
              <pre>{{ formatJsonDetails(selectedError.details) }}</pre>
            </div>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h } from 'vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import {
  ReloadOutlined,
  ExclamationCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue'
import { logApi } from '../api/logs'

// 扩展dayjs
dayjs.extend(relativeTime)

// 响应式数据
const loading = ref(false)
const stats = reactive({
  total: 0,
  by_level: {},
  by_module: {},
  recent_errors: 0,
  error_rate: 0
})

const recentErrors = ref([])
const errorDetailVisible = ref(false)
const selectedError = ref(null)

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

function getLevelProgressColor(level) {
  const colors = {
    debug: '#d9d9d9',
    info: '#1890ff',
    warning: '#fa8c16',
    error: '#ff4d4f',
    critical: '#722ed1'
  }
  return colors[level] || '#d9d9d9'
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

function formatNumber(num) {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

function formatTime(timestamp) {
  return dayjs(timestamp).format('MM-DD HH:mm')
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

function showErrorDetail(error) {
  selectedError.value = error
  errorDetailVisible.value = true
}

async function fetchStats() {
  try {
    const response = await logApi.getStats({ hours: 24 })
    if (response.success) {
      Object.assign(stats, response.data)
    }
  } catch (error) {
    console.error('获取日志统计失败:', error)
  }
}

async function fetchRecentErrors() {
  try {
    const response = await logApi.getErrorLogs({ hours: 24, page_size: 5 })
    if (response.success) {
      recentErrors.value = response.data.logs || []
    }
  } catch (error) {
    console.error('获取最近错误失败:', error)
  }
}

async function refresh() {
  loading.value = true
  try {
    await Promise.all([
      fetchStats(),
      fetchRecentErrors()
    ])
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  refresh()
})

// 暴露refresh方法供父组件调用
defineExpose({
  refresh
})
</script>

<style scoped>
.log-summary {
  height: 100%;
}

.metrics-row {
  margin-bottom: 16px;
}

.metric-item {
  text-align: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  position: relative;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.metric-trend {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 16px;
  color: #52c41a;
}

.metric-trend.trend-danger {
  color: #ff4d4f;
}

.level-distribution {
  space-y: 8px;
}

.level-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.level-tag {
  min-width: 50px;
  text-align: center;
}

.level-count {
  min-width: 40px;
  font-weight: bold;
  font-size: 12px;
}

.level-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}

.level-progress {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.recent-errors {
  space-y: 12px;
}

.error-item {
  padding: 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.error-item:hover {
  border-color: #ff7875;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.15);
}

.error-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.error-time {
  font-size: 11px;
  color: #999;
}

.error-message {
  font-size: 13px;
  color: #333;
  margin-bottom: 6px;
  line-height: 1.4;
}

.error-module {
  text-align: right;
}

.module-activity {
  background: #fafafa;
  padding: 12px;
  border-radius: 6px;
}

.module-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: white;
  border-radius: 4px;
  margin-bottom: 4px;
}

.module-count {
  font-weight: bold;
  font-size: 12px;
  color: #666;
}

.error-detail .error-content {
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-detail .error-details {
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}

.error-detail .error-details pre {
  margin: 0;
  font-size: 11px;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .metrics-row .ant-col {
    span: 24;
    margin-bottom: 8px;
  }
  
  .module-activity .ant-col {
    span: 12;
  }
}
</style>