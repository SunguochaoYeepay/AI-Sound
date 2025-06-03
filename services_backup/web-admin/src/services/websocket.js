/**
 * WebSocket服务
 * 实现与后端的实时通信
 */

class WebSocketService {
  constructor() {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.listeners = new Map()
    this.isConnecting = false
    this.isManualClose = false
  }

  // 连接WebSocket
  connect(url = null) {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }

    this.isConnecting = true
    this.isManualClose = false

    const wsUrl = url || this.getWebSocketUrl()
    
    try {
      this.ws = new WebSocket(wsUrl)
      this.setupEventHandlers()
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      this.isConnecting = false
      this.handleReconnect()
    }
  }

  // 获取WebSocket URL
  getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.VITE_WS_HOST || window.location.host
    const port = import.meta.env.VITE_WS_PORT || '9930'
    // 生成客户端ID
    const clientId = this.generateClientId()
    return `${protocol}//${host.split(':')[0]}:${port}/ws/${clientId}`
  }

  // 生成客户端ID
  generateClientId() {
    return 'client_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now()
  }

  // 设置事件处理器
  setupEventHandlers() {
    this.ws.onopen = () => {
      console.log('WebSocket连接已建立')
      this.isConnecting = false
      this.reconnectAttempts = 0
      this.emit('connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.handleMessage(data)
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
      }
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket连接已关闭:', event.code, event.reason)
      this.isConnecting = false
      this.emit('disconnected', { code: event.code, reason: event.reason })
      
      if (!this.isManualClose && event.code !== 1000) {
        this.handleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      this.isConnecting = false
      this.emit('error', error)
    }
  }

  // 处理消息
  handleMessage(data) {
    const { type, payload } = data
    
    switch (type) {
      case 'engine_status_update':
        this.emit('engineStatusUpdate', payload)
        break
      case 'task_update':
        this.emit('taskUpdate', payload)
        break
      case 'system_notification':
        this.emit('systemNotification', payload)
        break
      case 'heartbeat':
        this.handleHeartbeat(payload)
        break
      default:
        this.emit('message', data)
    }
  }

  // 处理心跳
  handleHeartbeat(payload) {
    // 回复心跳
    this.send({
      type: 'heartbeat_response',
      payload: { timestamp: Date.now() }
    })
  }

  // 处理重连
  handleReconnect() {
    if (this.isManualClose || this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('停止重连尝试')
      return
    }

    this.reconnectAttempts++
    console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    
    setTimeout(() => {
      this.connect()
    }, this.reconnectInterval * this.reconnectAttempts)
  }

  // 发送消息
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
      return true
    } else {
      console.warn('WebSocket未连接，无法发送消息')
      return false
    }
  }

  // 订阅引擎状态更新
  subscribeEngineStatus() {
    this.send({
      type: 'subscribe',
      payload: { channel: 'engine_status' }
    })
  }

  // 订阅任务更新
  subscribeTaskUpdates() {
    this.send({
      type: 'subscribe',
      payload: { channel: 'task_updates' }
    })
  }

  // 取消订阅
  unsubscribe(channel) {
    this.send({
      type: 'unsubscribe',
      payload: { channel }
    })
  }

  // 关闭连接
  close() {
    this.isManualClose = true
    if (this.ws) {
      this.ws.close(1000, 'Manual close')
    }
  }

  // 获取连接状态
  getReadyState() {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED
  }

  // 是否已连接
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }

  // 事件监听
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  // 移除事件监听
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  // 触发事件
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`事件处理器错误 (${event}):`, error)
        }
      })
    }
  }

  // 清除所有监听器
  removeAllListeners() {
    this.listeners.clear()
  }
}

// 创建全局WebSocket实例
export const wsService = new WebSocketService()

// 默认导出
export default wsService