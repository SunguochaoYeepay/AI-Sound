<template>
  <div class="system-status">
    <a-card title="系统状态" size="small" :loading="loading">
      <template #extra>
        <a-button 
          type="text" 
          size="small" 
          @click="refreshStatus"
          :loading="refreshing"
        >
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新
        </a-button>
      </template>

      <a-row :gutter="[16, 16]">
        <!-- 数据库状态 -->
        <a-col :span="8">
          <a-statistic
            title="数据库"
            :value="systemStatus.database"
            :value-style="getStatusStyle(systemStatus.database)"
          >
            <template #prefix>
              <DatabaseOutlined />
            </template>
          </a-statistic>
        </a-col>

        <!-- TTS服务状态 -->
        <a-col :span="8">
          <a-statistic
            title="TTS服务"
            :value="systemStatus.tts_service"
            :value-style="getStatusStyle(systemStatus.tts_service)"
          >
            <template #prefix>
              <SoundOutlined />
            </template>
          </a-statistic>
        </a-col>

        <!-- WebSocket状态 -->
        <a-col :span="8">
          <a-statistic
            title="实时通信"
            :value="websocketStatus"
            :value-style="getStatusStyle(websocketStatus)"
          >
            <template #prefix>
              <WifiOutlined />
            </template>
          </a-statistic>
        </a-col>
      </a-row>

      <!-- 详细状态 -->
      <a-divider />
      
      <a-descriptions size="small" :column="2">
        <a-descriptions-item label="最后检查">
          {{ lastCheckTime }}
        </a-descriptions-item>
        <a-descriptions-item label="连接统计">
          发送: {{ wsStats.messagesSent }} | 接收: {{ wsStats.messagesReceived }}
        </a-descriptions-item>
      </a-descriptions>

      <!-- 通知列表 -->
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
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '../stores/app.js'
import { useWebSocketStore } from '../stores/websocket.js'
import { systemAPI } from '../api/v2.js'
import dayjs from 'dayjs'
import {
  ReloadOutlined,
  DatabaseOutlined,
  SoundOutlined,
  WifiOutlined
} from '@ant-design/icons-vue'

// Store
const appStore = useAppStore()
const wsStore = useWebSocketStore()

// 响应式数据
const loading = ref(false)
const refreshing = ref(false)
const healthCheckInterval = ref(null)

// 计算属性
const systemStatus = computed(() => appStore.systemStatus)
const notifications = computed(() => appStore.notifications)
const websocketStatus = computed(() => wsStore.connectionStatus)
const wsStats = computed(() => wsStore.stats)

const recentNotifications = computed(() => 
  notifications.value.slice(0, 3)
)

const lastCheckTime = computed(() => {
  if (!systemStatus.value.last_check) return '未检查'
  return dayjs(systemStatus.value.last_check).format('HH:mm:ss')
})

// 方法
const getStatusStyle = (status) => {
  const statusMap = {
    'healthy': { color: '#52c41a' },
    'connected': { color: '#52c41a' },
    'unhealthy': { color: '#ff4d4f' },
    'disconnected': { color: '#ff4d4f' },
    'degraded': { color: '#fa8c16' },
    'connecting': { color: '#1890ff' },
    'unknown': { color: '#d9d9d9' }
  }
  return statusMap[status] || statusMap['unknown']
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

const refreshStatus = async () => {
  refreshing.value = true
  try {
    await checkSystemHealth()
  } finally {
    refreshing.value = false
  }
}

const checkSystemHealth = async () => {
  try {
    const result = await systemAPI.healthCheck()
    if (result.success && result.data) {
      appStore.updateSystemStatus({
        database: result.data.services?.database?.status || 'unknown',
        tts_service: Object.values(result.data.services?.tts_client || {}).every(Boolean) ? 'healthy' : 'unhealthy',
        websocket: result.data.services?.websocket_manager?.status || 'unknown'
      })
    }
  } catch (error) {
    console.error('系统健康检查失败:', error)
  }
}

const startHealthCheck = () => {
  // 立即执行一次
  checkSystemHealth()
  
  // 设置定时器，每30秒检查一次
  healthCheckInterval.value = setInterval(checkSystemHealth, 30000)
}

const stopHealthCheck = () => {
  if (healthCheckInterval.value) {
    clearInterval(healthCheckInterval.value)
    healthCheckInterval.value = null
  }
}

// 生命周期
onMounted(() => {
  loading.value = true
  
  // 启动健康检查
  startHealthCheck()
  
  // 连接WebSocket
  wsStore.connect().catch(error => {
    console.error('WebSocket连接失败:', error)
  })
  
  loading.value = false
})

onUnmounted(() => {
  stopHealthCheck()
})
</script>

<style scoped>
.system-status {
  margin-bottom: 16px;
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
</style> 