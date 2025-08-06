/**
 * WebSocket状态管理
 * 管理实时通信连接和消息
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getBackendUrl } from '@/config/services'
import { useAppStore } from './app'

export const useWebSocketStore = defineStore('websocket', () => {
  const appStore = useAppStore()

  // WebSocket连接状态
  const ws = ref(null)
  const connected = ref(false)
  const connecting = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = ref(5)

  // 消息队列
  const messageQueue = ref([])
  const subscriptions = ref(new Map())

  // 统计信息
  const stats = ref({
    messagesReceived: 0,
    messagesSent: 0,
    lastActivity: null,
    connectionTime: null
  })

  // 计算属性
  const connectionStatus = computed(() => {
    if (connecting.value) return 'connecting'
    if (connected.value) return 'connected'
    return 'disconnected'
  })

  const hasQueuedMessages = computed(() => messageQueue.value.length > 0)

  // WebSocket URL
  const getWebSocketUrl = () => {
    // 在开发环境中，使用相对路径通过Vite代理
    if (import.meta.env.DEV) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${protocol}//${window.location.host}/ws`
    }

    // 生产环境也使用相对路径，通过代理处理
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/ws`
  }

  // 连接WebSocket
  const connect = () => {
    if (connected.value || connecting.value) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      try {
        connecting.value = true
        const wsUrl = getWebSocketUrl()

        console.log('🔌 尝试连接WebSocket:', wsUrl)
        console.log('🔍 环境信息:', {
          dev: import.meta.env.DEV,
          baseUrl: import.meta.env.VITE_API_BASE_URL,
          location: window.location.host
        })

        ws.value = new WebSocket(wsUrl)

        ws.value.onopen = () => {
          connected.value = true
          connecting.value = false
          reconnectAttempts.value = 0
          stats.value.connectionTime = new Date()

          console.log('✅ WebSocket连接已建立')
          appStore.addNotification({
            type: 'success',
            title: 'WebSocket连接',
            message: '实时通信连接已建立'
          })

          // 发送排队的消息
          flushMessageQueue()

          resolve()
        }

        ws.value.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            handleMessage(data)
            stats.value.messagesReceived++
            stats.value.lastActivity = new Date()
          } catch (error) {
            console.error('WebSocket消息解析失败:', error)
          }
        }

        ws.value.onclose = (event) => {
          connected.value = false
          connecting.value = false

          console.log('🔌 WebSocket连接已关闭', event.code, event.reason)

          // 尝试重连
          if (!event.wasClean && reconnectAttempts.value < maxReconnectAttempts.value) {
            scheduleReconnect()
          } else {
            appStore.addNotification({
              type: 'warning',
              title: 'WebSocket断开',
              message: '实时通信连接已断开'
            })
          }
        }

        ws.value.onerror = (error) => {
          console.error('WebSocket连接错误:', error)
          connecting.value = false

          appStore.addNotification({
            type: 'error',
            title: 'WebSocket错误',
            message: '实时通信连接发生错误'
          })

          reject(error)
        }
      } catch (error) {
        connecting.value = false
        reject(error)
      }
    })
  }

  // 断开连接
  const disconnect = () => {
    if (ws.value) {
      ws.value.close(1000, 'Client disconnecting')
      ws.value = null
    }
    connected.value = false
    connecting.value = false
    subscriptions.value.clear()
    messageQueue.value = []
  }

  // 发送消息
  const sendMessage = (type, data = {}) => {
    const message = {
      type,
      data,
      timestamp: new Date().toISOString()
    }

    if (connected.value && ws.value?.readyState === WebSocket.OPEN) {
      try {
        ws.value.send(JSON.stringify(message))
        stats.value.messagesSent++
        stats.value.lastActivity = new Date()
        return true
      } catch (error) {
        console.error('发送WebSocket消息失败:', error)
        // 添加到队列重试
        messageQueue.value.push(message)
        return false
      }
    } else {
      // 连接未建立，添加到队列
      messageQueue.value.push(message)
      return false
    }
  }

  // 订阅消息类型
  const subscribe = (messageType, callback) => {
    if (!subscriptions.value.has(messageType)) {
      subscriptions.value.set(messageType, new Set())
    }
    subscriptions.value.get(messageType).add(callback)

    // 返回取消订阅函数
    return () => {
      const callbacks = subscriptions.value.get(messageType)
      if (callbacks) {
        callbacks.delete(callback)
        if (callbacks.size === 0) {
          subscriptions.value.delete(messageType)
        }
      }
    }
  }

  // 处理接收到的消息
  const handleMessage = (message) => {
    const { type, data } = message

    // 调用订阅的回调函数
    const callbacks = subscriptions.value.get(type)
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(data, message)
        } catch (error) {
          console.error('WebSocket消息处理回调出错:', error)
        }
      })
    }

    // 处理通用消息类型
    switch (type) {
      case 'notification':
        appStore.addNotification(data)
        break
      case 'system_status':
        appStore.updateSystemStatus(data)
        break
      case 'subscription_confirmed':
        console.log('✅ 订阅确认:', data)
        break
      case 'unsubscription_confirmed':
        console.log('✅ 取消订阅确认:', data)
        break
      case 'connection_established':
        console.log('✅ 连接建立确认:', data)
        break
      case 'topic_message':
        // 主题消息类型，已通过回调处理，不需要额外操作
        console.log('📨 处理主题消息:', message.topic, data?.type || 'unknown')
        break
      default:
        // 未知消息类型，记录详细日志
        if (type !== 'heartbeat' && type !== 'ping' && type !== 'pong') {
          console.log('收到未知类型的WebSocket消息:', type, data)
        }
    }
  }

  // 清空消息队列
  const flushMessageQueue = () => {
    if (!connected.value || messageQueue.value.length === 0) {
      return
    }

    const queue = [...messageQueue.value]
    messageQueue.value = []

    queue.forEach((message) => {
      if (ws.value?.readyState === WebSocket.OPEN) {
        try {
          ws.value.send(JSON.stringify(message))
          stats.value.messagesSent++
        } catch (error) {
          console.error('发送排队消息失败:', error)
          messageQueue.value.push(message)
        }
      }
    })
  }

  // 安排重连
  const scheduleReconnect = () => {
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)
    reconnectAttempts.value++

    console.log(`⏱️ ${delay / 1000}秒后尝试重连 (第${reconnectAttempts.value}次)`)

    setTimeout(() => {
      if (!connected.value) {
        connect().catch(() => {
          // 重连失败，继续尝试
          if (reconnectAttempts.value < maxReconnectAttempts.value) {
            scheduleReconnect()
          }
        })
      }
    }, delay)
  }

  // 获取连接统计
  const getStats = () => {
    return {
      ...stats.value,
      connected: connected.value,
      reconnectAttempts: reconnectAttempts.value,
      queuedMessages: messageQueue.value.length,
      subscriptions: subscriptions.value.size
    }
  }

  return {
    // 状态
    connected,
    connecting,
    connectionStatus,
    hasQueuedMessages,
    stats,

    // 方法
    connect,
    disconnect,
    sendMessage,
    subscribe,
    getStats
  }
})
