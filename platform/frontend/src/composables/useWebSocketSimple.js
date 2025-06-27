import { ref } from 'vue'

let websocketInstance = null
const isConnected = ref(false)
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 5

export function useWebSocket() {
  const connect = async () => {
    try {
      if (websocketInstance && websocketInstance.readyState === WebSocket.OPEN) {
        console.log('WebSocket已连接')
        return true
      }

      const wsUrl = (() => {
        if (import.meta.env.VITE_WS_URL) {
          return import.meta.env.VITE_WS_URL
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.host
        
        if (host.includes(':3000')) {
          return `${protocol}//${window.location.hostname}:8000/ws`
        } else if (host.includes('localhost:8001') || host.includes('127.0.0.1:8001')) {
          return `${protocol}//${window.location.hostname}:8001/ws`
        } else {
          return `${protocol}//${host}/ws`
        }
      })()
      
      console.log('🔗 连接WebSocket:', wsUrl)
      
      websocketInstance = new WebSocket(wsUrl)
      
      websocketInstance.onopen = () => {
        console.log('✅ WebSocket连接成功')
        isConnected.value = true
        reconnectAttempts.value = 0
      }
      
      websocketInstance.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('📨 收到WebSocket消息:', data)
          
          // 发送自定义事件
          window.dispatchEvent(new CustomEvent('websocket_message', {
            detail: event.data
          }))
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }
      
      websocketInstance.onclose = (event) => {
        console.log('❌ WebSocket连接关闭:', event.code, event.reason)
        isConnected.value = false
        
        // 自动重连
        if (reconnectAttempts.value < maxReconnectAttempts) {
          reconnectAttempts.value++
          console.log(`🔄 尝试重连 (${reconnectAttempts.value}/${maxReconnectAttempts})`)
          setTimeout(() => {
            connect()
          }, 2000 * reconnectAttempts.value)
        }
      }
      
      websocketInstance.onerror = (error) => {
        console.error('❌ WebSocket错误:', error)
        isConnected.value = false
      }
      
      return true
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      isConnected.value = false
      return false
    }
  }
  
  const disconnect = () => {
    if (websocketInstance) {
      websocketInstance.close()
      websocketInstance = null
    }
    isConnected.value = false
  }
  
  const send = (message) => {
    if (websocketInstance && websocketInstance.readyState === WebSocket.OPEN) {
      websocketInstance.send(JSON.stringify(message))
      return true
    }
    console.warn('WebSocket未连接，无法发送消息')
    return false
  }
  
  return {
    connect,
    disconnect,
    send,
    isConnected
  }
}