<template>
  <div class="settings-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 700;">
          系统设置
        </h1>
        <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
          查看引擎状态和系统配置信息
        </p>
      </div>
      <div class="header-actions">
        <a-button type="primary" size="large" @click="refreshStatus" :loading="refreshing" ghost>
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
            </svg>
          </template>
          刷新状态
        </a-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧：引擎状态 -->
      <div class="status-panel">
        <!-- 引擎状态卡片 -->
        <a-card title="MegaTTS3 引擎状态" :bordered="false" class="status-card">
          <template #extra>
            <a-tag :color="engineStatus.status === 'running' ? 'success' : 'error'" size="large">
              <template #icon>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <circle cx="12" cy="12" r="6"/>
                </svg>
              </template>
              {{ engineStatus.status === 'running' ? '运行中' : '离线' }}
            </a-tag>
          </template>

          <div class="status-info">
            <div class="info-row">
              <span class="info-label">服务地址:</span>
              <span class="info-value">{{ engineStatus.host }}:{{ engineStatus.port }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">引擎版本:</span>
              <span class="info-value">{{ engineStatus.version }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">启动时间:</span>
              <span class="info-value">{{ engineStatus.startTime }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">运行时长:</span>
              <span class="info-value">{{ engineStatus.uptime }}</span>
            </div>
          </div>
        </a-card>

        <!-- 性能监控 -->
        <a-card title="性能监控" :bordered="false" class="performance-card">
          <div class="performance-metrics">
            <div class="metric-item">
              <div class="metric-label">CPU 使用率</div>
              <a-progress 
                :percent="performanceData.cpu" 
                :stroke-color="getProgressColor(performanceData.cpu)"
                :show-info="true"
              />
            </div>
            <div class="metric-item">
              <div class="metric-label">内存使用率</div>
              <a-progress 
                :percent="performanceData.memory" 
                :stroke-color="getProgressColor(performanceData.memory)"
                :show-info="true"
              />
            </div>
            <div class="metric-item">
              <div class="metric-label">GPU 使用率</div>
              <a-progress 
                :percent="performanceData.gpu" 
                :stroke-color="getProgressColor(performanceData.gpu)"
                :show-info="true"
              />
            </div>
            <div class="metric-item">
              <div class="metric-label">VRAM 使用</div>
              <a-progress 
                :percent="performanceData.vram" 
                :stroke-color="getProgressColor(performanceData.vram)"
                :show-info="true"
              />
            </div>
          </div>
        </a-card>

        <!-- 系统信息 -->
        <a-card title="系统信息" :bordered="false" class="system-card">
          <div class="system-info">
            <div class="info-section">
              <h4>硬件信息</h4>
              <div class="info-grid">
                <div class="info-item">
                  <span class="item-label">CPU:</span>
                  <span class="item-value">{{ systemInfo.cpu }}</span>
                </div>
                <div class="info-item">
                  <span class="item-label">内存:</span>
                  <span class="item-value">{{ systemInfo.memory }}</span>
                </div>
                <div class="info-item">
                  <span class="item-label">GPU:</span>
                  <span class="item-value">{{ systemInfo.gpu }}</span>
                </div>
                <div class="info-item">
                  <span class="item-label">VRAM:</span>
                  <span class="item-value">{{ systemInfo.vram }}</span>
                </div>
              </div>
            </div>

            <a-divider />

            <div class="info-section">
              <h4>软件环境</h4>
              <div class="info-grid">
                <div class="info-item">
                  <span class="item-label">操作系统:</span>
                  <span class="item-value">{{ systemInfo.os }}</span>
                </div>
                <div class="info-item">
                  <span class="item-label">Python:</span>
                  <span class="item-value">{{ systemInfo.python }}</span>
                </div>
                <div class="info-item">
                  <span class="item-label">PyTorch:</span>
                  <span class="item-value">{{ systemInfo.pytorch }}</span>
                </div>
                <div class="info-item">
                  <span class="item-label">CUDA:</span>
                  <span class="item-value">{{ systemInfo.cuda }}</span>
                </div>
              </div>
            </div>
          </div>
        </a-card>
      </div>

      <!-- 右侧：模型信息和统计 -->
      <div class="info-panel">
        <!-- 模型信息 -->
        <a-card title="已加载模型" :bordered="false" class="models-card">
          <div class="models-list">
            <div 
              v-for="model in loadedModels" 
              :key="model.name"
              class="model-item"
              :class="{ 'active': model.status === 'loaded' }"
            >
              <div class="model-info">
                <div class="model-name">{{ model.name }}</div>
                <div class="model-desc">{{ model.description }}</div>
              </div>
              <div class="model-status">
                <a-tag :color="model.status === 'loaded' ? 'success' : 'default'">
                  {{ model.status === 'loaded' ? '已加载' : '未加载' }}
                </a-tag>
                <div class="model-size">{{ model.size }}</div>
              </div>
            </div>
          </div>
        </a-card>

        <!-- 使用统计 -->
        <a-card title="使用统计" :bordered="false" class="stats-card">
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-icon" style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ usageStats.totalRequests }}</div>
                <div class="stat-label">总请求数</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ usageStats.successRate }}%</div>
                <div class="stat-label">成功率</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ usageStats.avgProcessTime }}s</div>
                <div class="stat-label">平均处理时间</div>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                  <path d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"/>
                </svg>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ usageStats.totalAudioGenerated }}</div>
                <div class="stat-label">生成音频总数</div>
              </div>
            </div>
          </div>
        </a-card>

        <!-- 服务日志 -->
        <a-card title="服务日志" :bordered="false" class="logs-card">
          <template #extra>
            <a-button type="text" size="small" @click="clearLogs">
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                </svg>
              </template>
              清空日志
            </a-button>
          </template>

          <div class="logs-container">
            <div 
              v-for="(log, index) in serviceLogs" 
              :key="index"
              class="log-item"
              :class="log.level"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-level">{{ log.level.toUpperCase() }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'

// 响应式数据
const refreshing = ref(false)

// 引擎状态
const engineStatus = reactive({
  status: 'running',
  host: 'localhost',
  port: 7929,
  version: 'v3.2.1',
  startTime: '2024-01-20 09:30:15',
  uptime: '3天 14小时 25分钟'
})

// 性能数据
const performanceData = reactive({
  cpu: 45,
  memory: 68,
  gpu: 72,
  vram: 58
})

// 系统信息
const systemInfo = reactive({
  cpu: 'Intel Core i7-12700K @ 3.60GHz',
  memory: '32GB DDR4-3200',
  gpu: 'NVIDIA RTX 4080 Super',
  vram: '16GB GDDR6X',
  os: 'Windows 11 Pro 23H2',
  python: '3.11.7',
  pytorch: '2.1.2+cu121',
  cuda: '12.1'
})

// 已加载模型
const loadedModels = ref([
  {
    name: 'MegaTTS3-Base',
    description: '基础语音合成模型',
    status: 'loaded',
    size: '2.8GB'
  },
  {
    name: 'Voice-Cloning',
    description: '声音克隆专用模型',
    status: 'loaded',
    size: '1.2GB'
  },
  {
    name: 'Multi-Speaker',
    description: '多角色语音模型',
    status: 'loaded',
    size: '3.5GB'
  },
  {
    name: 'Emotion-TTS',
    description: '情感语音合成模型',
    status: 'unloaded',
    size: '2.1GB'
  }
])

// 使用统计
const usageStats = reactive({
  totalRequests: 2468,
  successRate: 98.5,
  avgProcessTime: 3.2,
  totalAudioGenerated: 1234
})

// 服务日志
const serviceLogs = ref([
  {
    time: '2024-01-23 15:30:45',
    level: 'info',
    message: 'Voice cloning request completed successfully'
  },
  {
    time: '2024-01-23 15:29:12',
    level: 'info',
    message: 'Loading voice model: 温柔女声'
  },
  {
    time: '2024-01-23 15:28:33',
    level: 'warn',
    message: 'GPU memory usage is high: 89%'
  },
  {
    time: '2024-01-23 15:27:54',
    level: 'info',
    message: 'New audio generation request received'
  },
  {
    time: '2024-01-23 15:26:18',
    level: 'error',
    message: 'Failed to process audio file: invalid format'
  },
  {
    time: '2024-01-23 15:25:01',
    level: 'info',
    message: 'MegaTTS3 engine initialized successfully'
  }
])

// 方法
const getProgressColor = (percent) => {
  if (percent < 50) return '#06b6d4'
  if (percent < 80) return '#f59e0b'
  return '#ef4444'
}

const refreshStatus = async () => {
  refreshing.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 更新性能数据
    performanceData.cpu = Math.floor(Math.random() * 30) + 40
    performanceData.memory = Math.floor(Math.random() * 20) + 60
    performanceData.gpu = Math.floor(Math.random() * 25) + 65
    performanceData.vram = Math.floor(Math.random() * 30) + 50
    
    // 添加新日志
    const now = new Date()
    const timeStr = now.toLocaleString('zh-CN', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    })
    
    serviceLogs.value.unshift({
      time: timeStr,
      level: 'info',
      message: 'System status refreshed'
    })
    
    // 保持日志数量不超过20条
    if (serviceLogs.value.length > 20) {
      serviceLogs.value = serviceLogs.value.slice(0, 20)
    }
    
    message.success('状态刷新成功')
  } catch (error) {
    message.error('状态刷新失败')
  } finally {
    refreshing.value = false
  }
}

const clearLogs = () => {
  serviceLogs.value = []
  message.success('日志已清空')
}

// 页面加载时初始化
onMounted(() => {
  // 这里可以添加初始化逻辑，比如从API获取真实状态
})
</script>

<style scoped>
.settings-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 32px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  border-radius: 16px;
  color: white;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
}

.status-card, .performance-card, .system-card, .models-card, .stats-card, .logs-card {
  margin-bottom: 24px;
  border-radius: 12px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
  border: none !important;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.info-label {
  color: #6b7280;
  font-weight: 500;
}

.info-value {
  color: #374151;
  font-weight: 600;
}

.performance-metrics {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-label {
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

.system-info h4 {
  color: #374151;
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: #f8fafc;
  border-radius: 6px;
}

.item-label {
  color: #6b7280;
  font-size: 13px;
  font-weight: 500;
}

.item-value {
  color: #374151;
  font-size: 13px;
  font-weight: 600;
}

.models-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.3s;
}

.model-item:hover {
  border-color: #06b6d4;
  background: #f0f9ff;
}

.model-item.active {
  border-color: #10b981;
  background: #f0fdf4;
}

.model-info {
  flex: 1;
}

.model-name {
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.model-desc {
  font-size: 12px;
  color: #6b7280;
}

.model-status {
  text-align: right;
}

.model-size {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.4;
}

.log-item.info {
  background: #f0f9ff;
  border-left: 3px solid #06b6d4;
}

.log-item.warn {
  background: #fffbeb;
  border-left: 3px solid #f59e0b;
}

.log-item.error {
  background: #fef2f2;
  border-left: 3px solid #ef4444;
}

.log-time {
  color: #6b7280;
  min-width: 120px;
}

.log-level {
  color: #374151;
  font-weight: 600;
  min-width: 50px;
}

.log-message {
  color: #374151;
  flex: 1;
}

/* 滚动条样式 */
.logs-container::-webkit-scrollbar {
  width: 4px;
}

.logs-container::-webkit-scrollbar-track {
  background: #f5f3f0;
  border-radius: 2px;
}

.logs-container::-webkit-scrollbar-thumb {
  background: #06b6d4;
  border-radius: 2px;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style> 