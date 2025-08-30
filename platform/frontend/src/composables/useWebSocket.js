import { ref, onMounted, onUnmounted } from 'vue'
import { storyboardAPI } from '@/api/storyboard'

/**
 * WebSocket连接管理
 * 用于实时接收分析进度更新
 */
export function useWebSocket(sessionId) {
  const isConnected = ref(false)
  const progress = ref(0)
  const currentStep = ref('')
  const error = ref(null)
  const ws = ref(null)

  // 连接WebSocket
  const connect = () => {
    if (!sessionId) return

    try {
      ws.value = storyboardAPI.createWebSocket(sessionId)
      
      ws.value.onopen = () => {
        isConnected.value = true
        error.value = null
        console.log('WebSocket连接已建立')
      }
      
      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'progress') {
            progress.value = data.progress || 0
            currentStep.value = data.step || ''
          } else if (data.type === 'error') {
            error.value = data.message || '分析过程中发生错误'
          } else if (data.type === 'complete') {
            progress.value = 100
            currentStep.value = '分析完成'
            isConnected.value = false
          }
        } catch (err) {
          console.error('解析WebSocket消息失败:', err)
        }
      }
      
      ws.value.onerror = (event) => {
        error.value = 'WebSocket连接错误'
        isConnected.value = false
        console.error('WebSocket错误:', event)
      }
      
      ws.value.onclose = () => {
        isConnected.value = false
        console.log('WebSocket连接已关闭')
      }
    } catch (err) {
      error.value = '创建WebSocket连接失败: ' + err.message
      console.error('WebSocket连接失败:', err)
    }
  }

  // 断开连接
  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    isConnected.value = false
  }

  // 重新连接
  const reconnect = () => {
    disconnect()
    setTimeout(connect, 1000)
  }

  // 组件挂载时连接
  onMounted(() => {
    if (sessionId) {
      connect()
    }
  })

  // 组件卸载时断开连接
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    progress,
    currentStep,
    error,
    connect,
    disconnect,
    reconnect
  }
}
