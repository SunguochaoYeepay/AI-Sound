<template>
  <div v-if="visible" class="dev-console">
    <div class="console-header">
      <span class="console-title">🔧 开发者控制台</span>
      <a-button size="small" @click="visible = false">✕</a-button>
    </div>
    
    <div class="console-content">
      <a-tabs v-model:activeKey="activeTab" size="small">
        <!-- 轮询监控 -->
        <a-tab-pane key="polling" tab="轮询监控">
          <div class="tab-content">
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-label">活跃轮询</div>
                <div class="stat-value">{{ pollingStats.active }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">可疑轮询</div>
                <div class="stat-value danger">{{ pollingStats.suspicious }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">网络请求</div>
                <div class="stat-value">{{ pollingStats.requests }}</div>
              </div>
            </div>
            
            <div class="action-buttons">
              <a-button type="primary" @click="refreshStats">🔄 刷新</a-button>
              <a-button @click="viewReport">📊 查看报告</a-button>
              <a-button danger @click="clearSuspicious">🧹 清理异常</a-button>
              <a-button danger @click="emergencyStop">🚨 紧急停止</a-button>
            </div>
            
            <div v-if="report" class="report-section">
              <h4>诊断报告</h4>
              <pre class="report-content">{{ JSON.stringify(report, null, 2) }}</pre>
            </div>
          </div>
        </a-tab-pane>
        
        <!-- 系统信息 -->
        <a-tab-pane key="system" tab="系统信息">
          <div class="tab-content">
            <div class="info-list">
              <div class="info-item">
                <span class="info-label">当前路由:</span>
                <span class="info-value">{{ currentRoute }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">页面状态:</span>
                <span class="info-value">{{ document.hidden ? '隐藏' : '可见' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">内存使用:</span>
                <span class="info-value">{{ memoryUsage }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">连接状态:</span>
                <span class="info-value">{{ navigator.onLine ? '在线' : '离线' }}</span>
              </div>
            </div>
          </div>
        </a-tab-pane>
        
        <!-- 快捷操作 -->
        <a-tab-pane key="actions" tab="快捷操作">
          <div class="tab-content">
            <div class="quick-actions">
              <a-button block @click="refreshPage">🔄 刷新页面</a-button>
              <a-button block @click="clearCache">🗑️ 清除缓存</a-button>
              <a-button block @click="exportLogs">📥 导出日志</a-button>
              <a-button block @click="showShortcuts">⌨️ 快捷键</a-button>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>
  
  <!-- 浮动开启按钮 -->
  <div v-if="!visible" class="console-trigger" @click="visible = true">
    🔧
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'

const route = useRoute()
const visible = ref(false)
const activeTab = ref('polling')
const report = ref(null)

const pollingStats = reactive({
  active: 0,
  suspicious: 0,
  requests: 0
})

const currentRoute = computed(() => route.path)

const memoryUsage = computed(() => {
  if (window.performance && window.performance.memory) {
    const memory = window.performance.memory
    const used = Math.round(memory.usedJSHeapSize / 1024 / 1024)
    const total = Math.round(memory.totalJSHeapSize / 1024 / 1024)
    return `${used}MB / ${total}MB`
  }
  return '不支持'
})

// 定时更新统计信息
let statsTimer = null

const refreshStats = () => {
  if (window.debugTools) {
    const timers = window.debugTools.getActiveTimers()
    const suspicious = window.debugTools.findSuspiciousPolling()
    const requests = window.debugTools.checkNetworkRequests()
    
    pollingStats.active = timers.length
    pollingStats.suspicious = suspicious.length
    pollingStats.requests = requests.length
  }
}

const viewReport = () => {
  if (window.debugTools) {
    report.value = window.debugTools.generateDiagnosticReport()
  }
}

const clearSuspicious = () => {
  if (window.debugTools) {
    const count = window.debugTools.clearSuspiciousPolling()
    refreshStats()
    message.success(`清除了 ${count} 个异常轮询`)
  }
}

const emergencyStop = () => {
  if (window.debugTools) {
    const count = window.debugTools.clearAllTimers()
    refreshStats()
    message.warning(`紧急停止了所有 ${count} 个定时器`)
  }
}

const refreshPage = () => {
  window.location.reload()
}

const clearCache = () => {
  if ('caches' in window) {
    caches.keys().then(names => {
      names.forEach(name => {
        caches.delete(name)
      })
      message.success('缓存已清除')
    })
  } else {
    localStorage.clear()
    sessionStorage.clear()
    message.success('本地存储已清除')
  }
}

const exportLogs = () => {
  const logs = {
    timestamp: new Date().toISOString(),
    route: route.path,
    stats: pollingStats,
    report: report.value,
    userAgent: navigator.userAgent,
    url: window.location.href
  }
  
  const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `debug-logs-${Date.now()}.json`
  link.click()
  URL.revokeObjectURL(url)
  message.success('日志已导出')
}

const showShortcuts = () => {
  message.info('快捷键：Ctrl+Shift+F 一键修复，Ctrl+Shift+D 开/关控制台')
}

// 快捷键支持
const handleKeydown = (e) => {
  if (e.ctrlKey && e.shiftKey && e.key === 'D') {
    e.preventDefault()
    visible.value = !visible.value
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  
  // 开启统计信息定时更新
  statsTimer = setInterval(refreshStats, 3000)
  refreshStats()
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (statsTimer) {
    clearInterval(statsTimer)
  }
})
</script>

<style scoped>
.dev-console {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 400px;
  max-height: 600px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  overflow: hidden;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f5f5;
  border-bottom: 1px solid #d9d9d9;
}

.console-title {
  font-weight: 600;
  color: #262626;
}

.console-content {
  height: 100%;
  max-height: 540px;
  overflow-y: auto;
}

.tab-content {
  padding: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.stat-label {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.stat-value.danger {
  color: #ff4d4f;
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.report-section {
  margin-top: 16px;
}

.report-section h4 {
  margin: 0 0 8px 0;
  color: #262626;
}

.report-content {
  background: #f6f6f6;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 200px;
  overflow: auto;
  white-space: pre-wrap;
}

.info-list {
  space-y: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-label {
  font-weight: 500;
  color: #595959;
}

.info-value {
  color: #262626;
  font-family: monospace;
}

.quick-actions {
  display: grid;
  gap: 8px;
}

.console-trigger {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 48px;
  height: 48px;
  background: #1890ff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 9998;
  font-size: 18px;
  transition: all 0.3s ease;
}

.console-trigger:hover {
  background: #40a9ff;
  transform: scale(1.1);
}

/* 只在开发环境显示 */
.dev-console,
.console-trigger {
  display: none;
}

/* 通过body类名控制显示 */
body.dev-mode .dev-console,
body.dev-mode .console-trigger {
  display: block;
}
</style> 