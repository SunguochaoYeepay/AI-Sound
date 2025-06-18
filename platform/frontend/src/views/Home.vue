<template>
  <div class="home-container">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1>欢迎使用 AI-Sound 智能语音平台</h1>
          <p>专业的AI语音合成与声音克隆解决方案</p>
          <div class="quick-actions">
            <a-button type="primary" size="large" @click="navigateTo('voice-clone')">
              <template #icon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
              </template>
              开始声音克隆
            </a-button>
            <a-button size="large" @click="navigateTo('novel-projects')">
              <template #icon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
                </svg>
              </template>
              语音合成项目
            </a-button>
          </div>
        </div>
        <div class="welcome-illustration">
          <div class="floating-card">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="url(#gradient1)">
              <defs>
                <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#06b6d4"/>
                  <stop offset="100%" style="stop-color:#0891b2"/>
                </linearGradient>
              </defs>
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能卡片 -->
    <div class="feature-grid">
      <a-row :gutter="[24, 24]">
        <a-col :xs="24" :sm="12" :lg="6">
          <FeatureCard
            title="声音克隆测试"
            description="快速测试和体验AI声音克隆功能"
            icon="microphone"
            color="#06b6d4"
            @click="navigateTo('voice-clone')"
          />
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <FeatureCard
            title="声音库管理"
            description="管理和配置你的声音库资源"
            icon="star"
            color="#8b5cf6"
            @click="navigateTo('voice-library')"
          />
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <FeatureCard
            title="书籍管理"
            description="导入和管理你的文本内容"
            icon="book"
            color="#10b981"
            @click="navigateTo('books')"
          />
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <FeatureCard
            title="语音合成"
            description="创建和管理语音合成项目"
            icon="project"
            color="#f59e0b"
            @click="navigateTo('novel-projects')"
          />
        </a-col>
      </a-row>
    </div>

    <!-- 系统状态概览 -->
    <div class="status-overview">
      <a-card title="系统状态概览" :bordered="false" class="status-card">
        <template #extra>
          <a-space>
            <a-button type="text" @click="refreshStatus" :loading="refreshing" size="small">
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
                </svg>
              </template>
              刷新
            </a-button>
            <a-button type="text" @click="refreshStatus" :loading="refreshing" size="small">
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
                </svg>
              </template>
              刷新
            </a-button>
            <a-button type="link" @click="router.push('/settings')" size="small">
              详细状态
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
                </svg>
              </template>
            </a-button>
          </a-space>
        </template>
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :sm="8">
            <a-statistic
              title="数据库连接"
              :value="systemStatus.database === 'healthy' ? '正常' : '异常'"
              :value-style="{ color: systemStatus.database === 'healthy' ? '#3f8600' : '#cf1322' }"
            >
              <template #prefix>
                <svg width="16" height="16" viewBox="0 0 24 24" :fill="systemStatus.database === 'healthy' ? '#3f8600' : '#cf1322'">
                  <path d="M12 3c5.5 0 10 3.58 10 8s-4.5 8-10 8c-1.24 0-2.43-.18-3.53-.5C5.55 21 2 21 2 21c2.33-2.33 2.7-3.9 2.75-4.5C3.05 15.07 2 13.13 2 11c0-4.42 4.5-8 10-8z"/>
                </svg>
              </template>
            </a-statistic>
          </a-col>
          <a-col :xs="24" :sm="8">
            <a-statistic
              title="TTS服务"
              :value="systemStatus.tts_service === 'healthy' ? '正常' : '异常'"
              :value-style="{ color: systemStatus.tts_service === 'healthy' ? '#3f8600' : '#cf1322' }"
            >
              <template #prefix>
                <svg width="16" height="16" viewBox="0 0 24 24" :fill="systemStatus.tts_service === 'healthy' ? '#3f8600' : '#cf1322'">
                  <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                </svg>
              </template>
            </a-statistic>
          </a-col>
          <a-col :xs="24" :sm="8">
            <a-statistic
              title="音频文件"
              :value="audioLibraryCount"
              :value-style="{ color: '#3f8600' }"
            >
              <template #prefix>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="#3f8600">
                  <path d="M12 3l1.5 4.5h4.5l-3.75 2.7 1.5 4.5L12 12l-3.75 2.7 1.5-4.5L6 7.5h4.5L12 3z"/>
                </svg>
              </template>
            </a-statistic>
          </a-col>
        </a-row>
        
        <!-- 详细状态信息 -->
        <a-divider />
        <a-row :gutter="[16, 8]">
          <a-col :span="12">
            <div class="status-detail">
              <span class="detail-label">最后检查:</span>
              <span class="detail-value">{{ lastCheckTime }}</span>
            </div>
          </a-col>
          <a-col :span="12">
            <div class="status-detail">
              <span class="detail-label">平台版本:</span>
              <span class="detail-value">v2.0.0</span>
            </div>
          </a-col>
        </a-row>
        
        <!-- 添加系统性能小卡片 -->
        <a-divider />
        <a-row :gutter="[8, 8]">
          <a-col :span="6">
            <div class="mini-metric">
              <div class="mini-metric-label">CPU</div>
              <div class="mini-metric-value">45%</div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="mini-metric">
              <div class="mini-metric-label">内存</div>
              <div class="mini-metric-value">62%</div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="mini-metric">
              <div class="mini-metric-label">GPU</div>
              <div class="mini-metric-value">28%</div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="mini-metric">
              <div class="mini-metric-label">连接数</div>
              <div class="mini-metric-value">{{ wsStats.connections || 1 }}</div>
            </div>
          </a-col>
        </a-row>

        <!-- 最近通知 -->
        <div v-if="notifications.length > 0" class="notifications-section">
          <a-divider>最近通知</a-divider>
          <a-list 
            size="small" 
            :data-source="recentNotifications"
            :split="false"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #avatar>
                    <a-badge 
                      :status="getNotificationStatus(item.type)" 
                      :text="item.title"
                    />
                  </template>
                  <template #description>
                    <div class="notification-content">
                      <span>{{ item.message }}</span>
                      <small class="notification-time">
                        {{ formatTime(item.timestamp) }}
                      </small>
                    </div>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </a-card>
    </div>

    <!-- 最近活动 -->
    <div class="recent-activity">
      <a-card title="最近活动" :bordered="false" class="activity-card">
        <a-timeline>
          <a-timeline-item color="green">
            <template #dot>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="#52c41a">
                <path d="M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2ZM10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z"/>
              </svg>
            </template>
            系统启动完成 - 刚才
          </a-timeline-item>
          <a-timeline-item color="blue">
            <template #dot>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="#1890ff">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
            </template>
            声音库初始化完成 - 5分钟前
          </a-timeline-item>
          <a-timeline-item color="orange">
            <template #dot>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="#fa8c16">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
              </svg>
            </template>
            数据库连接建立 - 10分钟前
          </a-timeline-item>
        </a-timeline>
        <div style="text-align: center; margin-top: 16px;">
          <a-button type="link" @click="router.push('/settings')">查看详细状态</a-button>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app.js'
import { useWebSocketStore } from '../stores/websocket.js'
import { systemAPI } from '../api/v2.js'
import dayjs from 'dayjs'
import FeatureCard from '../components/FeatureCard.vue'

const router = useRouter()
const appStore = useAppStore()
const wsStore = useWebSocketStore()

// 响应式数据
const refreshing = ref(false)

// 计算属性
const systemStatus = computed(() => appStore.systemStatus)
const notifications = computed(() => appStore.notifications || [])
const audioLibraryCount = computed(() => 1247) // 模拟音频文件数量

const recentNotifications = computed(() => 
  notifications.value.slice(0, 3)
)

const lastCheckTime = computed(() => {
  if (!systemStatus.value.last_check) return '未检查'
  return dayjs(systemStatus.value.last_check).format('HH:mm:ss')
})

const wsStats = computed(() => {
  return {
    connections: wsStore.connected ? 1 : 0
  }
})

// 方法
const refreshStatus = async () => {
  refreshing.value = true
  try {
    const result = await systemAPI.healthCheck()
    if (result.success && result.data) {
      const services = result.data.services || {}
      appStore.updateSystemStatus({
        database: services.database?.status || 'unknown',
        tts_service: Object.values(services.tts_client || {}).every(Boolean) ? 'healthy' : 'unhealthy',
        websocket: services.websocket_manager?.status || 'unknown'
      })
    }
  } catch (error) {
    console.error('刷新状态失败:', error)
    appStore.updateSystemStatus({
      database: 'unhealthy',
      tts_service: 'unhealthy',
      websocket: 'unhealthy'
    })
  } finally {
    refreshing.value = false
  }
}

const getNotificationStatus = (type) => {
  const statusMap = {
    'success': 'success',
    'error': 'error',
    'warning': 'warning',
    'info': 'processing'
  }
  return statusMap[type] || 'default'
}

const formatTime = (timestamp) => {
  return dayjs(timestamp).format('MM-DD HH:mm')
}

// 导航函数
const navigateTo = (route) => {
  const routeMap = {
    'voice-clone': '/basic-tts',
    'voice-library': '/characters',
    'books': '/books',
    'novel-projects': '/novel-reader'
  }
  
  router.push(routeMap[route] || route)
}
</script>

<style scoped>
.home-container {

  margin: 0 auto;
  padding: 0 24px;
}

.welcome-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 48px;
  margin-bottom: 32px;
  color: white;
  position: relative;
  overflow: hidden;
}

.welcome-banner::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

.welcome-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.welcome-text h1 {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 16px;
  background: linear-gradient(45deg, #ffffff, #f0f9ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-text p {
  font-size: 18px;
  margin-bottom: 32px;
  opacity: 0.9;
}

.quick-actions {
  display: flex;
  gap: 16px;
}

.quick-actions .ant-btn {
  height: 48px;
  padding: 0 24px;
  border-radius: 8px;
  font-weight: 500;
  border: none;
}

.quick-actions .ant-btn-primary {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  box-shadow: 0 4px 16px rgba(6, 182, 212, 0.3);
}

.quick-actions .ant-btn:not(.ant-btn-primary) {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  backdrop-filter: blur(10px);
}

.welcome-illustration {
  display: flex;
  align-items: center;
  justify-content: center;
}

.floating-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  animation: float 4s ease-in-out infinite;
}

.feature-grid {
  margin-bottom: 32px;
}

.status-overview {
  margin-bottom: 32px;
}

.status-card {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

.status-card :deep(.ant-card-head) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.status-card :deep(.ant-card-head-title) {
  font-weight: 600;
  color: #1f2937;
}

.recent-activity {
  margin-bottom: 32px;
}

.activity-card {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

.activity-card :deep(.ant-card-head) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.activity-card :deep(.ant-card-head-title) {
  font-weight: 600;
  color: #1f2937;
}

.mini-metric {
  text-align: center;
  padding: 8px;
  background: rgba(0,0,0,0.02);
  border-radius: 6px;
  transition: all 0.2s;
}

.mini-metric:hover {
  background: rgba(24, 144, 255, 0.05);
  transform: translateY(-1px);
}

.mini-metric-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 2px;
}

.mini-metric-value {
  font-size: 16px;
  font-weight: 600;
  color: #1890ff;
}

.status-detail {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}

.detail-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.detail-value {
  font-size: 14px;
  color: #1f2937;
}

.notifications-section {
  margin-top: 16px;
}

.notification-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-time {
  color: #999;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .welcome-banner {
    padding: 32px 24px;
  }
  
  .welcome-content {
    flex-direction: column;
    text-align: center;
    gap: 32px;
  }
  
  .welcome-text h1 {
    font-size: 28px;
  }
  
  .quick-actions {
    justify-content: center;
  }
  
  .floating-card {
    padding: 24px;
  }
}
</style> 