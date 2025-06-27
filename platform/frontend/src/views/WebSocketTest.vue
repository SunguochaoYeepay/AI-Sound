<template>
  <div class="websocket-test">
    <a-card title="WebSocket连接测试" size="small">
      <template #extra>
        <a-space>
          <a-button 
            type="primary" 
            @click="connectWebSocket"
            :loading="connecting"
            :disabled="connected"
          >
            连接WebSocket
          </a-button>
          <a-button 
            @click="disconnectWebSocket"
            :disabled="!connected"
          >
            断开连接
          </a-button>
        </a-space>
      </template>

      <!-- 连接状态 -->
      <a-row :gutter="16">
        <a-col :span="8">
          <a-statistic
            title="连接状态"
            :value="connectionStatus"
            :value-style="getStatusStyle(connectionStatus)"
          >
            <template #prefix>
              <WifiOutlined />
            </template>
          </a-statistic>
        </a-col>
        
        <a-col :span="8">
          <a-statistic
            title="发送消息"
            :value="stats.messagesSent"
          >
            <template #prefix>
              <ArrowUpOutlined />
            </template>
          </a-statistic>
        </a-col>
        
        <a-col :span="8">
          <a-statistic
            title="接收消息"
            :value="stats.messagesReceived"
          >
            <template #prefix>
              <ArrowDownOutlined />
            </template>
          </a-statistic>
        </a-col>
      </a-row>

      <a-divider />

      <!-- 测试消息 -->
      <a-row :gutter="16">
        <a-col :span="16">
          <a-input
            v-model:value="testMessage"
            placeholder="输入测试消息"
            @press-enter="sendTestMessage"
          />
        </a-col>
        <a-col :span="8">
          <a-button 
            type="primary" 
            @click="sendTestMessage"
            :disabled="!connected"
            block
          >
            发送测试消息
          </a-button>
        </a-col>
      </a-row>

      <a-divider />

      <!-- 连接信息 -->
      <a-descriptions title="连接信息" size="small" :column="2">
        <a-descriptions-item label="WebSocket URL">
          {{ wsUrl }}
        </a-descriptions-item>
        <a-descriptions-item label="连接时间">
          {{ connectionTime }}
        </a-descriptions-item>
        <a-descriptions-item label="最后活动">
          {{ lastActivity }}
        </a-descriptions-item>
        <a-descriptions-item label="重连次数">
          {{ reconnectAttempts }}
        </a-descriptions-item>
      </a-descriptions>

      <!-- 消息日志 -->
      <a-divider />
      <div class="message-log">
        <h4>消息日志</h4>
        <a-list 
          size="small" 
          :data-source="messageLog"
          :split="false"
          style="max-height: 300px; overflow-y: auto;"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta>
                <template #avatar>
                  <a-tag :color="item.type === 'sent' ? 'blue' : 'green'">
                    {{ item.type === 'sent' ? '发送' : '接收' }}
                  </a-tag>
                </template>
                <template #title>
                  <span class="message-time">{{ item.timestamp }}</span>
                </template>
                <template #description>
                  <pre class="message-content">{{ item.content }}</pre>
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
import { useWebSocketStore } from '../stores/websocket.js'
import { message } from 'ant-design-vue'
import { getBackendUrl } from '@/config/services'
import dayjs from 'dayjs'
import {
  WifiOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons-vue'

// Store
const wsStore = useWebSocketStore()

// 响应式数据
const testMessage = ref('Hello WebSocket!')
const messageLog = ref([])
const unsubscribe = ref(null)

// 计算属性
const connected = computed(() => wsStore.connected)
const connecting = computed(() => wsStore.connecting)
const connectionStatus = computed(() => wsStore.connectionStatus)
const stats = computed(() => wsStore.stats)
const reconnectAttempts = computed(() => wsStore.stats?.reconnectAttempts || 0)

const wsUrl = computed(() => {
  // 复制WebSocket URL生成逻辑
  if (import.meta.env.DEV) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/ws`
  }
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const baseUrl = import.meta.env.VITE_API_BASE_URL || getBackendUrl()
  const cleanHost = baseUrl.replace(/^https?:\/\//, '')
  return `${protocol}//${cleanHost}/ws`
})

const connectionTime = computed(() => {
  if (!stats.value?.connectionTime) return '未连接'
  return dayjs(stats.value.connectionTime).format('HH:mm:ss')
})

const lastActivity = computed(() => {
  if (!stats.value?.lastActivity) return '无活动'
  return dayjs(stats.value.lastActivity).format('HH:mm:ss')
})

// 方法
const getStatusStyle = (status) => {
  const statusMap = {
    'connected': { color: '#52c41a' },
    'connecting': { color: '#1890ff' },
    'disconnected': { color: '#ff4d4f' }
  }
  return statusMap[status] || { color: '#d9d9d9' }
}

const connectWebSocket = async () => {
  try {
    await wsStore.connect()
    message.success('WebSocket连接成功')
    
    addLogMessage('system', '连接建立成功')
    
    // 订阅所有消息类型进行测试
    unsubscribe.value = wsStore.subscribe('test', (data, fullMessage) => {
      addLogMessage('received', JSON.stringify(fullMessage, null, 2))
    })
    
  } catch (error) {
    console.error('WebSocket连接失败:', error)
    message.error('WebSocket连接失败: ' + error.message)
    addLogMessage('error', '连接失败: ' + error.message)
  }
}

const disconnectWebSocket = () => {
  wsStore.disconnect()
  message.info('WebSocket连接已断开')
  addLogMessage('system', '连接已断开')
  
  if (unsubscribe.value) {
    unsubscribe.value()
    unsubscribe.value = null
  }
}

const sendTestMessage = () => {
  if (!connected.value) {
    message.warning('请先连接WebSocket')
    return
  }
  
  const success = wsStore.sendMessage('test', {
    message: testMessage.value,
    timestamp: new Date().toISOString()
  })
  
  if (success) {
    addLogMessage('sent', JSON.stringify({
      type: 'test',
      data: {
        message: testMessage.value,
        timestamp: new Date().toISOString()
      }
    }, null, 2))
    
    message.success('消息发送成功')
  } else {
    message.error('消息发送失败')
    addLogMessage('error', '消息发送失败')
  }
}

const addLogMessage = (type, content) => {
  messageLog.value.unshift({
    type,
    content,
    timestamp: dayjs().format('HH:mm:ss.SSS')
  })
  
  // 限制日志条数
  if (messageLog.value.length > 50) {
    messageLog.value = messageLog.value.slice(0, 50)
  }
}

// 生命周期
onMounted(() => {
  addLogMessage('system', '测试页面已加载')
  addLogMessage('info', `WebSocket URL: ${wsUrl.value}`)
})

onUnmounted(() => {
  if (unsubscribe.value) {
    unsubscribe.value()
  }
})
</script>

<style scoped>
.websocket-test {
  padding: 24px;
}

.message-log {
  margin-top: 16px;
}

.message-time {
  font-size: 12px;
  color: #999;
}

.message-content {
  margin: 0;
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style> 